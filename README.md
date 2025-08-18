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
