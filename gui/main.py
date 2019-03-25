import os
import re
import sys
import ntpath
import numpy as np
import serial.tools.list_ports
import h5py
import logging
import signal
import threading

from PyQt5.QtWidgets import (QComboBox, QMainWindow, QApplication, QWidget, QLabel, QLineEdit,
                             QCheckBox)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtCore

import matplotlib as mpl
mpl.use("QT5Agg")  # noqa: E402
from matplotlib.backends.qt_compat import QtWidgets
import matplotlib.pyplot as plt

import pyqtgraph as pg

from acconeer_utils.clients.reg.client import RegClient, RegSPIClient
from acconeer_utils.clients.json.client import JSONClient
from acconeer_utils.clients import configs
from acconeer_utils import example_utils

import data_processing

sys.path.append(os.path.join(os.path.dirname(__file__), "../examples/processing"))  # noqa: E402
import presence_detection as prd
import phase_tracking as pht
import breathing as br
import sleep_breathing as sb
import obstacle_detection as od


class GUI(QMainWindow):
    sig_scan = pyqtSignal(str, str, object)
    cl_file = False
    data = None
    client = None
    sweep_count = -1
    acc_file = os.path.join(os.path.dirname(__file__), "acc.png")
    last_file = os.path.join(os.path.dirname(__file__), "last_config.npy")
    sweep_buffer = 500
    env_plot_max_y = 0
    cl_supported = False
    sweep_number = 0
    sweeps_skipped = 0
    service_labels = {}
    service_params = None

    def __init__(self):
        super().__init__()

        self.init_labels()
        self.init_textboxes()
        self.init_buttons()
        self.init_dropdowns()
        self.init_checkboxes()
        self.init_sublayouts()
        self.start_up()

        self.main_widget = QWidget()
        self.main_layout = QtWidgets.QGridLayout(self.main_widget)
        self.main_layout.sizeConstraint = QtWidgets.QLayout.SetDefaultConstraint

        self.main_layout.addLayout(self.panel_sublayout, 0, 1)
        self.main_layout.setColumnStretch(0, 1)

        self.canvas = self.init_graphs()
        self.main_layout.addWidget(self.canvas, 0, 0)

        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        self.setGeometry(50, 50, 1200, 700)
        self.setWindowTitle("Acconeer Exploration GUI")
        self.show()

        self.radar = data_processing.DataProcessing()

    def init_labels(self):
        text = {
            "sensor":       "Sensor",
            "server":       "Host address",
            "scan":         "Scan",
            "gain":         "Gain",
            "frequency":    "Sweep frequency",
            "sweeps":       "Number of sweeps",
            "sweep_buffer": "Sweep buffer",
            "start_range":  "Start (m)",
            "end_range":    "Stop (m)",
            "clutter":      "Background settings",
            "interface":    "Interface",
            "power_bins":   "Power bins",
            "sweep_info":   "Sweeps: 0 (skipped 0)",
            "saturated":    "Warning: Data saturated, reduce gain!",
            "stitching":    "Experimental stitching enabled!"
        }

        self.labels = {}
        for key in text:
            self.labels[key] = QLabel(self)
        for key, val in self.labels.items():
            val.setText(text[key])

        self.labels["power_bins"].setVisible(False)
        self.labels["saturated"].setStyleSheet("color: #f0f0f0")
        self.labels["stitching"].setVisible(False)
        self.labels["stitching"].setStyleSheet("color: red")

    def init_textboxes(self):
        text = {
            "sensor":       "1",
            "host":         "192.168.1.100",
            "frequency":    "10",
            "sweeps":       "-1",
            "gain":         "0.4",
            "start_range":  "0.18",
            "end_range":    "0.72",
            "sweep_buffer": "100",
            "power_bins":   "6",
        }
        self.textboxes = {}
        for key in text:
            self.textboxes[key] = QLineEdit(self)
            self.textboxes[key].setText(text[key])

        self.textboxes["power_bins"].setVisible(False)

    def init_checkboxes(self):
        check = {
            "clutter_file": "",
            "verbose":      "Enable verbose",
        }

        check_status = {
            "clutter_file": False,
            "verbose": False,
        }

        check_visible = {
            "clutter_file": False,
            "verbose": True,
        }

        check_funcs = {
            "clutter_file": self.update_scan,
            "verbose": self.set_log_level,
        }

        self.checkboxes = {}
        for key in check:
            self.checkboxes[key] = QCheckBox(check[key], self)
            self.checkboxes[key].setChecked(check_status[key])
            self.checkboxes[key].setVisible(check_visible[key])
            if check_funcs[key]:
                self.checkboxes[key].stateChanged.connect(check_funcs[key])

    def init_graphs(self, mode="Select service", refresh=False):
        axes = {
            "Select service": [None, None],
            "IQ": [None, None],
            "Envelope": [None, None],
            "Power bin": [None, None],
            "Presence detection": [prd, prd.PresenceDetectionProcessor],
            "Breathing": [br, br.BreathingProcessor],
            "Phase tracking": [pht, pht.PhaseTrackingProcessor],
            "Sleep breathing": [sb, sb.PresenceDetectionProcessor],
            "Obstacle detection": [od, od.ObstacleDetectionProcessor],
        }

        self.external = axes[mode][1]
        canvas = None

        self.textboxes["power_bins"].setVisible(False)
        self.labels["power_bins"].setVisible(False)
        self.profiles.setVisible(False)

        self.cl_supported = False
        if "IQ" in self.mode.currentText() or "Envelope" in self.mode.currentText():
            self.cl_supported = True
        else:
            self.load_clutter_file(force_unload=True)

        self.buttons["create_cl"].setEnabled(self.cl_supported)
        self.buttons["load_cl"].setEnabled(self.cl_supported)

        self.current_canvas = mode

        font = QFont()
        font.setPixelSize(12)
        ax_color = (0, 0, 0)
        ax = ("bottom", "left")

        if mode == "Select service":
            canvas = QLabel()
            pixmap = QPixmap(self.acc_file)
            canvas.setPixmap(pixmap)
            return canvas

        pg.setConfigOption("background", "#f0f0f0")
        pg.setConfigOption("foreground", "k")
        pg.setConfigOption("leftButtonPan", False)
        pg.setConfigOptions(antialias=True)
        canvas = pg.GraphicsLayoutWidget()

        if not refresh:
            for m in self.service_labels:
                for key in self.service_labels[m]:
                    for element in self.service_labels[m][key]:
                        if "label" in element or "box" in element:
                            self.service_labels[m][key][element].setVisible(False)
        if not self.external:
            self.service_params = None

        if self.external:
            if not refresh:
                self.service_params = None
                try:
                    self.service_params = axes[mode][0].get_processing_config()
                    self.add_params(self.service_params)
                except Exception:
                    pass
            self.service_widget = axes[mode][0].PGUpdater(
                self.update_sensor_config(refresh=refresh), self.service_params)
            self.service_widget.setup(canvas)

            return canvas
        elif "power" in mode.lower():
            self.power_plot_window = canvas.addPlot(title="Power bin")
            self.power_plot_window.showGrid(x=True, y=True)
            for i in ax:
                self.power_plot_window.getAxis(i).tickFont = font
                self.power_plot_window.getAxis(i).setPen(ax_color)
            pen = pg.mkPen(example_utils.color_cycler(0), width=2)
            self.power_plot = pg.BarGraphItem(x=np.arange(1, 7),
                                              height=np.linspace(0, 6, num=6),
                                              width=.5,
                                              pen=pen,
                                              name="Power bins")
            self.power_plot_window.setLabel("left", "Amplitude")
            self.power_plot_window.setLabel("bottom", "Power bin range (mm)")
            self.power_plot_window.setYRange(0, 10)
            self.power_plot_window.setXRange(0.5, 6.5)
            self.power_plot_window.addItem(self.power_plot)
            self.textboxes["power_bins"].setVisible(True)
            self.labels["power_bins"].setVisible(True)
        else:
            self.envelope_plot_window = canvas.addPlot(title="Envelope")
            self.envelope_plot_window.showGrid(x=True, y=True)
            self.envelope_plot_window.addLegend(offset=(-10, 10))
            for i in ax:
                self.envelope_plot_window.getAxis(i).tickFont = font
                self.envelope_plot_window.getAxis(i).setPen(ax_color)

            pen = example_utils.pg_pen_cycler()
            self.envelope_plot = self.envelope_plot_window.plot(range(10),
                                                                np.zeros(10),
                                                                pen=pen,
                                                                name="Envelope")
            self.envelope_plot_window.setYRange(0, 1)
            pen = pg.mkPen(0.2, width=2, style=QtCore.Qt.DotLine)
            self.clutter_plot = self.envelope_plot_window.plot(range(10),
                                                               np.zeros(10),
                                                               pen=pen,
                                                               name="Background")
            self.env_peak_vline = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen(width=2,
                                                  style=QtCore.Qt.DotLine))
            self.envelope_plot_window.addItem(self.env_peak_vline)
            self.clutter_plot.setZValue(2)

            self.peak_text = pg.TextItem(text="", color=(1, 1, 1), anchor=(0, 1))
            self.peak_text.setZValue(3)
            self.envelope_plot_window.addItem(self.peak_text)
            self.envelope_plot_window.setLabel("left", "Amplitude")
            self.envelope_plot_window.setLabel("bottom", "Distance (mm)")

            canvas.nextRow()

            if mode.lower() == "iq":
                self.iq_plot_window = canvas.addPlot(title="Phase")
                self.iq_plot_window.showGrid(x=True, y=True)
                self.iq_plot_window.addLegend(offset=(-10, 10))
                for i in ax:
                    self.iq_plot_window.getAxis(i).tickFont = font
                    self.iq_plot_window.getAxis(i).setPen(ax_color)
                pen = example_utils.pg_pen_cycler()
                self.iq_plot = self.iq_plot_window.plot(range(10),
                                                        np.arange(10)*0,
                                                        pen=pen,
                                                        name="IQ Phase")
                self.iq_plot_window.setLabel("left", "Normalized phase")
                self.iq_plot_window.setLabel("bottom", "Distance (mm)")
                canvas.nextRow()
            else:
                self.profiles.setVisible(True)
            self.hist_plot_image = canvas.addPlot()
            self.hist_plot = pg.ImageItem(titel="History")
            colormap = plt.get_cmap("viridis")
            colormap._init()
            lut = (colormap._lut * 255).view(np.ndarray)
            self.hist_plot.setLookupTable(lut)
            pen = example_utils.pg_pen_cycler(1)
            self.hist_plot_peak = self.hist_plot_image.plot(range(10),
                                                            np.zeros(10),
                                                            pen=pen)
            self.hist_plot_image.addItem(self.hist_plot)
            self.hist_plot_image.setLabel("left", "Distance (mm)")
            self.hist_plot_image.setLabel("bottom", "Time (Sweep number)")
            for i in ax:
                self.hist_plot_image.getAxis(i).tickFont = font
                self.hist_plot_image.getAxis(i).setPen(ax_color)

        return canvas

    def init_dropdowns(self):
        self.mode = QComboBox(self)
        self.mode.addItem("Select service")
        self.mode.addItem("IQ")
        self.mode.addItem("Envelope")
        self.mode.addItem("Power bin")
        self.mode.addItem("Phase tracking")
        self.mode.addItem("Presence detection")
        self.mode.addItem("Breathing")
        self.mode.addItem("Sleep breathing")
        self.mode.addItem("Obstacle detection")
        self.mode.move(50, 250)

        self.mode_to_param = {
            "Select service": "",
            "IQ": "iq_data",
            "Envelope": "envelope_data",
            "Power bin": "power_bin",
            "Breathing": "iq_data",
            "Phase tracking": "iq_data",
            "Presence detection": "iq_data",
            "Sleep breathing": "iq_data",
            "Obstacle detection": "iq_data",
        }

        self.mode_to_config = {
            "Select service": ["", ""],
            "IQ": [configs.IQServiceConfig(), "internal"],
            "Envelope": [configs.EnvelopeServiceConfig(), "internal"],
            "Power bin": [configs.PowerBinServiceConfig(), "internal_power"],
            "Breathing": [br.get_sensor_config(), "external"],
            "Phase tracking": [pht.get_sensor_config(), "external"],
            "Presence detection": [prd.get_sensor_config(), "external"],
            "Sleep breathing": [sb.get_sensor_config(), "external"],
            "Obstacle detection": [od.get_sensor_config(), "external"]
        }

        self.mode.currentIndexChanged.connect(self.update_canvas)

        self.interface = QComboBox(self)
        self.interface.addItem("Socket")
        self.interface.addItem("Serial")
        self.interface.addItem("SPI")
        self.interface.currentIndexChanged.connect(self.update_interface)

        self.ports = QComboBox(self)
        self.update_ports()

        self.profiles = QComboBox(self)
        self.profiles.addItem("Max SNR")
        self.profiles.addItem("Max depth resolution")
        self.profiles.currentIndexChanged.connect(self.set_profile)

    def set_profile(self):
        profile = self.profiles.currentText().lower()

        if "snr" in profile:
            self.textboxes["gain"].setText(str(0.45))
        elif "resolution" in profile:
            self.textboxes["gain"].setText(str(0.8))

    def update_ports(self):
        port_infos = serial.tools.list_ports.comports()
        ports = [port_info[0] for port_info in port_infos]

        try:
            opsys = os.uname()
            if "microsoft" in opsys.release.lower() and "linux" in opsys.sysname.lower():
                print("WSL detected. Limiting serial ports")
                ports_reduced = []
                for p in ports:
                    if int(re.findall(r"\d+", p)[0]) < 20:
                        ports_reduced.append(p)
                ports = ports_reduced
        except Exception:
            pass

        self.ports.clear()
        self.ports.addItems(ports)

    def init_buttons(self):
        self.buttons = {
            "start":        QtWidgets.QPushButton("Start", self),
            "connect":      QtWidgets.QPushButton("Connect", self),
            "stop":         QtWidgets.QPushButton("Stop", self),
            "create_cl":    QtWidgets.QPushButton("Scan Background", self),
            "load_cl":      QtWidgets.QPushButton("Load Background", self),
            "load_scan":    QtWidgets.QPushButton("Load Scan", self),
            "save_scan":    QtWidgets.QPushButton("Save Scan", self),
            "replay_buffered": QtWidgets.QPushButton("Replay buffered/loaded", self),
            "scan_ports":   QtWidgets.QPushButton("Scan ports", self),
        }

        button_funcs = {
            "start": self.start_scan,
            "connect": self.connect_to_server,
            "stop": self.stop_scan,
            "create_cl": lambda: self.start_scan(create_cl=True),
            "load_cl": self.load_clutter_file,
            "load_scan": lambda: self.load_scan(),
            "replay_buffered": lambda: self.load_scan(restart=True),
            "save_scan": lambda: self.save_scan(self.data),
            "scan_ports": self.update_ports,
        }

        button_enabled = {
            "start": False,
            "connect": True,
            "stop": False,
            "create_cl": False,
            "load_cl": True,
            "load_scan": True,
            "save_scan": False,
            "replay_buffered": False,
            "scan_ports": True,
        }

        for key in button_funcs:
            self.buttons[key].clicked.connect(button_funcs[key])
            self.buttons[key].setEnabled(button_enabled[key])

        self.buttons["scan_ports"].hide()

    def init_sublayouts(self):
        # Panel sublayout
        self.panel_sublayout = QtWidgets.QHBoxLayout()
        panel_sublayout_inner = QtWidgets.QVBoxLayout()

        # Server sublayout
        server_sublayout_grid = QtWidgets.QGridLayout()
        server_sublayout_grid.addWidget(self.labels["server"], 0, 0)
        server_sublayout_grid.addWidget(self.buttons["scan_ports"], 0, 0)
        server_sublayout_grid.addWidget(self.labels["interface"], 0, 1)
        server_sublayout_grid.addWidget(self.ports, 1, 0)
        server_sublayout_grid.addWidget(self.textboxes["host"], 1, 0)
        server_sublayout_grid.addWidget(self.interface, 1, 1)
        server_sublayout_grid.addWidget(self.mode, 2, 0)
        server_sublayout_grid.addWidget(self.buttons["connect"], 2, 1)

        # Controls sublayout
        control_sublayout_grid = QtWidgets.QGridLayout()
        control_sublayout_grid.addWidget(self.labels["scan"], 0, 0)
        control_sublayout_grid.addWidget(self.buttons["start"], 1, 0)
        control_sublayout_grid.addWidget(self.buttons["stop"], 1, 1)
        control_sublayout_grid.addWidget(self.buttons["save_scan"], 2, 0)
        control_sublayout_grid.addWidget(self.buttons["load_scan"], 2, 1)
        control_sublayout_grid.addWidget(self.buttons["replay_buffered"], 3, 0, 1, 2)
        control_sublayout_grid.addWidget(self.labels["sweep_buffer"], 4, 0)
        control_sublayout_grid.addWidget(self.textboxes["sweep_buffer"], 4, 1)
        control_sublayout_grid.addWidget(QLabel(self), 5, 0)
        control_sublayout_grid.addWidget(self.labels["clutter"], 6, 0)
        control_sublayout_grid.addWidget(self.buttons["create_cl"], 7, 0)
        control_sublayout_grid.addWidget(self.buttons["load_cl"], 7, 1)
        control_sublayout_grid.addWidget(self.checkboxes["clutter_file"], 8, 0, 1, 2)

        # Settings sublayout
        settings_sublayout_grid = QtWidgets.QGridLayout()
        settings_sublayout_grid.addWidget(self.profiles, 0, 0, 1, 2)
        settings_sublayout_grid.addWidget(self.labels["sensor"], 1, 0)
        settings_sublayout_grid.addWidget(self.textboxes["sensor"], 1, 1)
        settings_sublayout_grid.addWidget(self.labels["start_range"], 2, 0)
        settings_sublayout_grid.addWidget(self.labels["end_range"], 2, 1)
        settings_sublayout_grid.addWidget(self.textboxes["start_range"], 3, 0)
        settings_sublayout_grid.addWidget(self.textboxes["end_range"], 3, 1)
        settings_sublayout_grid.addWidget(self.labels["frequency"], 4, 0)
        settings_sublayout_grid.addWidget(self.textboxes["frequency"], 4, 1)
        settings_sublayout_grid.addWidget(self.labels["gain"], 5, 0)
        settings_sublayout_grid.addWidget(self.textboxes["gain"], 5, 1)
        settings_sublayout_grid.addWidget(self.labels["sweeps"], 6, 0)
        settings_sublayout_grid.addWidget(self.textboxes["sweeps"], 6, 1)
        settings_sublayout_grid.addWidget(self.labels["power_bins"], 7, 0)
        settings_sublayout_grid.addWidget(self.textboxes["power_bins"], 7, 1)
        settings_sublayout_grid.addWidget(self.labels["stitching"], 8, 0, 1, 2)

        # Service params sublayout
        self.serviceparams_sublayout_grid = QtWidgets.QGridLayout()

        # Info sublayout
        info_sublayout_grid = QtWidgets.QGridLayout()
        info_sublayout_grid.addWidget(self.checkboxes["verbose"], 0, 0, 1, 2)
        info_sublayout_grid.addWidget(self.labels["sweep_info"], 1, 0, 1, 2)
        info_sublayout_grid.addWidget(self.labels["saturated"], 2, 0, 1, 2)

        panel_sublayout_inner.addStretch(10)
        panel_sublayout_inner.addLayout(server_sublayout_grid)
        panel_sublayout_inner.addStretch(5)
        panel_sublayout_inner.addLayout(control_sublayout_grid)
        panel_sublayout_inner.addStretch(5)
        panel_sublayout_inner.addLayout(settings_sublayout_grid)
        panel_sublayout_inner.addStretch(5)
        panel_sublayout_inner.addLayout(self.serviceparams_sublayout_grid)
        panel_sublayout_inner.addStretch(20)
        panel_sublayout_inner.addLayout(info_sublayout_grid)
        panel_sublayout_inner.addStretch(1)
        self.panel_sublayout.addStretch(5)
        self.panel_sublayout.addLayout(panel_sublayout_inner)
        self.panel_sublayout.addStretch(10)

    def add_params(self, params):
        for mode in self.service_labels:
            for key in self.service_labels[mode]:
                for element in self.service_labels[mode][key]:
                    if "label" in element or "box" in element:
                        self.service_labels[mode][key][element].setVisible(False)
        mode = self.mode.currentText()

        index = 0
        if mode not in self.service_labels:
            self.service_labels[mode] = {}

        for key in params:
            if key not in self.service_labels[mode]:
                self.service_labels[mode][key] = {}
                if params[key]["value"] is not None:
                    self.service_labels[mode][key]["label"] = QLabel(self)
                    self.service_labels[mode][key]["label"].setMinimumWidth(125)
                    self.service_labels[mode][key]["label"].setText(params[key]["name"])
                    self.service_labels[mode][key]["box"] = QLineEdit(self)
                    self.service_labels[mode][key]["box"].setText(str(params[key]["value"]))
                    self.service_labels[mode][key]["limits"] = params[key]["limits"]
                    self.service_labels[mode][key]["default"] = params[key]["value"]
                    self.serviceparams_sublayout_grid.addWidget(
                        self.service_labels[mode][key]["label"], index, 0)
                    self.serviceparams_sublayout_grid.addWidget(
                        self.service_labels[mode][key]["box"], index, 1)
                    self.service_labels[mode][key]["box"].setVisible(True)

                else:
                    self.service_labels[mode][key]["label"] = QLabel(self)
                    self.service_labels[mode][key]["label"].setText(str(params[key]["text"]))
                    self.serviceparams_sublayout_grid.addWidget(
                        self.service_labels[mode][key]["label"], index, 0, 1, 2)
                index += 1
            else:
                for element in self.service_labels[mode][key]:
                    if "label" in element or "box" in element:
                        self.service_labels[mode][key][element].setVisible(True)

    def update_canvas(self, force_update=False):
        mode = self.mode.currentText()

        if force_update or self.current_canvas not in mode:
            self.main_layout.removeWidget(self.canvas)
            self.canvas.setParent(None)
            self.canvas.deleteLater()
            self.canvas = None
            refresh = False
            if self.current_canvas == mode:
                refresh = True
                self.service_params = self.update_service_params()
            self.canvas = self.init_graphs(mode, refresh=refresh)
            self.main_layout.addWidget(self.canvas, 0, 0)

        self.update_sensor_config()

    def update_interface(self):
        if self.buttons["connect"].text() == "Disconnect":
            self.connect_to_server()

        if "serial" in self.interface.currentText().lower():
            self.ports.show()
            self.textboxes["host"].hide()
            self.labels["server"].hide()
            self.buttons["scan_ports"].show()
        elif "spi" in self.interface.currentText().lower():
            self.ports.hide()
            self.textboxes["host"].hide()
            self.labels["server"].hide()
            self.buttons["scan_ports"].hide()
        else:
            self.ports.hide()
            self.textboxes["host"].show()
            self.labels["server"].show()
            self.buttons["scan_ports"].hide()

    def error_message(self, error):
        em = QtWidgets.QErrorMessage(self.main_widget)
        em.setWindowTitle("Error")
        em.showMessage(error)

    def start_scan(self, create_cl=False, from_file=False):
        if "Select" in self.mode.currentText():
            self.error_message("Please select a service")
            return

        if self.external:
            self.update_canvas(force_update=True)

        data_source = "stream"
        if from_file:
            data_source = "file"
        sweep_buffer = 500
        try:
            sweep_buffer = int(self.textboxes["sweep_buffer"].text())
        except Exception:
            self.error_message("Sweep buffer needs to be a positive integer\n")
            self.textboxes["sweep_buffer"].setText("500")

        if create_cl and self.cl_file:
            self.load_clutter_file(force_unload=True)

        use_cl = False
        if self.checkboxes["clutter_file"].isChecked():
            use_cl = True

        params = {
            "sensor_config": self.update_sensor_config(),
            "clutter_file": self.cl_file,
            "use_clutter": use_cl,
            "create_clutter": create_cl,
            "data_source": data_source,
            "data_type": self.mode_to_param[self.mode.currentText()],
            "service_type": self.mode.currentText(),
            "sweep_buffer": sweep_buffer,
            "service_params": self.update_service_params(),
        }

        self.threaded_scan = Threaded_Scan(params, parent=self)
        self.threaded_scan.sig_scan.connect(self.thread_receive)
        self.sig_scan.connect(self.threaded_scan.receive)

        self.buttons["start"].setEnabled(False)
        self.buttons["load_scan"].setEnabled(False)
        self.buttons["save_scan"].setEnabled(False)
        self.buttons["create_cl"].setEnabled(False)
        self.buttons["load_cl"].setEnabled(False)
        self.mode.setEnabled(False)
        self.buttons["stop"].setEnabled(True)

        self.sweep_number = 0
        self.sweeps_skipped = 0
        self.threaded_scan.start()

        self.buttons["connect"].setEnabled(False)
        self.buttons["replay_buffered"].setEnabled(False)

    def update_scan(self):
        if self.cl_file:
            clutter_file = self.cl_file
            if not self.checkboxes["clutter_file"].isChecked():
                clutter_file = None
            self.sig_scan.emit("set_clutter_flag", "", clutter_file)

    def stop_scan(self):
        self.sig_scan.emit("stop", "", None)
        self.buttons["load_scan"].setEnabled(True)
        self.buttons["load_cl"].setEnabled(self.cl_supported)
        self.buttons["create_cl"].setEnabled(self.cl_supported)
        self.mode.setEnabled(True)
        self.buttons["stop"].setEnabled(False)
        self.buttons["connect"].setEnabled(True)
        self.buttons["start"].setEnabled(True)
        if self.data is not None:
            self.buttons["replay_buffered"].setEnabled(True)

    def set_log_level(self):
        log_level = logging.INFO
        if self.checkboxes["verbose"].isChecked():
            log_level = logging.DEBUG
        example_utils.set_loglevel(log_level)

    def connect_to_server(self):
        if self.buttons["connect"].text() == "Connect":
            max_num = 4
            if "Select service" in self.current_canvas:
                self.mode.setCurrentIndex(2)

            if self.interface.currentText().lower() == "socket":
                self.client = JSONClient(self.textboxes["host"].text())
            elif self.interface.currentText().lower() == "spi":
                self.client = RegSPIClient()
            else:
                port = self.ports.currentText()
                if "scan" in port.lower():
                    self.error_message("Please select port first!")
                    return
                self.client = RegClient(port)
                max_num = 1

            conf = self.update_sensor_config()
            sensor = 1
            connection_success = False
            error = None
            while sensor <= max_num:
                conf.sensor = sensor
                try:
                    self.client.setup_session(conf)
                    self.client.start_streaming()
                    self.client.stop_streaming()
                    connection_success = True
                    self.textboxes["sensor"].setText("{:d}".format(sensor))
                    break
                except Exception as e:
                    sensor += 1
                    error = e
            if connection_success:
                self.buttons["start"].setEnabled(True)
                self.buttons["create_cl"].setEnabled(self.cl_supported)
            else:
                self.error_message("Could not connect to server!\n{}".format(error))
                return

            self.buttons["connect"].setText("Disconnect")
            self.buttons["connect"].setStyleSheet("QPushButton {color: red}")
        else:
            self.buttons["connect"].setText("Connect")
            self.buttons["connect"].setStyleSheet("QPushButton {color: black}")
            self.sig_scan.emit("stop", "", None)
            self.buttons["start"].setEnabled(False)
            self.buttons["create_cl"].setEnabled(False)
            if self.cl_supported:
                self.buttons["load_cl"].setEnabled(True)

            try:
                self.client.stop_streaming()
            except Exception:
                pass

            try:
                self.client.disconnect()
            except Exception:
                pass

    def update_sensor_config(self, refresh=False):
        conf, service = self.mode_to_config[self.mode.currentText()]

        if not conf:
            return None

        external = ("internal" not in service.lower())

        conf.sensor = int(self.textboxes["sensor"].text())
        if not refresh and external:
            color = "grey"
            self.textboxes["start_range"].setText("{:.2f}".format(conf.range_interval[0]))
            self.textboxes["end_range"].setText("{:.2f}".format(conf.range_interval[1]))
            self.textboxes["gain"].setText("{:.2f}".format(conf.gain))
            self.textboxes["frequency"].setText("{:d}".format(conf.sweep_rate))
            self.sweep_count = -1
        else:
            stitching = self.check_values(conf.mode)
            color = "white"
            conf.range_interval = [
                    float(self.textboxes["start_range"].text()),
                    float(self.textboxes["end_range"].text()),
            ]
            conf.sweep_rate = int(self.textboxes["frequency"].text())
            conf.gain = float(self.textboxes["gain"].text())
            self.sweep_count = int(self.textboxes["sweeps"].text())
            if "power" in self.mode.currentText().lower():
                conf.bin_count = int(self.textboxes["power_bins"].text())
            conf.experimental_stitching = stitching

            if "envelope" in self.mode.currentText().lower():
                if "snr" in self.profiles.currentText().lower():
                    conf.session_profile = configs.EnvelopeServiceConfig.MAX_SNR
                elif "depth" in self.profiles.currentText().lower():
                    conf.session_profile = configs.EnvelopeServiceConfig.MAX_DEPTH_RESOLUTION

        if self.service_params:  # Only lock boxes for services not yet supporting changing params
            external = False
            color = "white"

        lock = {
            "start_range": True,
            "end_range": True,
            "frequency": True,
            "gain": True,
            "sweeps": True,
        }

        for key in lock:
            if "sensor" not in key and "host" not in key:
                self.textboxes[key].setReadOnly(external)
                style_sheet = "QLineEdit {{background-color: {}}}".format(color)
                self.textboxes[key].setStyleSheet(style_sheet)

        return conf

    def update_service_params(self):
        errors = []
        mode = self.mode.currentText()

        if mode not in self.service_labels:
            return None

        for key in self.service_labels[mode]:
            if "box" in self.service_labels[mode][key]:
                if self.service_labels[mode][key]["box"].isVisible():
                    er = False
                    val = self.is_float(self.service_labels[mode][key]["box"].text(),
                                        is_positive=False)
                    limits = self.service_labels[mode][key]["limits"]
                    default = self.service_labels[mode][key]["default"]
                    if val is not False:
                        val, er = self.check_limit(val, self.service_labels[mode][key]["box"],
                                                   limits[0], limits[1], set_to=default)
                    else:
                        er = True
                        val = default
                        self.service_labels[mode][key]["box"].setText(str(default))
                    if er:
                        errors.append("{:s} must be between {:s} and {:s}!\n".format(
                            key, str(limits[0]), str(limits[1])))
                self.service_params[key]["value"] = self.service_params[key]["type"](val)
        if len(errors):
            self.error_message("".join(errors))
        return self.service_params

    def check_values(self, mode):
        errors = []
        if not self.textboxes["frequency"].text().isdigit():
            errors.append("Frequency must be an integer and not less than 0!\n")
            self.textboxes["frequency"].setText("10")

        if not self.textboxes["sensor"].text().isdigit():
            errors.append("Sensor must be an integer between 1 and 4!\n")
            self.textboxes["sensor"].setText("0")
        else:
            sensor = int(self.textboxes["sensor"].text())
            sensor, e = self.check_limit(sensor, self.textboxes["sensor"], 1, 4)
            if e:
                errors.append("Sensor must be an integer between 1 and 4!\n")

        sweeps = self.is_float(self.textboxes["sweeps"].text(), is_positive=False)
        if sweeps == -1:
            pass
        elif sweeps >= 1:
            if not self.textboxes["sweeps"].text().isdigit():
                errors.append("Sweeps must be a -1 or an int larger than 0!\n")
                self.textboxes["sensor"].setText("-1")
        else:
            errors.append("Sweeps must be -1 or an int larger than 0!\n")
            self.textboxes["sweeps"].setText("-1")

        gain = self.is_float(self.textboxes["gain"].text())
        gain, e = self.check_limit(gain, self.textboxes["gain"], 0, 1, set_to=0.7)
        if e:
            errors.append("Gain must be between 0 and 1!\n")

        start = self.is_float(self.textboxes["start_range"].text())
        start, e = self.check_limit(start, self.textboxes["start_range"], 0.06, 6.94)
        if e:
            errors.append("Start range must be between 0.06m and 6.94m!\n")

        end = self.is_float(self.textboxes["end_range"].text())
        end, e = self.check_limit(end, self.textboxes["end_range"], 0.12, 7)
        if e:
            errors.append("End range must be between 0.12m and 7.0m!\n")

        r = end - start

        env_max_range = 0.96
        iq_max_range = 0.72
        if self.interface.currentText().lower() == "socket":
            if "IQ" in self.mode.currentText() or "Envelope" in self.mode.currentText():
                env_max_range = 6.88
                iq_max_range = 6.88

        stitching = False
        if r <= 0:
            errors.append("Range must not be less than 0!\n")
            self.textboxes["end_range"].setText(str(start + 0.06))
            end = start + 0.06
            r = end - start

        if "envelope" in mode.lower():
            if r > env_max_range:
                errors.append("Envelope range must be less than %.2fm!\n" % env_max_range)
                self.textboxes["end_range"].setText(str(start + env_max_range))
                end = start + env_max_range
                r = end - start
            elif r > 0.96:
                stitching = True

        if "iq" in mode.lower():
            if r > iq_max_range:
                errors.append("IQ range must be less than %.2fm!\n" % iq_max_range)
                self.textboxes["end_range"].setText(str(start + iq_max_range))
                end = start + iq_max_range
                r = end - start
            elif r > 0.72:
                stitching = True

        self.labels["stitching"].setVisible(stitching)

        if len(errors):
            self.error_message("".join(errors))

        return stitching

    def is_float(self, val, is_positive=True):
        try:
            f = float(val)
            if is_positive and f <= 0:
                raise ValueError("Not positive")
            return f
        except Exception:
            return False

    def check_limit(self, val, field, start, end, set_to=None):
        out_of_range = False
        if isinstance(val, bool):
            val = start
            out_of_range = True
        if val < start:
            val = start
            out_of_range = True
        if val > end:
            val = end
            out_of_range = True
        if out_of_range:
            if set_to:
                val = set_to
            field.setText(str(val))
        return val, out_of_range

    def load_clutter_file(self, force_unload=False, fname=None):
        if not fname:
            if "unload" in self.buttons["load_cl"].text().lower() or force_unload:
                self.cl_file = None
                self.checkboxes["clutter_file"].setVisible(False)
                self.buttons["load_cl"].setText("Load Background")
                self.buttons["load_cl"].setStyleSheet("QPushButton {color: black}")
            else:
                options = QtWidgets.QFileDialog.Options()
                options |= QtWidgets.QFileDialog.DontUseNativeDialog
                fname, _ = QtWidgets.QFileDialog.getOpenFileName(
                    self,
                    "Load background file",
                    "",
                    "NumPy data Files (*.npy)",
                    options=options
                    )

        if fname:
            self.cl_file = fname
            self.checkboxes["clutter_file"].setVisible(True)
            s = "Background: {}".format(ntpath.basename(fname))
            self.checkboxes["clutter_file"].setText(s)
            self.checkboxes["clutter_file"].setChecked(True)
            self.buttons["load_cl"].setText("Unload background")
            self.buttons["load_cl"].setStyleSheet("QPushButton {color: red}")

    def load_scan(self, restart=False):
        if restart:
            self.start_scan(from_file=True)
            return

        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Load scan",
                "",
                "HDF5 data files (*.h5);; NumPy data files (*.npy)",
                options=options
                )

        if filename:
            cl_file = None
            if "h5" in filename:
                self.data = {}
                try:
                    f = h5py.File(filename, "r")
                except Exception as e:
                    self.error_message("{}".format(e))
                    print(e)
                    return

                try:
                    mode = f["service_type"][()]
                except Exception:
                    print("Service type not stored, setting to Envelope!")
                    mode = "Envelope"

                index = self.mode.findText(mode, QtCore.Qt.MatchFixedString)
                if index >= 0:
                    self.mode.setCurrentIndex(index)

                try:
                    if "iq" in mode.lower():
                        conf = configs.IQServiceConfig()
                    else:
                        conf = configs.EnvelopeServiceConfig()
                    real = np.asarray(list(f["real"]))
                    im = np.asarray(list(f["imag"]))
                    self.data["sweeps"] = real[...] + 1j * im[...]
                    data_len = len(self.data["sweeps"][:, 0])
                except Exception as e:
                    self.error_message("{}".format(e))
                    print(e)
                    return

                try:
                    self.profiles.setCurrentIndex(f["profile"][()])
                except Exception:
                    pass
                try:
                    conf.sweep_rate = f["sweep_rate"][()]
                    conf.range_interval = [f["start"][()], f["end"][()]]
                    if "power" in mode:
                        conf.bin_count = int(self.textboxes["power_bins"].text())
                    conf.gain = f["gain"][()]
                except Exception as e:
                    print("Config not stored in file...")
                    print(e)
                    conf.range_interval = [
                            float(self.textboxes["start_range"].text()),
                            float(self.textboxes["end_range"].text()),
                    ]
                    conf.sweep_rate = int(self.textboxes["frequency"].text())
                self.data["service_type"] = mode
                self.data["sensor_config"] = conf
                self.data["cl_file"] = None
                try:
                    self.data["cl_file"] = f["clutter_file"][()]
                    cl_file = self.data["cl_file"]
                except Exception:
                    pass
            else:
                try:
                    self.data = np.load(filename)
                    mode = self.data[0]["service_type"]
                    cl_file = self.data[0]["cl_file"]
                    data_len = len(self.data)
                    conf = self.data[0]["sensor_config"]
                except Exception as e:
                    self.error_message("{}".format(e))
                    return
                index = self.mode.findText(mode, QtCore.Qt.MatchFixedString)
                if index >= 0:
                    self.mode.setCurrentIndex(index)

            self.textboxes["start_range"].setText(str(conf.range_interval[0]))
            self.textboxes["end_range"].setText(str(conf.range_interval[1]))
            self.textboxes["gain"].setText(str(conf.gain))
            self.textboxes["frequency"].setText(str(int(conf.sweep_rate)))
            if "power" in mode.lower():
                self.textboxes["power_bins"].setText(str(conf.bin_count))

            if isinstance(cl_file, str) or isinstance(cl_file, os.PathLike):
                try:
                    os.path.isfile(cl_file)
                    self.load_clutter_file(fname=cl_file)
                except Exception as e:
                    print("Background file not found")
                    print(e)

            self.textboxes["sweep_buffer"].setText(str(data_len))
            self.start_scan(from_file=True)

    def save_scan(self, data, clutter=False):
        if "sleep" in self.mode.currentText().lower():
            if int(self.textboxes["sweep_buffer"].text()) < 1000:
                self.error_message("Please set sweep buffer to >= 1000")
                return
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog

        title = "Save scan"
        file_types = "HDF5 data files (*.h5);; NumPy data files (*.npy)"
        if clutter:
            title = "Save background"
            file_types = "NumPy data files (*.npy)"
        filename, info = QtWidgets.QFileDialog.getSaveFileName(
                self, title, "", file_types, options=options)

        if filename:
            if clutter:
                try:
                    np.save(filename, data)
                except Exception as e:
                    self.error_message("Failed to save file:\n {:s}".format(e))
                    return
                self.cl_file = filename
                if "npy" not in filename.lower():
                    self.cl_file += ".npy"
                label_text = "Background: {}".format(ntpath.basename(filename))
                self.checkboxes["clutter_file"].setText(label_text)
                self.checkboxes["clutter_file"].setChecked(True)
                self.checkboxes["clutter_file"].setVisible(True)
                self.buttons["load_cl"].setText("Unload background")
                self.buttons["load_cl"].setStyleSheet("QPushButton {color: red}")
            else:
                if "h5" in info:
                    sweep_data = []
                    for sweep in data:
                        sweep_data.append(sweep["sweep_data"])
                    sweep_data = np.asarray(sweep_data)
                    if ".h5" not in filename:
                        filename = filename + ".h5"
                    try:
                        f = h5py.File(filename, "w")
                    except Exception as e:
                        self.error_message("Failed to save file:\n {:s}".format(e))
                        return
                    f.create_dataset("imag", data=np.imag(sweep_data), dtype=np.float32)
                    f.create_dataset("real", data=np.real(sweep_data), dtype=np.float32)
                    f.create_dataset("sweep_rate", data=int(self.textboxes["frequency"].text()),
                                     dtype=np.float32)
                    f.create_dataset("start", data=float(self.textboxes["start_range"].text()),
                                     dtype=np.float32)
                    f.create_dataset("end", data=float(self.textboxes["end_range"].text()),
                                     dtype=np.float32)
                    f.create_dataset("gain", data=float(self.textboxes["gain"].text()),
                                     dtype=np.float32)
                    f.create_dataset("service_type", data=self.mode.currentText().lower(),
                                     dtype=h5py.special_dtype(vlen=str))
                    f.create_dataset("clutter_file", data=self.cl_file,
                                     dtype=h5py.special_dtype(vlen=str))
                    f.create_dataset("profile", data=self.profiles.currentIndex(),
                                     dtype=np.int)
                    f.create_dataset("power_bins", data=int(self.textboxes["power_bins"].text()),
                                     dtype=np.int)
                else:
                    try:
                        np.save(filename, data)
                    except Exception as e:
                        self.error_message("Failed to save file:\n {:s}".format(e))
                        return

    def thread_receive(self, message_type, message, data=None):
        if "error" in message_type:
            self.error_message("{}".format(message))
            if "client" in message_type:
                self.stop_scan()
                if self.buttons["connect"].text() == "Disconnect":
                    self.connect_to_server()
                self.buttons["create_cl"].setEnabled(False)
                self.buttons["start"].setEnabled(False)
            if "clutter" in message_type:
                self.load_clutter_file(force_unload=True)
        elif message_type == "clutter_data":
            self.save_scan(data, clutter=True)
        elif message_type == "scan_data":
            self.data = data
            self.buttons["save_scan"].setEnabled(True)
        elif message_type == "scan_done":
            self.stop_scan()
            if "Connect" == self.buttons["connect"].text():
                self.buttons["start"].setEnabled(False)
        elif "update_plots" in message_type:
            if data:
                self.update_plots(data)
        elif "update_power_plots" in message_type:
            if data:
                self.update_power_plots(data)
        elif "update_external_plots" in message_type:
            if data:
                self.update_external_plots(data)
        elif "sweep_info" in message_type:
            self.update_sweep_info(data)
        else:
            print(message_type, message, data)

    def update_plots(self, data):
        mode = self.mode.currentText()
        xstart = data["x_mm"][0]
        xend = data["x_mm"][-1]
        xdim = data["hist_env"].shape[0]
        if not data["sweep"]:
            self.env_plot_max_y = 0
            self.envelope_plot_window.setXRange(xstart, xend)
            self.peak_text.setPos(xstart, 0)

            self.smooth_envelope = example_utils.SmoothMax(
                int(self.textboxes["frequency"].text()),
                tau_decay=1,
                tau_grow=0.2
                )

            if mode == "IQ":
                self.iq_plot_window.setXRange(xstart, xend)
                self.iq_plot_window.setYRange(-1.1, 1.1)

            xax = self.hist_plot_image.getAxis("left")
            x = np.round(np.arange(0, xdim+xdim/9, xdim/9))
            labels = np.round(np.arange(xstart, xend+(xend-xstart)/9,
                              (xend-xstart)/9))
            ticks = [list(zip(x, labels))]
            xax.setTicks(ticks)

        peak = "Peak: N/A"
        if data["peaks"]["peak_mm"]:
            self.env_peak_vline.setValue(data["peaks"]["peak_mm"])
            peak = "Peak: %.1fmm" % data["peaks"]["peak_mm"]
            if data["snr"] and np.isfinite(data["snr"]):
                peak = "Peak: %.1fmm, SNR: %.1fdB" % (data["peaks"]["peak_mm"], data["snr"])

        self.peak_text.setText(peak, color=(1, 1, 1))

        max_val = max(np.max(data["env_clutter"]+data["env_ampl"]), np.max(data["env_clutter"]))
        peak_line = np.flip((data["hist_plot"]-xstart)/(xend - xstart)*xdim, axis=0)

        self.envelope_plot.setData(data["x_mm"], data["env_ampl"] + data["env_clutter"])
        self.clutter_plot.setData(data["x_mm"], data["env_clutter"])

        ymax_level = min(1.5*np.max(np.max(data["hist_env"])), self.env_plot_max_y)

        self.hist_plot.updateImage(data["hist_env"].T, levels=(0, ymax_level))
        self.hist_plot_peak.setData(peak_line)
        self.hist_plot_peak.setZValue(2)

        self.envelope_plot_window.setYRange(0, self.smooth_envelope.update(max_val))
        if mode == "IQ":
            self.iq_plot.setData(data["x_mm"], data["phase"])

        if max_val > self.env_plot_max_y:
            self.env_plot_max_y = 1.2 * max_val

        if self.sweep_buffer > data["sweep"]:
            self.hist_plot_image.setYRange(0, xdim)

    def update_power_plots(self, data):
        xstart = data["x_mm"][0]
        xend = data["x_mm"][-1]
        if not data["sweep"]:
            bin_num = int(self.textboxes["power_bins"].text())
            bin_width = (xend - xstart)/(bin_num + 1)
            self.env_plot_max_y = 0
            self.power_plot_window.setXRange(xstart, xend)
            self.power_plot.setOpts(x=data["x_mm"], width=bin_width)
            self.power_plot_window.setXRange(xstart - bin_width / 2,
                                             xend + bin_width / 2)
            self.smooth_power = example_utils.SmoothMax(
                int(self.textboxes["frequency"].text()),
                tau_decay=1,
                tau_grow=0.2
                )
        self.power_plot.setOpts(height=data["iq_data"])
        self.power_plot_window.setYRange(0, self.smooth_power.update(np.max(data["iq_data"])))

    def update_external_plots(self, data):
        self.service_widget.update(data)

    def update_sweep_info(self, data):
        self.sweeps_skipped += data["sequence_number"] - (self.sweep_number + 1)
        self.sweep_number = data["sequence_number"]

        nr = ""
        if self.sweep_number > 1e6:
            self.sweep_number = 1e6
            nr = ">"

        skip = ""
        if self.sweeps_skipped > 1e6:
            self.sweeps_skipped = 1e6
            skip = ">"

        self.labels["sweep_info"].setText("Sweeps: {:s}{:d} (skipped {:s}{:d})".format(
            nr, self.sweep_number, skip, self.sweeps_skipped))

        if data.get("data_saturated"):
            self.labels["saturated"].setStyleSheet("color: red")
        else:
            self.labels["saturated"].setStyleSheet("color: #f0f0f0")

    def start_up(self):
        if os.path.isfile(self.last_file):
            try:
                last = np.load(self.last_file)
                self.update_settings(last.item()["sensor_config"], last.item())
            except Exception as e:
                print("Could not load settings from last session\n{}".format(e))

    def update_settings(self, sensor_config, last_config=None):
        try:
            self.profiles.setCurrentIndex(last_config["profile"])
            self.textboxes["sweep_buffer"].setText(last_config["sweep_buffer"])
            self.textboxes["sensor"].setText("{:d}".format(sensor_config.sensor[0]))
            self.interface.setCurrentIndex(last_config["interface"])
            self.ports.setCurrentIndex(last_config["port"])
        except Exception as e:
            print("Warning, could not restore last session\n{}".format(e))

        try:
            self.textboxes["gain"].setText("{:.1f}".format(sensor_config.gain))
            self.textboxes["frequency"].setText(str(sensor_config.sweep_rate))
            self.textboxes["start_range"].setText("{:.2f}".format(sensor_config.range_interval[0]))
            self.textboxes["end_range"].setText("{:.2f}".format(sensor_config.range_interval[1]))
        except Exception as e:
            print("Warning, could not restore last session\n{}".format(e))

        if last_config:
            self.textboxes["host"].setText(last_config["host"])
            self.sweep_count = last_config["sweep_count"]

    def closeEvent(self, event=None):
        if "select" not in str(self.mode.currentText()).lower():
            last_config = {
                "sensor_config": self.update_sensor_config(),
                "sweep_count": self.sweep_count,
                "host": self.textboxes["host"].text(),
                "sweep_buffer": self.textboxes["sweep_buffer"].text(),
                "interface": self.interface.currentIndex(),
                "port": self.ports.currentIndex(),
                "profile": self.profiles.currentIndex(),
                }

            np.save(self.last_file, last_config)

        try:
            self.client.disconnect()
        except Exception:
            pass

        self.close()


