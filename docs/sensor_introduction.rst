Radar sensor introduction
=========================

Welcome!
--------

We are very happy that you have decided to have a closer look at what Acconeer’s pulsed coherent radar technology can offer. We are working hard to give you the right tools to **“Explore the Next Sense”**, whether it is for remote monitoring of vital signs, smart city IoT, robot navigation or any other imaginable sensing application where precision, size, and power consumption are key parameters.
This document serves as an introduction to Acconeer’s sensor technology and product offer. The Acconeer radar system is described based on established radar theory to give you the right knowledge to integrate and configure the sensor in your product.

When starting to use the Acconeer sensor there are different alternatives for both hardware and software setup and we are adding more as we get to know your needs. Check out our website to see our current offer of sensors, modules, and evaluation kits. A typical development flow to get started is to setup one of our evaluation kits and:

* Use the Exploration tool to get data from sensor into Python to start application development for your use case

* Use the Radar system software API or Module protocol to start software development

* Use our Reference applications to get guidance on use case specific software solutions

To further support and guide you through the development process we also provide several user guides, data sheets, reference schematics, and reference layouts, which you can find at `acconeer.com <https://acconeer.com>`_. Also check out our Demo videos `Demo videos <https://www.youtube.com/channel/UC56HMJfKPSpamS-kMHXOcAw>`_ and `Application page <https://www.acconeer.com/applications>`_ to get inspiration on how you can solve different use cases and how the Acconeer sensor can be used in your application.

.. figure:: /_static/introduction/fig_selected_use_cases.png
    :scale: 30
    :align: center

Radar basics and the Acconeer pulsed coherent radar
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Radar is a well-established technology which has been used in many different applications where accurate and robust distance measurement is required. You can find radar in cars, in the process industry, in airplanes etc. However, most often these radar systems are big, power hungry and expensive, what Acconeer offer is a way to take radar into applications where size, cost and power consumption matter.
Radar is an acronym for Radio Detection and Ranging and is a way of determining range to an object by transmitting and detecting radio waves. Acconeer’s radar system is a time-of-flight system, which means that a radio wave is transmitted by a first antenna, reflected by an object, and then received by a second antenna. The time of flight between transmission and reception of the signal is measured, as illustrated in :numref:`fig_sensor_wave_object`.

.. _fig_sensor_wave_object:
.. figure:: /_static/introduction/fig_sensor_wave_object.png
    :scale: 100
    :align: center

    Illustration of the pulsed coherent radar system where the time of flight is measured to determine distance to object

The distance to the object can then be calculated by multiplying the time-of-flight with the speed of the radio wave (same as speed of light) and then dividing by two as the distance the signal has traveled is equal to two times the distance to the object. More details about the radar and the Acconeer approach can be found in the chapter `System Overview`_.

There are different approaches to building radar systems, each with its own pros and cons that typically results in a trade-off between accuracy and power consumption :numref:`fig_pulsed_coherent_radar`. At Acconeer we have solved this by combining two important features of a radar system, the first is that it is pulsed, which means that the radio part is shut down in between transmission of signals. In fact, the Acconeer radar is pulsed so fast that the radio is active less than 1 % of the time even when transmitting at maximum rate, this is how the power consumption can be kept low and optimized dependent on the update rate required by your application.

.. _fig_pulsed_coherent_radar:
.. figure:: /_static/introduction/fig_pulsed_coherent_radar.png
    :scale: 60
    :align: center

    Pulsed coherent radar.

The second feature is that it is coherent, which means that each transmitted signal has a stable time and phase reference on the pico second scale, which allows for high accuracy measurements. Coherent radar systems usually rely on a continuous generation of the radio signal, which consumes a lot of current independent on update rate, hence one of the innovations Acconeer have made is to combine the benefits of pulsed systems and the benefits of coherent systems into one product, the Pulsed Coherent Radar (PCR).
The unique selling points of the PCR sensor are summarized in :numref:`fig_unique_selling_points`. The sensor makes it possible to perform high accuracy measurements while consuming very little power and the fast pulsing of the system makes it possible to track fast movements.

.. _fig_unique_selling_points:
.. figure:: /_static/introduction/fig_unique_selling_points.png
    :scale: 60
    :align: center

    Unique selling points of the Acconeer pulsed coherent radar.

