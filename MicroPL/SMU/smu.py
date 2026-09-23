import numpy as np
import time
#import pyqtgraph as pg
import serial


from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QVBoxLayout,
    QApplication
)

from PyQt5.QtCore import (
    pyqtSignal,
    QRunnable,
    pyqtSlot,
    QObject
)

class SMU:
    def __init__(self,app):
        self.app=app
        self.COM_PORT = "COM22"
        self.GPIB_ADDRESS = 16

        self.connected=False
        try:
            self.connect()
            print("SMU connected")
            self.connected=True

            # Default Settings:

            # Set data format to clean comma-separated values (G5,2,0)
            self.write("G5,2,0X")

            # Keithley 237: voltage source, current measurement
            self.write("F0,0X")

            # 99 mA current compliance
            self.write("L0.099,0X")


        except:
            print("SMU dummy mode")

    def connect(self):
        self.ser = serial.Serial(self.COM_PORT, 115200, timeout=2)

        self.write("++mode 1")
        self.write(f"++addr {self.GPIB_ADDRESS}")
        self.write("++auto 0")


    def write(self,cmd):
        self.ser.write((cmd + "\n").encode())
        time.sleep(0.1)

    def read(self):
        return self.ser.readline().decode(errors="ignore").strip()
    