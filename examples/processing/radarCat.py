
from enum import Enum
import numpy as np
from scipy.signal import welch
from threading import Thread
import subprocess
import gphoto2 as gp
import logging
import os
from datetime import datetime
import time
from threading import Timer

from acconeer_utils.clients import SocketClient, SPIClient, UARTClient
from acconeer_utils.clients import configs
from acconeer_utils import example_utils
from acconeer_utils.structs import configbase


HALF_WAVELENGTH = 2.445e-3  # m

WAITFORCOMPLETINGSPEEDLIMITDETECTION = None

# Speedlimit in km/h
SPEEDLIMIT = 4
SPEEDLIMIT_TEMP = SPEEDLIMIT
CAMERA = None
CONTEXT = None
DIRECTION = ""
LOCKRADAR = None

# setup logging
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)

def get_sensor_config():
    config = configs.SparseServiceConfig()

    config.range_interval = [2.1, 3.0]
    config.stepsize = 2
    config.sampling_mode = configs.SparseServiceConfig.SAMPLING_MODE_A
    config.number_of_subsweeps = NUM_FFT_BINS
    config.gain = 0.6
    config.hw_accelerated_average_samples = 60
    # config.subsweep_rate = 6e3

    # force max frequency
    config.sweep_rate = 200
    config.experimental_stitching = False
git
    return config
    
def main():
    global CAMERA
    global CONTEXT
    global logging
    
    args = example_utils.ExampleArgumentParser(num_sens=1).parse_args()
    example_utils.config_logging(args)
    logging.info("radarCat starting with args " + str(args))

    if args.socket_addr:
        client = SocketClient(args.socket_addr)
    elif args.spi:
        client = SPIClient()
    else:
        port = args.serial_port or example_utils.autodetect_serial_port()
        client = UARTClient(port)

    # setup Camera date and time
    logging.info("set Camera date and time")
    subprocess.call(["gphoto2","--set-config", "datetime=now"])

    gp.check_result(gp.use_python_logging())
    CONTEXT = gp.gp_context_new()
    CAMERA = gp.check_result(gp.gp_camera_new())
    gp.check_result(gp.gp_camera_init(CAMERA, CONTEXT))

    sensor_config = get_sensor_config()
    processing_config = get_processing_config()
    sensor_config.sensor = args.sensors

    session_info = client.setup_session(sensor_config)
    logging.info(session_info)

    client.start_streaming()

    interrupt_handler = example_utils.ExampleInterruptHandler()
    print("Press Ctrl-C to end session")

    processor = Processor(sensor_config, processing_config, session_info)

    global SPEEDLIMIT_TEMP
    global WAITFORCOMPLETINGSPEEDLIMITDETECTION
    global DIRECTION
    global LOCKRADAR

    lastSpeed = np.nan
    lastDistance = 0
    curDirection = "away"
    gotDirection = False

    while not interrupt_handler.got_signal:
        # if WAITFORCOMPLETINGSPEEDLIMITDETECTION:
        #   logging.info("Stop streaming")
        #   client.stop_streaming()
        #   time.sleep(20)
        #   logging.info("Start streaming")
        #   client.start_streaming()
        info, sweep = client.get_next()
        if LOCKRADAR:
            gotDirection = False
            continue

        plot_data = processor.process(sweep)

        speed = (plot_data["speed"])

        if np.isnan(speed) and np.isnan(lastSpeed):
            continue

        speed = speed * 3.6
        distance = (plot_data["distance"])

        if speed > 0.2 and (lastSpeed != speed or distance != lastDistance):
            if lastDistance != 0 and distance > lastDistance:
               if not gotDirection:
                    DIRECTION = "away"
                    gotDirection = True
               curDirection = "away"
            elif lastDistance != 0 and distance < lastDistance:
                if not gotDirection:
                    DIRECTION = "towards"
                    gotDirection = True
                curDirection = "towards"
            elif lastDistance != 0 and distance == lastDistance:
               curDirection = "stay"
            else:
               curDirection = ""

            logging.info("Speed: " + str(round(speed, 1)) + "km/h in " + str(round(distance, 1)) + "m " + curDirection)
            lastSpeed = speed
            lastDistance = distance
        elif speed < 0.4 and lastSpeed != 0:
            logging.info("No movement")
            lastSpeed = np.nan
            lastDistance = 0

        if speed > SPEEDLIMIT_TEMP:
            SPEEDLIMIT_TEMP = speed
            logging.info("Maximal current Speed: " + str(SPEEDLIMIT_TEMP))
            if not WAITFORCOMPLETINGSPEEDLIMITDETECTION:
                WAITFORCOMPLETINGSPEEDLIMITDETECTION = True
                r = Timer(2.0, lockRadar, (""))
                r.start()

                threadCaptureImage = Thread(target = captureImage, args=[])
                threadCaptureImage.start()

                threadSendRadarCatImage = Thread(target = sendRadarCatImage, args=[])
                threadSendRadarCatImage.start()

    print("Disconnecting...")
    client.disconnect()

