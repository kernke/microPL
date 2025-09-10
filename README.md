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
    electric_measurement_to_timeline
    save_timeline

    # setting an acquisition time ends the auto-exposure
    spectral_acquisition_time_s: 1

    acquisition_name : Dark image
    spectral_shutter_mode: closed
    spectral_acquire

    group_name: IV-curve measurement
    measure_iv_curve_set_currents, spectral_bool:0,spatial_bool:1,start_current_mA:0,end_current_mA:100,step_current_mA:5,settling_time_s:0.1