Another benefit of the pulse coherent radar is that amplitude, time and phase of the received signal can be handled separately and allow for classification of different materials that the signal has been reflected on. These are all benefits when compared to sensors such as infra-red and ultrasonic. Additional benefits are that the Acconeer radar can be hidden behind colored plastic or glass and hence do not need an open or visible aperture, we call this optimized integration. The sensor is also robust as it is not sensitive to ambient light or sound and not sensitive to dust or even color of the object.

The Acconeer offer
^^^^^^^^^^^^^^^^^^

The Acconeer offer consists of two parts, hardware and software, as illustrated in :numref:`fig_acconeer_offer`. In addition, Acconeer also provides various tools to aid the customer in the development process.

.. _fig_acconeer_offer:
.. figure:: /_static/introduction/fig_acconeer_offer.png
    :scale: 60
    :align: center

    The Acconeer offer.

The A111 sensor is the core of the hardware offer and is available in module and in evaluation kits. The purpose of the evaluation kit is to provide a platform to get acquainted with the pulsed coherent radar and to start use case evaluation. The sensor evaluation kits are based on Raspberry Pi, which is a well-known and available platform which also allows you to connected other types of sensors. The module is an integration of the A111 and a microcontroller unit (MCU) and has its own evaluation kit. Just as the sensor evaluation kit it can be used to get familiar with the pulsed coherent radar technology and get started with use case development. It can also be included as a single unit in your product to decrease your development cost and decrease time to market.

:numref:`fig_acconeer_offer` outlines the software structure, platform for running it, and communication interfaces. The software for controlling the A111 sensor and retrieving data from it is called Radar System Software (RSS) and provides output at two levels:

* Service, provides pre-processed sensor data

* Detector, provides results based on the sensor data - all Detectors are based on Services

.. _fig_system_structure:
.. figure:: /_static/introduction/fig_system_structure.png
    :scale: 80
    :align: center

    System structure, the RSS software runs on a host that controls the sensor.

RSS is provided as library files and is written in C and designed to be portable between different platforms, a list of currently supported processor architectures and toolchains are available at the Acconeer developer site acconeer.com. Apart from RSS Acconeer provides Example applications and stubbed software integration source code in the Software development kits (SDKs) as well as full reference integrations for selected platforms.

Acconeer provide four types of applications:

* Example applications: Example of how to use RSS, available in SDK at Acconeer developer site

* Reference applications: Use case specific reference application available at Acconeer GitHub

* Streaming server: Application streaming data from sensor evaluation kit to PC, available in SDK at Acconeer developer site

* Module server: Application providing a register write based interface to Acconeer modules, available in Module software image at Acconeer developer site.

Both RSS and Applications run on a host platform and Acconeer provides a software integration reference with guidance on how to integrate to your host platform as well as specific integration for the modules and evaluation kits that Acconeer provides. The software integration includes hardware abstraction layer, device drivers, and build environment provided as source code and is available in the SDK. Based on these deliveries it is possible for the customer to create their own integration layer for any platform that uses a supported processor architecture. The currently available products and corresponding software deliveries are listed in :numref:`fig_product_sw_offer`, refer to documentation for each specific product for further details.

.. _fig_product_sw_offer:
.. figure:: /_static/introduction/fig_product_sw_offer.png
    :scale: 50
    :align: center

    Products and software deliverables.

More SDK variants are available at Acconeer.com, they all contain RSS, Software integration, and Example applications. The Module software image contain RSS, software integration, and Module server and can be downloaded from acconeer.com.
The module can be used in two different setups:

* Stand-alone module: The module has got no dependency on external controllers. The application is customized to a specific use case by the customer and runs on the embedded MCU. The customers application is accessing the RSS API via a software interface.

* Controlled module: The module is connected to an external controller where the customer runs their application software. The customers are accessing the RSS API via a hardware interface through the module software, that provided register mapped protocol.

The two setups listed above are also illustrated in :numref:`fig_setups`.

.. _fig_setups:
.. figure:: /_static/introduction/fig_setups.png
    :scale: 80
    :align: center

    Setup.