class Threaded_Scan(QtCore.QThread):
    sig_scan = pyqtSignal(str, str, object)

    def __init__(self, params, parent=None):
        QtCore.QThread.__init__(self, parent)

        self.client = parent.client
        self.radar = parent.radar
        self.sensor_config = parent.update_sensor_config()
        self.params = params
        self.data = parent.data
        self.parent = parent
        self.running = True
        self.sweep_count = parent.sweep_count
        if self.sweep_count == -1:
            self.sweep_count = np.inf

    def run(self):
        if self.params["data_source"] == "stream":
            data = None

            try:
                self.client.setup_session(self.sensor_config)
                self.radar.prepare_processing(self, self.params)
                self.client.start_streaming()
            except Exception as e:
                self.emit("client_error", "Failed to communicate with server!\n"
                          "{}".format(self.format_error(e)))
                self.running = False

            try:
                while self.running:
                    info, sweep = self.client.get_next()
                    self.emit("sweep_info", "", info)
                    plot_data, data = self.radar.process(sweep)
                    if plot_data and plot_data["sweep"] + 1 >= self.sweep_count:
                        self.running = False
            except Exception as e:
                msg = "Failed to communicate with server!\n{}".format(self.format_error(e))
                self.emit("client_error", msg)

            try:
                self.client.stop_streaming()
            except Exception:
                pass

            if data:
                self.emit("scan_data", "", data)
        elif self.params["data_source"] == "file":
            self.radar.prepare_processing(self, self.params)
            self.radar.process_saved_data(self.data, self)
        else:
            self.emit("error", "Unknown mode %s!" % self.mode)
        self.emit("scan_done", "", "")

    def receive(self, message_type, message, data=None):
        if message_type == "stop":
            self.running = False
            self.radar.abort_processing()
        elif message_type == "set_clutter_flag":
            self.radar.set_clutter_flag(data)

    def emit(self, message_type, message, data=None):
        self.sig_scan.emit(message_type, message, data)

    def format_error(self, e):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        err = "{}\n{}\n{}\n{}".format(exc_type, fname, exc_tb.tb_lineno, e)
        return err


def sigint_handler(gui):
    event = threading.Event()
    thread = threading.Thread(target=watchdog, args=(event,))
    thread.start()
    gui.closeEvent()
    event.set()
    thread.join()


def watchdog(event):
    flag = event.wait(1)
    if not flag:
        print("\nforcing exit...")
        os._exit(1)


if __name__ == "__main__":
    example_utils.config_logging(level=logging.INFO)

    app = QApplication(sys.argv)
    ex = GUI()

    signal.signal(signal.SIGINT, lambda *_: sigint_handler(ex))

    # Makes sure the signal is caught
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(200)

    sys.exit(app.exec_())
