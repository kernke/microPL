import numpy as np
import time
#import pyqtgraph as pg
import serial


class SMU:
    def __init__(self,app):
        self.app=app
        self.COM_PORT = "COM22"
        self.GPIB_ADDRESS = 16
        self.latency_time=0.1

        self.connected=False
        try:
            self.connect()
            print("SMU connected")
            self.connected=True

            self.set_voltage_V=0
            self.voltage_actual=0
            self.currentA_actual=0
            self.settling_time=0.5

        except:
            print("SMU dummy mode")
            self.app.add_log("SMU dummy mode")


    def connect(self):
        self.ser = serial.Serial(self.COM_PORT, 115200, timeout=2)

        self.write("++mode 1")
        self.write(f"++addr {self.GPIB_ADDRESS}")
        self.write("++auto 0")

        # Default Settings:

        # Set data format to clean comma-separated values (G5,2,0)
        self.write("G5,2,0X")

        # Keithley 237: voltage source, current measurement
        self.write("F0,0X")

        # 99 mA current compliance
        self.write("L0.099,0X")

        # Enable output
        self.write("N1X")

        self.app.add_log("SMU connected")


    def write(self,cmd):
        self.ser.write((cmd + "\n").encode())
        time.sleep(self.latency_time)

    def read(self):
        return self.ser.readline().decode(errors="ignore").strip()

    def set_voltage(self,voltage_V=None):
        if voltage_V:
            self.write(f"B{voltage_V},0,0X")
        else:
            self.write(f"B{self.set_voltage_V},0,0X")
        time.sleep(self.settling_time)

    def readout(self):
        # Trigger measurement
        self.write("H0X")
   
        # Read result
        self.write("++read eoi")
        response = self.read()

        try:
            values = response.split(",")
            self.currentA_actual = float(values[1])
            self.voltage_actual = float(values[0])
        except (ValueError, IndexError):
            print("Could not parse:", repr(response))
            self.readout()