For the Stand-alone module setup the customer should use the RSS library and Software integration source code provided in the corresponding SDK and build their own application on these deliveries. For the Controlled module regime, the complete software that runs on the module is delivered as an image. The customer can freely select between these two options, Acconeer supports both.


.. _Acconeer tools:

Acconeer tools
^^^^^^^^^^^^^^

To help you to get to know the Acconeer products and get started quickly with application development we provide a Python based tool which consists of several scripts that gives you access to real time data and sensor configuration to easily start developing signal processing for specific use cases. The scripts can also be used to graphically display the radar output and to investigate the reflective properties of different objects. The Exploration tool requires that the Streaming server or Module server is installed on your sensor evaluation kit or module evaluation kit, respectively. The Streaming Server and Module server reflects the RSS API, which helps to understand how to manage the RSS API in your application. The Exploration tool is provided for all our evaluation kits and is available at `Acconeer GitHub <https://github.com/acconeer/acconeer-python-exploration>`_. An overview of how Exploration tool interface software and hardware for the evaluation kits is presented in :numref:`fig_sw_hw_if`.

.. _fig_sw_hw_if:
.. figure:: /_static/introduction/fig_sw_hw_if.png
    :scale: 80
    :align: center

    Overview of software and hardware interfaces to Acconeer tools.


Services and Detectors
----------------------

The RSS provides output at two different levels, Service and Detector. The Service output is pre-processed sensor data as a function of distance. Detectors are built with this Service data as the input and the output is a result, in the form of e.g. distance, motion, angle etc. Services and Detectors currently available are listed in :numref:`fig_detectors_services`.

.. _fig_detectors_services:
.. figure:: /_static/introduction/fig_detectors_services.png
    :scale: 80
    :align: center

    Available Detectors and Services.

Each Detector is built on top of a Service, i.e. you have the possibility to use our out-of-the-box Detectors or develop your own. To select the Service or Detector applicable for your use case it is recommended to use the Exploration tool (see Section `Acconeer tools`_) to observe the different outputs and understand what they represent, each Service and Detector also comes with its own user guide, which can be found at `acconeer.com <https://acconeer.com>`_.

At `acconeer.com <https://acconeer.com>`_ we have several movies showing demos where the Acconeer sensor is used in different use cases. These demo movies come with use case specific reference applications, which are available for download at our GitHub page. These reference applications are written in C code and use our Services and Detectors, check out these examples to get inspiration on how to build your product with the Acconeer sensor.


Envelope and Power bin Services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:numref:`fig_power_bins_demo` and :numref:`fig_env_demo` show outputs from the Power bin and Envelope Services obtained with one of the scripts in Exploration tool, the setup and environment are identical for the two data sets. Here it can be seen that Power bin and Envelope Services provides output of the same type, i.e. amplitude of received signal as a function of distance. The difference lies in the signal processing done and the Power bin output has lower SNR, lower resolution in range, but requires less processing and memory allocation than Envelope.

.. _fig_power_bins_demo:
.. figure:: /_static/introduction/fig_power_bins_demo.png
    :scale: 60
    :align: center

    Output from the Power bin service in Exploration Tool.


.. _fig_env_demo:
.. figure:: /_static/introduction/fig_env_demo.png
    :scale: 60
    :align: center

    Output from the Envelope service in Exploration Tool.


IQ Service
^^^^^^^^^^

The IQ Service provides data in cartesian form, which is shown in :numref:`fig_iq_demo` with distance on the third axis, data taken with the same setup as for Envelope and Power bin in :numref:`fig_power_bins_demo` and :numref:`fig_env_demo`.

.. _fig_iq_demo:
.. figure:: /_static/introduction/fig_iq_demo.png
    :scale: 60
    :align: center

    Output from the Envelope service in Exploration Tool.

The cartesian data can be transformed to polar data providing phase and amplitude of the signal. Having the phase of the signal available makes it possible to perform more accurate measurements as compared to the Power bin and Envelope Services where only the amplitude is available. This is illustrated in :numref:`fig_wavelet` where an object is moving towards the radar. The envelope of the signal only varies slightly when the object is moving, while the value of the coherent signal at a fixed time delay varies substantially. This change will be present in the phase of the data from the IQ Service API.