class ProcessingConfiguration(configbase.ProcessingConfig):
    VERSION = 1

    class SpeedUnit(Enum):
        METER_PER_SECOND = ("m/s", 1)
        KILOMETERS_PER_HOUR = ("km/h", 3.6)
        MILES_PER_HOUR = ("mph", 2.237)

        @property
        def label(self):
            return self.value[0]

        @property
        def scale(self):
            return self.value[1]

    min_speed = configbase.FloatParameter(
            label="Minimum speed",
            unit="m/s",
            default_value=0.2,
            limits=(0, 5),
            decimals=1,
            updateable=True,
            order=0,
            )

    shown_speed_unit = configbase.EnumParameter(
            label="Speed unit",
            default_value=SpeedUnit.METER_PER_SECOND,
            enum=SpeedUnit,
            updateable=True,
            order=100,
            )

    show_data_plot = configbase.BoolParameter(
            label="Show data",
            default_value=False,
            updateable=True,
            order=110,
            )

    show_sd_plot = configbase.BoolParameter(
            label="Show spectral density",
            default_value=True,
            updateable=True,
            order=120,
            )

    show_vel_history_plot = configbase.BoolParameter(
            label="Show speed history",
            default_value=True,
            updateable=True,
            order=130,
            )


get_processing_config = ProcessingConfiguration


