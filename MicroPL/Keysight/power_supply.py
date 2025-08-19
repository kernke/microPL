import pyvisa
import time
import numpy as np
from PyQt5.QtWidgets import QHBoxLayout,  QLineEdit,QLabel

class Keysight:
    def __init__(self,app):
        self.model_name="E36105B"
        self.resource_str="USB0::0x2A8D::0x1802::MY61001772::0::INSTR"
        rm = pyvisa.ResourceManager()
        self.psu = rm.open_resource(self.resource_str)

        print("Keysight connected")

        self.app=app
        self.voltage=0
        self.current=0

        self.voltages_set = []
        self.voltages_measured = []
        self.currents_measured = []

    def on(self):
        self.psu.write ("OUTP ON")

    def off(self):
        self.psu.write ("OUTP OFF")

    def set_voltage(self, voltage):
        self.psu.write(f"SOUR:VOLT {voltage}")
        time.sleep(1.01)

    def set_current(self, current):
        self.psu.write(f"SOUR:CURR {current}")
        time.sleep(1.01)

    def measure_voltage(self):
        return float(self.psu.query("MEAS:VOLT?").strip())

    def measure_current(self):
        return float(self.psu.query("MEAS:CURR?").strip())

    def measure(self, voltage_step, max_voltage):
        print("Starting measurement...")
        self.on()

        for v in np.arange(0, max_voltage + voltage_step, voltage_step):
            self.set_voltage(v)

            meas_v = self.measure_voltage()
            meas_i = self.measure_current()

            self.voltages_set.append(v)
            self.voltages_measured.append(meas_v)
            self.currents_measured.append(meas_i)

            print(f"Set {v:>4.1f} V -> Measured: {meas_v:>6.3f} V, {meas_i*1000:>7.3f} mA")

        self.off()

    def power_ui(self,layoutright):
        self.app.heading_label(layoutright,"LED Power Supply")####################################################

        layoutlim=QHBoxLayout()
        label = QLabel("Set        ")
        label.setStyleSheet("color:white")
        layoutlim.addWidget(label)

        layoutlim.addStretch()
        self.app.normal_button(layoutlim,"<- Switch ->",self.power_switch)        
        #btn.setFixedWidth(80)
        layoutlim.addStretch()

        label = QLabel("Limit (max)")
        label.setStyleSheet("color:white")
        layoutlim.addWidget(label)

        layoutright.addLayout(layoutlim)

        layoutset=QHBoxLayout()
        voltwidget = QLineEdit()
        voltwidget.setStyleSheet("background-color: lightGray")
        voltwidget.setMaxLength(7)
        voltwidget.setFixedWidth(self.app.standard_width)
        voltwidget.setText(str(0.0))
        label = QLabel("Voltage (V)")
        label.setStyleSheet("color:white")
        layoutset.addWidget(voltwidget)
        layoutset.addWidget(label)
        layoutset.addStretch()
        currentwidget = QLineEdit()
        currentwidget.setStyleSheet("background-color: lightGray")
        currentwidget.setMaxLength(7)
        currentwidget.setFixedWidth(self.app.standard_width)
        currentwidget.setText(str(0.0))
        label = QLabel("Current (mA)")
        label.setStyleSheet("color:white")
        layoutset.addWidget(label)
        layoutset.addWidget(currentwidget)
        
        layoutright.addLayout(layoutset)
        layoutright.addStretch()

    def power_switch(self):
        pass


    """
    def plot_iv_detailed(self, zoom_voltage=1):
        plt.figure()
        plt.plot(self.voltages_measured, self.currents_measured, marker='o')
        plt.xlabel("Measured Voltage (V)")
        plt.ylabel("Measured Current (A)")
        plt.title("I/V Curve from Keysight")
        plt.grid(True)

        plt.figure()
        plt.plot(self.voltages_measured, self.currents_measured, marker='o')
        plt.xlim(0, zoom_voltage)
        plt.xlabel("Measured Voltage (V)")
        plt.ylabel("Measured Current (A)")
        plt.title("I/V Curve Zoomed from Keysight")
        plt.grid(True)

        plt.figure()
        plt.plot(self.voltages_measured, self.currents_measured, marker='o')
        plt.xlabel("Measured Voltage (V)")
        plt.ylabel("Measured Current (A)")
        plt.title("I/V Curve (Log Scale)")
        plt.yscale("log")
        plt.grid(True, which="both")
        
        plt.show()
    """