.. _fig_wavelet:
.. figure:: /_static/introduction/fig_wavelet.png
    :scale: 70
    :align: center

    Illustration of envelope and phase change of a received pulse for a reflection from a moving object, what is returned from the IQ Service is in cartesian form.

The IQ Service is the choice when high accuracy is required, and higher processing power and memory allocation can be tolerated.


Detectors
^^^^^^^^^

Detectors take Service data as input and produce a result as the output that can be used by the application. Currently we have three Detectors available that produce different types of results and that are based on different Services. User guides for the different Detectors are available at acconeer.com and the Detectors are also available in the Exploration tool.

In addition, we provide several Reference applications which uses Services or Detector to demonstrate how to develop applications based on our technology, you can find these at the Acconeer GitHub.


Distance peak detector
~~~~~~~~~~~~~~~~~~~~~~

Finds peaks in the data provided from the Envelope Service and provides the distance to these peaks. The peaks are identified if above a threshold, which can be set to be fixed, based on the response from the environment without the object to be identified, or based on receiver noise. This Detector is used for the characterization of the A111 in the data sheet.


Motion detector
~~~~~~~~~~~~~~~

Records changes in the environment over time by using an adaptive threshold based on historic data. The Detector uses the amplitude information from the IQ service.


Distance basic
~~~~~~~~~~~~~~

Low complexity distance detection based on finding the maximum of the data provided from the Envelope Service.


Obstacle localization detector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assumes that the Acconeer sensor is placed on a moving object with a known velocity, such as a robotic vacuum cleaner or lawn mower. The Detector creates a virtual antenna array and uses synthetic aperture radar (SAR) signal processing to localize objects. This Detector is used in the Obstacle localization demo movie.


.. _ System Overview:

System overview
---------------

The Acconeer sensor is a pulsed coherent radar, which means that it transmits radio signals in short pulses where the starting phase is well known, as illustrated in :numref:`fig_transmit_signal_length`.

.. _fig_transmit_signal_length:
.. figure:: /_static/introduction/fig_transmit_signal_length.png
    :scale: 60
    :align: center

    Illustration of the time domain transmitted signal from the Acconeer A111 sensor, a radar sweep  typically consists of thousands of pulses.


These transmitted signals are reflected by an object and the time elapsed between transmission and reception of the reflected signal (:math:`t_{delay}`) is used to calculate the distance to the object by using

.. _Equation 1:

.. math::
    :label: Equation 1

    d=\frac{t_{delay}v}{2}

.. _Equation 2:

    .. math::
        :label: Equation 2

        v=\frac{c_0v}{\sqrt{\varepsilon_r}}

where :math:`\varepsilon_r` is the relative permittivity of the medium. The '2' in the denominator of is due to the fact that :math:`t_{delay}` is the time for the signal to travel to the object and back, hence to get the distance to the object a division by 2 is needed, as illustrated in :numref:`fig_sensor_wave_object`. As :math:`f_{RF}` is 60.5 GHz one wavelength (:math:`\lambda`) is roughly 5 mm, which then corresponds to a distance to the object of 2.5 mm.
:numref:`fig_block_diagram` shows a block diagram of the A111 sensor. The signal is transmitted from the Tx antenna and received by the Rx antenna, both integrated in the top layer of the A111 package substrate. In addition to the mmWave radio the sensor consists of power management and digital control, signal quantization, memory and a timing circuit.

.. _fig_block_diagram:
.. figure:: /_static/introduction/fig_block_diagram.png
    :scale: 100
    :align: center

    Block diagram of the A111 sensor, further details about interfaces can be found in the A111 data sheet.

:numref:`fig_envelope_2d` shows a typical radar sweep obtained with the Envelope Service, with one object present. The range resolution of the measurement is ~0.5 mm and each data point correspond to transmission of one pulse, hence, to sweep from 30 cm, from 20 cm to 50 cm as in :numref:`fig_envelope_2d`, requires that 600 pulses  are transmitted. The system relies on the fact that the pulses are transmitted phase coherent, which makes it possible to send multiple pulses and then combine the received signal from these pulses to improve signal-to-noise ratio (SNR) to enhance the object visibility.