class Processor:
    def __init__(self, sensor_config, processing_config, session_info):
        self.num_subsweeps = sensor_config.number_of_subsweeps
        subsweep_rate = session_info["actual_subsweep_rate"]
        est_update_rate = subsweep_rate / self.num_subsweeps

        self.fft_length = (self.num_subsweeps // 2) * FFT_OVERSAMPLING_FACTOR

        self.num_noise_est_bins = 3
        noise_est_tc = 1.0
        self.min_threshold = 2.5
        self.dynamic_threshold = 0.1
        self.noise_est_sf = self.tc_to_sf(noise_est_tc, est_update_rate)
        self.bin_fs = np.fft.rfftfreq(self.fft_length) * subsweep_rate
        self.bin_vs = self.bin_fs * HALF_WAVELENGTH
        self.update_idx = 0
        self.depths = get_range_depths(sensor_config, session_info)
        
        self.update_processing_config(processing_config)

    def update_processing_config(self, processing_config):
        self.min_speed = processing_config.min_speed

    def tc_to_sf(self, tc, fs):
        if tc <= 0.0:
            return 0.0

        return np.exp(-1.0 / (tc * fs))

    def dynamic_sf(self, static_sf):
        return min(static_sf, 1.0 - 1.0 / (1.0 + self.update_idx))

    def process(self, sweep):
        # Basic speed estimate

        zero_mean_sweep = sweep - sweep.mean(axis=0, keepdims=True)

        _, psds = welch(
                zero_mean_sweep,
                nperseg=self.num_subsweeps // 2,
                detrend=False,
                axis=0,
                nfft=self.fft_length,
                )

        psd = np.max(psds, axis=1)
        asd = np.sqrt(psd)

        inst_noise_est = np.mean(asd[(-self.num_noise_est_bins - 1):-1])
        sf = self.dynamic_sf(self.noise_est_sf)
        self.noise_est = sf * self.noise_est + (1.0 - sf) * inst_noise_est

        nasd = asd / self.noise_est

        threshold = max(self.min_threshold, np.max(nasd) * self.dynamic_threshold)
        over = nasd > threshold
        est_idx = np.where(over)[0][-1] if np.any(over) else np.nan

        if est_idx > 0:  # evaluates to false if nan
            est_vel = self.bin_vs[est_idx]
        else:
            est_vel = np.nan

        if est_vel < self.min_speed:  # evaluates to false if nan
            est_vel = np.nan

        # print speed and distance
        fft = np.fft.rfft(zero_mean_sweep.T * np.hanning(sweep.shape[0]), axis=1)
        abs_fft = np.abs(fft)
        max_depth_index, max_bin = np.unravel_index(abs_fft.argmax(), abs_fft.shape)
        depth = self.depths[max_depth_index]
        
        self.update_idx += 1

        return {
             "speed": est_vel,
             "distance": depth,
        }
      
def get_range_depths(sensor_config, session_info):
    range_start = session_info["actual_range_start"]
    range_end = range_start + session_info["actual_range_length"]
    num_depths = session_info["data_length"] // sensor_config.number_of_subsweeps
    return np.linspace(range_start, range_end, num_depths)
    
def captureImage():
    global CAMERA
    global CONTEXT
    global logging
    
    current_time = datetime.now()
    logging.info("Capture Image")
    file_path = gp.check_result(gp.gp_camera_capture(
        CAMERA, gp.GP_CAPTURE_IMAGE, CONTEXT))
    logging.info('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
    target = os.path.join('.', file_path.name)
    print ('Copying image to', target)
    camera_file = gp.check_result(gp.gp_camera_file_get(
            CAMERA, file_path.folder, file_path.name,
            gp.GP_FILE_TYPE_NORMAL, CONTEXT))
    gp.check_result(gp.gp_file_save(camera_file, target))
    # subprocess.call(['xdg-open', target])
    gp.check_result(gp.gp_camera_exit(CAMERA, CONTEXT))

    logging.info("Write capture date/time to file")
    f = open("captureDateTime.txt", "w")
    f.write(str(current_time))
    f.close()

def sendRadarCatImage(): 
    logging.info ("Lock radar until image is sendet")
    time.sleep(10)
    global WAITFORCOMPLETINGSPEEDLIMITDETECTION
    global SPEEDLIMIT_TEMP
    global SPEEDLIMIT   


    logging.info("Write max Speed to file: " + str(SPEEDLIMIT_TEMP))
    f = open("speed.txt", "w")
    f.write(str(round(SPEEDLIMIT_TEMP, 1)) + " km/h")
    f.close()
    
    logging.info("Write Speedlimit to file: " + str(SPEEDLIMIT))
    f = open("speedLimit.txt", "w")
    f.write(str(round(SPEEDLIMIT, 1)) + " km/h")
    f.close()
    
    logging.info("Start Postprocessing")
    myCmd = './postProcessing.sh'
    subprocess.call([myCmd])
    
    logging.info("Send Email with Attachment")
    myCmd = './sendmail.sh'
    subprocess.call([myCmd])

    SPEEDLIMIT_TEMP = SPEEDLIMIT
    WAITFORCOMPLETINGSPEEDLIMITDETECTION = None

    logging.info ("Release radar lock")

def lockRadar():
    global LOCKRADAR
    global DIRECTION
    LOCKRADAR = True
    logging.info("Write movement to file: " + str(DIRECTION))
    f = open("direction.txt", "w")
    if DIRECTION == "away":
        DIRECTION = "A"
    elif DIRECTION == "towards":
        DIRECTION = "T"
    else:
        DIRECTION = ""
    f.write(DIRECTION)
    f.close()
    DIRECTION = ""


if __name__ == "__main__":
    main()
