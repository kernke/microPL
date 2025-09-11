[![Python package](https://github.com/kernke/microPL/actions/workflows/python-package.yml/badge.svg)](https://github.com/kernke/microPL/actions/workflows/python-package.yml)

# microPL
Setup to control several devices, execute measurement sequences and preliminary show the data 

# Installation
When installing the first time, change into the directory containing setup.py and install via 

    pip install -r requirements.txt
    pip install https://github.com/MSLNZ/msl-equipment/releases/download/v0.2.0/msl_equipment-0.2.0-py3-none-any.whl
    pip install . 

For updating the package, it's just

    pip install . 

# Usage
Can be started from jupyter with the following two cells:

    import MicroPL as MPL
    from PyQt5.QtCore import QCoreApplication
    %gui qt

The first cell covers the imports and sets the kernel to an interactive mode.

    app = QCoreApplication.instance()
    window = MPL.MainWindow()
    window.show()
    app.exec()

The second cell actually starts the interface.

# Scripting

Nearly all buttons and functions of the interface can also be called in a scripted manner via a .txt-file.
Functions that just manipulate the display settings without affecting the saved data are not included.
Additionally, the functions to set the limits of the stage and the electric power supply are exempt to prevent any damage.
The .txt-file should include one command, corresponding to a click in the user interface, per line.
Empty lines or lines with just white spaces are ignored, as well as lines starting with a hashtag "#".

The .txt-file can be imported by choosing "from settings txt" under the tab "Scripts". 
While importing, the file is checked for invalid commands or typos and the line numbers including errors are displayed in the logging window.
When no errors are found, the script can be started and from top to bottom the commands in the .txt-file are executed sequentially.

    example_script.txt
    
    # a commment
    spatial_acquisition_time_s : 2.1
    spatial_acquire
    # any parameters not given explicitly, will be taken from the values
    # that were present, when the script was started
     
    spectral_auto_exposure, start_s: 0.1,min_s:0.01,  max_s   :3.4
    save_spectral_image_bool :  False
    spectral_acquire
    
    voltage_V : 5
    current_mA :3
    electric_output_bool : True
    
    sleep_s : 60

    # read out the actual voltage and current
    electric_measurement_to_timeline
    save_timeline

    # setting an acquisition time ends the auto-exposure
    spectral_acquisition_time_s: 1
    # alternatively "spectral_auto_exposure_stop" would have fixed the acquisition time
    # to the time determined by the previous acquisition

    acquisition_name : Dark image
    spectral_shutter_mode: closed
    spectral_acquire

    group_name: IV-curve measurement
    measure_iv_curve_set_currents, spectral_bool:0,spatial_bool:1,start_current_mA:0,end_current_mA:100,step_current_mA:5,settling_time_s:0.1

As can be seen in the example, three different types of commands exist.  
First, single keyword commands like "spectral_acquire",  
second, keywords that take a value separated by ":" like "voltage_V",  
and third, keywords that take further keywords with values, where each pair is separated by "," , like "spectral_auto_exposure".  
Within the line of one command only the keywords and separators matter, white spaces are ignored.  
Keywords that end with "bool" take either "True" and "False" or "1" and "0".  
Keywords that take a number typically specify the unit with the last letters.  
Comments need to fill their own line starting with "#", comments after a command are not supported.  
During script execution the otherwise automatically once per second refreshing timeline of current and voltage is stopped.  
However, any command changing the state of the electric power supply, as well as any image acquisition, is followed with an update of the timeline. If the voltage and current are supposed to be read out at any other point during the script execution "electric_measurement_to_timeline" updates the timeline explicitly.  
Any values that have been set, persist until they are changed, similar to using the interface interactively.  
Other scripts like "measure_iv_curve_set_currents" can be called as well.  
Note, that the mechanical shutter of the spectrometer is per default set to "Always Open" before the script execution and returned to "Normal" (opening and closing upon image acquisuition) afterwards.

Finally, an overview of the supported commands:

commands that are single keywords:

    save_timeline, reset_timeline, save_comment_only, spectral_acquire, spatial_acquire,
    spatial_auto_exposure_stop, spectral_auto_exposure_stop, electric_measurement_to_timeline

commands that take any positive floating number:

    spatial_acquisition_time_s, spectral_acquisition_time_s, center_wavelength_nm, stage_x_mm, 
    stage_y_mm, sleep_s, voltage_V, current_mA

commands that take a boolean:

    save_spectral_image_bool, electric_output_bool

commands that take any (except empty) string:

    comment, group_name, acquisition_name

commands that take a specific string:

    spectral_shutter_mode : normal,open,closed
    grating : 1, 2, 3, 4, 5, 6
    spatial_resolution : 2048, 1024, 512

commands that take keyword-value pairs:

    spatial_auto_exposure : start_s, min_s, max_s
    spectral_auto_exposure : start_s, min_s, max_s
    stage_mapping : spectral_bool, spatial_bool, x_min_mm, x_max_mm, x_num_int, y_min_mm, y_max_mm, y_num_int
    spectral_roi : x_min_int, x_max_int, y_min_int, y_max_int
    measure_iv_curve_set_currents : spectral_bool, spatial_bool, start_current_mA, end_current_mA, step_current_mA, settling_time_s
    measure_iv_curve_set_voltages : spectral_bool, spatial_bool, start_voltage_V, end_voltage_V, step_voltage_V, settling_time_s