.. _fig_envelope_2d:
.. figure:: /_static/introduction/fig_envelope_2d.png
    :scale: 60
    :align: center

    Output from Envelope service for a typical radar sweep with one object present.

The amount of energy received back to the Rx antenna depends on the reflectivity of the object (:math:`\gamma`), the radar cross section (RCS) of the object (:math:`\sigma`), and the distance to the object (R). A reflection occurs when there is a difference in relative permittivity between two media that the signal is propagating through, :math:`\gamma` is then given as


.. _Equation 3:

    .. math::
        :label: Equation 3

        \gamma=\left(\frac{\sqrt{\varepsilon_1}-\sqrt{\varepsilon_2}}{\sqrt{\varepsilon_1}+\sqrt{\varepsilon_2}}\right)^2

where :math:`\varepsilon_1` and :math:`\varepsilon_1` is the relative permittivity on either side of the boundary. The relative permittivity for common materials can be found in various data bases, but keep in mind that it is frequency dependent. As an example, `Table 1`_ lists approximate values for the real part of the relative permittivity for some common materials.

.. _Table 1:

    .. table:: Relative permittivity of common materials
        :align: center
        :widths: auto

        ==================== ===================================== ===========================================
        Material             :math:`real(\varepsilon_1)` at 60 GHz :math:`\gamma` with air boundary
        ==================== ===================================== ===========================================
        ABS plastic          2.48                                  0.049
        Mobile phone glass   6.9                                   0.02
        Plaster              2.7                                   0.059
        Concrete             4                                     0.11
        Wood                 2.4                                   0.046
        Textile              2                                     0.029
        Metal                --                                    1
        Human skin           8                                     0.22
        Water                11.1                                  0.28
        Air                  1                                     0
        ==================== ===================================== ===========================================


`Table 1`_ shows that some materials are semi-transparent to 60 GHz signals and it is hence possible to detect reflecting objects behind a surface of these materials, each boundary with a change in permittivity gives a reflection. This is a useful property in applications where the use case requires that the sensor measures through, e.g., a wall, clothing or plastic housing.

The radar cross section is the effective area of the object that the signal is reflected against, for simple geometrical shapes, where the size is larger than the wavelength of the signal (~5 mm) and is in the far-field distance, it can be expressed analytically as in :numref:`fig_rcs`. The far-field distance depends on the object size and its distance to the radar source. Generally speaking, far-field applies when the waves reflected by the object can be considered plane-waves. Representative back scattering pattern of a sphere, flat plate and trihedral corner reflector are shown in the polar plots.  It is seen that the objects can have different maximum RCS, but also different radiation patterns, a flat plate for instance is very directive and if tilted away from the Rx antenna the received energy will be decreased, whereas the corner has less angular dependence and is a more robust reflector in terms of angle with respect to the Rx antenna.

.. _fig_rcs:
.. figure:: /_static/introduction/fig_rcs.png
    :scale: 40
    :align: center

    Radiation pattern and analytical expressions for simple geometrical shapes.

For most objects it is not possible to analytically calculate σ, instead it needs to be measured or modelled or just tested if the received energy gives a high enough signal to noise ratio (SNR) to make a detection. The SNR is given by

.. _Equation 4:

    .. math::
        :label: Equation 4

        SNR_{dB}=10\log_{10}\frac{S}{N}=C_{dB}+\sigma_{dB}+\gamma_{dB}-k10\log_{10}(R)

where :math:`C` is the radar loop gain and :math:`R` is the distance to the object. :numref:`fig_rx_power_vs_dist` shows how the received energy drops with increasing R for objects where the exponent k is equal to 4, which applies for objects which are smaller than the area which is illuminated coherently by the radar. For objects that are larger than this area the :math:`k` is smaller than 4, with a lower limit of :math:`k = 2`  when the object is a large flat surface.

.. _fig_rx_power_vs_dist:
.. figure:: /_static/introduction/fig_rx_power_vs_dist.png
    :scale: 60
    :align: center

    Received signal power versus distance. Note: signal, S, is plotted in dB.

In `Table 2`_ and `Table 3`_ the visibility for a range of objects with common shapes (cylinder, plate, etc.) and of varying reflectivity, i.e. materials, is shown. Objects are at normal incidence and the governing system parameters are σ, γ, and C, as show in `Equation 4`_. The envelope service was used to collect the data with the maximize SNR configuration. The object counts as distinguishable from the noise with a SNR > 10 dB (Y), barely visible between 5dB and 10dB (-) and not visible with a SNR < 5 dB (N).
The range can be further increased based on the configuration of the sensor, as described in Section `Configuring the Acconeer sensor`_ and by optimizing the physical integration, as will be described in Section `Physical integration aspects`_. As an example for such an optimization `Table 3`_ shows results with an added radar Fresnel lens.

.. _Table 2:

    .. table:: Typical ranges without lens
        :align: center
        :widths: auto

        ====================================== ===== ===== ===== ===== =====
        Object                                 0.5 m 1 m   2 m   5 m   10 m
        ====================================== ===== ===== ===== ===== =====
        Corner reflector (a=4cm)               Y     Y     Y     Y     N
        Planar water surface                   Y     Y     Y     Y     Y
        Disc (r=4cm)                           Y     Y     Y     Y     Y
        Cu Plate (10x10cm)                     Y     Y     Y     Y     Y
        PET plastic Plate (10x10cm)            Y     Y     Y     Y     --
        Wood Plate (10x10cm)                   Y     Y     --    N     N
        Cardboard Plate (10x10cm)              Y     Y     Y     N     N
        Al Cylinder (h=30, r =2cm)             Y     Y     --    N     N
        Cu Cylinder (h=12, r =1.6cm)           Y     Y     Y     N     N
        PP plastic Cylinder (h=12, r =1.6cm)   Y     N     N     N     N
        Leg                                    Y     Y     --    N     N
        Hand (front)                           Y     Y     N     N     N
        Torso (front)                          Y     Y     Y     N     N
        Head                                   Y     Y     N     N     N
        Glass with water (h=8.5, r=2.7cm)      Y     Y     N     N     N
        PET Bottle with water (h=14, r=4.2cm)  Y     Y     N     N     N
        Football                               Y     Y     N     N     N
        ====================================== ===== ===== ===== ===== =====


.. _Table 3:

    .. table:: Typical ranges with 7dB radar lens
        :align: center
        :widths: auto

        ====================================== ===== ===== ===== ===== =====
        Object                                 0.5 m 1 m   2 m   5 m   10 m
        ====================================== ===== ===== ===== ===== =====
        Corner reflector (a=4cm)               Y     Y     Y     Y     Y
        Planar water surface                   Y     Y     Y     Y     Y
        Disc (r=4cm)                           Y     Y     Y     Y     Y
        Cu Plate (10x10cm)                     Y     Y     Y     Y     Y
        PET plastic Plate (10x10cm)            Y     Y     Y     Y     Y
        Wood Plate (10x10cm)                   Y     Y     Y     Y     N
        Cardboard Plate (10x10cm)              Y     Y     Y     Y     --
        Al Cylinder (h=30, r =2cm)             Y     Y     Y     Y     --
        Cu Cylinder (h=12, r =1.6cm)           Y     Y     Y     Y     --
        PP plastic Cylinder (h=12, r =1.6cm)   Y     Y     Y     N     N
        Leg                                    Y     Y     Y     Y     N
        Hand (front)                           Y     Y     Y     N     N
        Torso (front)                          Y     Y     Y     Y     N
        Head                                   Y     Y     Y     --    N
        Glass with water (h=8.5, r=2.7cm)      Y     Y     Y     --    N
        PET Bottle with water (h=14, r=4.2cm)  Y     Y     Y     N     N
        Football                               Y     Y     Y     N     N
        ====================================== ===== ===== ===== ===== =====



.. _Configuring the Acconeer sensor:

Configuring the Acconeer sensor
-------------------------------

The Acconeer sensor is highly configurable and can operate in many different modes where parameters are tuned to optimize the sensor performance for specific use cases. The first step is to select between the two basic configuration profiles provided to optimize on either depth resolution or SNR, or in terms of use cases, optimized for multiple objects/close range or for weak reflections/long range, respectively. Depth resolution (:math:`d_{res}`) is the ability to resolve reflections which are closely spaced, and hence depends on tpulse according to

.. _Equation 5:

    .. math::
        :label: Equation 5

        d_{res}=\frac{t_{pulse}v}{2}


:numref:`fig_distance_resolution` illustrates how the ability to resolve closely spaced reflections can be improved by decreasing tpulse. On the other hand, decreasing tpulse means that the total energy in the pulse is decreased and hence the SNR in the receiver, this is the trade-off that is made by selecting between the two profiles.

.. _fig_distance_resolution:
.. figure:: /_static/introduction/fig_distance_resolution.png
    :scale: 60
    :align: center

    Illustration of received signal containing 2 echoes. A longer pulsewavelet increases the transmitted energy, but also limits the depth resolution. The displayed data corresponds to the two setups in :numref:`fig_scenario`.


.. _fig_scenario:
.. figure:: /_static/introduction/fig_scenario.png
    :scale: 60
    :align: center

    Illustration of scenarios that can produce the data in :numref:`fig_distance_resolution`. A strong reflector, such as a flat metallic surface, can give a moderate radar signal if the angle to the radar is high. R1 is identical in the two illustrations as well as R2.


If angular information is needed one possibility is to mechanically move the sensor to scan an area and produce a synthetic aperture radar (SAR). One such case is for autonomous robots using sensor input for navigation. Another option is to use multiple A111 sensors and merge data from them to calculate the position of the object by trilateration. This can be achieved by running the sensors sequentially and merge the data in the application. We also have the possibility to create a multi-static radar by synchronizing multiple sensors to allow for 1 sensor to transmit and multiple to receive at the same time, this mode is currently not available in our software.

Optimizing on depth resolution also means that close in range performance is improved. The A111 sensor has both the Tx and Rx antenna integrated and as they are so closely spaced there will be leakage between the two antennas. This means that any objects close to the sensor will have to be filtered from this static leakage. The ability to do this is improved if a short tpulse is used, as illustrated in :numref:`fig_close_in_distance`.


.. _fig_close_in_distance:
.. figure:: /_static/introduction/fig_close_in_distance.png
    :scale: 60
    :align: center

    Illustration of how the leakage between the Tx and Rx antenna will appear in the Envelope Service data for a short and a long pulse.

`Table 4`_  shows a list of important parameters that are available through our API and that can be used to optimize the performance for a specific use case, refer to product documentation and user guides for a complete list of all parameters and how to use them.


.. _Table 4:

    .. table:: List of sensor parameters
        :align: center
        :widths: auto

        ================== ===========================================================================
        Parameter          Comment
        ================== ===========================================================================
        Profile            Select between Maximize SNR or Maximize Depth Resolution
        Receiver gain      Adjust to accommodate received signal level
        Start range        Start of sweep
        Sweep length       Length of sweep, set independently of Start range
        Running average    Filtering to average over sweeps to stabilize the amplitude [#]_
        Frequency          Desired rate at which sweeps are generated
        Power save mode    Tradeoff between power consumption and rate at which sweeps are generated
        ================== ===========================================================================


.. [#] The filtered signal :math:`\hat{y}(r,s)` at distance :math:`r` and for sweep :math:`s` is :math:`\hat{y}(r,s)=(1-k)y(r,s)+k\hat{y}(r,s-1)`, where :math:`y(r,s)` is the unfiltered signal and :math:`k` is the running average factor.

Different power modes will limit the maximum obtainable sweep frequency, as will start and end range and the speed of the SPI data transfer. `Table 5`_ shows a reference measurement indicating the point at which the sensor reaches the maximum limit on sweep frequency for the 4 different power modes for the specific integration of ‘XM112’ and for a sweep configuration identical to that used in the data sheet.


.. _Table 5:

    .. table:: Maximum sweep frequency @ SPI data transfer rate of 30 MHz
        :align: center
        :widths: auto

        ================== ===========================================================================
        Power mode         Maximum sweep frequency of sensor for SPI data transfer rate of 30 MHz
        ================== ===========================================================================
        A                  TBD
        B                  TBD
        C                  TBD
        D                  TBD
        ================== ===========================================================================


.. _Physical integration aspects:

Physical integration aspects
----------------------------

The A111 sensor contains the mmWave front-end, digital control logic, digitization of received signal and memory, all in one package. To integrate it in your application it is required to have a reference frequency or XTAL (20-80 MHz), 1.8 V supply, and a host processor, as illustrated in :numref:`fig_host_platform`, supported platforms and reference schematics are available at `developer.acconeer.com <https://developer.acconeer.com>`_.


.. _fig_host_platform:
.. figure:: /_static/introduction/fig_host_platform.png
    :scale: 60
    :align: center

    Illustration of integration into host platform, the A111 is marked with the Acconeer logo.

In addition to the above it is also important for optimized integration to consider the electromagnetic (EM) environment, both in terms of what is placed on top of the sensor as well as to the side of the sensor. To evaluate the EM integration a Radar loop measurement can be conducted by placing an object in front of the sensor and rotating the sensor around its own axis, as illustrated in :numref:`fig_radar_loop_pattern`. The received energy from e.g. the Envelope Service can then be used to plot the amplitude versus rotation angle (θ).


.. _fig_radar_loop_pattern:
.. figure:: /_static/introduction/fig_radar_loop_pattern.png
    :scale: 60
    :align: center

    Setup configuration for radar loop pattern measurements.


The radiation pattern of the integrated antennas will be affected by anything that is put on top of the sensor as a cover. The transmission through a material is given by 1-γ, where γ is the reflectivity calculated in Equation 3. Hence, materials with low reflectivity are good materials to use as a cover on top of the sensor, plastic is a good choice and the sensor is not sensitive to the color of the material. Figure 21 shows the measured Radar loop pattern for 3 different scenarios, plastic (ABS), gorilla glass (GorillaGlass) and free space (FS). To further optimize the cover integration the thickness of the material should be considered. One can also use a layered cover which uses materials of different ε for optimum matching to the medium in which the signal is going to propagate or even to increase the directivity, as shown in Figure 21, where the beam width has been decreased by adding material on top of the sensor. More information on the EM integration aspects can be found in “Electromagnetic Integration - Basic Guidelines” document available at `developer.acconeer.com <https://developer.acconeer.com>`_.


.. _fig_h_plan_pattern:
.. figure:: /_static/introduction/fig_h_plan_pattern.png
    :scale: 60
    :align: center

    Integration of sensor cover and how different materials impact the radiation pattern on the H-plane. The object used is a trihedral corner of radius 5 cm.


Summary
-------

Acconeer’s Pulsed coherent radar technology is unique as it combines high precision and low power consumption into a tiny package and for the first time enables radar in products where size, cost and power consumption matters. We are committed to making the technology available to everyone and we are working hard to make it easy for you to take your product to the market, whether you need pre-integrated hardware or new Detectors we will help you to get the product to your customers.
Sign up for our newsletter or check out our website and Github for updates on new cool features that we have released, we are constantly innovating, **“Explore the next sense!”**.


Disclaimer
----------

The information herein is believed to be correct as of the date issued. Acconeer AB (**“Acconeer”**) will not be responsible for damages of any nature resulting from the use or reliance upon the information contained herein. Acconeer makes no warranties, expressed or implied, of merchantability or fitness for a particular purpose or course of performance or usage of trade. Therefore, it is the user’s responsibility to thoroughly test the product in their particular application to determine its performance, efficacy and safety. Users should obtain the latest relevant information before placing orders.
Unless Acconeer has explicitly designated an individual Acconeer product as meeting the requirement of a particular industry standard, Acconeer is not responsible for any failure to meet such industry standard requirements.
Unless explicitly stated herein this document Acconeer has not performed any regulatory conformity test. It is the user’s responsibility to assure that necessary regulatory conditions are met and approvals have been obtained when using the product. Regardless of whether the product has passed any conformity test, this document does not constitute any regulatory approval of the user’s product or application using Acconeer’s product.
Nothing contained herein is to be considered as permission or a recommendation to infringe any patent or any other intellectual property right. No license, express or implied, to any intellectual property right is granted by Acconeer herein.
Acconeer reserves the right to at any time correct, change, amend, enhance, modify, and improve this document and/or Acconeer products without notice.
This document supersedes and replaces all information supplied prior to the publication hereof.
