import pyvisa
#import time
import numpy as np
from PyQt5.QtWidgets import QHBoxLayout,  QLineEdit,QLabel,QVBoxLayout

class Keysight:
    def __init__(self,app):
        self.app=app
        self.model_name="E36105B"
        self.resource_str="USB0::0x2A8D::0x1802::MY61001772::0::INSTR"
        try:
            # needs the existence of a driver like 'C:\WINDOWS\system32\visa32.dll' or similar
            rm = pyvisa.ResourceManager()
            self.psu = rm.open_resource(self.resource_str)
            print("Keysight connected")
            self.connected=True
            self.app.add_log("Keysight connected")
        except:
            self.connected=False
            #self.psu = "dummy"
            print("dummy mode for keysight")
            self.app.add_log("Keysight dummy mode")


        self.voltage=0
        self.current=0
        self.output_on=False

        self.voltages_set = []
        self.voltages_measured = []
        self.currents_measured = []

    def on(self):
        self.psu.write ("OUTP ON")

    def off(self):
        self.psu.write ("OUTP OFF")

    def set_voltage(self, voltage):
        self.psu.write(f"SOUR:VOLT {voltage}")
        #time.sleep(1.01)

    def set_current(self, current):
        self.psu.write(f"SOUR:CURR {current}")
        #time.sleep(1.01)

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

    def expand(self):
        if not self.expanded:
            self.expanded=True
            self.app.set_layout_visible(self.dropdown,True)
        else:
            self.expanded=False
            self.app.set_layout_visible(self.dropdown,False)

    def power_ui(self,layoutright):
        self.expanded=False
        self.app.heading_label(layoutright,"LED Power Supply",self.expand)

        self.dropdown=QVBoxLayout()
        
        layoutoutput=QHBoxLayout()
        self.app.normal_button(layoutoutput,"Output",self.power_on)
        label = QLabel("grey   -> off\ngreen -> on")
        label.setStyleSheet("color:white")
        label.setWordWrap(True)
        layoutoutput.addWidget(label)
        layoutoutput.addStretch()

        
        self.dropdown.addLayout(layoutoutput)
        layoutset=QHBoxLayout()
        voltwidget = QLineEdit()
        voltwidget.setStyleSheet("background-color: lightGray")
        voltwidget.setMaxLength(7)
        voltwidget.setFixedWidth(self.app.standard_width)
        voltwidget.setText(str(0.0))
        label = QLabel("voltage (V)")
        label.setStyleSheet("color:white")
        layoutset.addWidget(voltwidget)
        layoutset.addWidget(label)
        layoutset.addStretch()
        currentwidget = QLineEdit()
        currentwidget.setStyleSheet("background-color: lightGray")
        currentwidget.setMaxLength(7)
        currentwidget.setFixedWidth(self.app.standard_width)
        currentwidget.setText(str(0.0))
        label = QLabel("current (mA)")
        label.setStyleSheet("color:white")
        layoutset.addWidget(label)
        layoutset.addWidget(currentwidget)
        
        self.dropdown.addLayout(layoutset)
        layoutfresh=QHBoxLayout()
        freshwidget = QLineEdit()
        freshwidget.setStyleSheet("background-color: lightGray")
        freshwidget.setMaxLength(7)
        freshwidget.setFixedWidth(self.app.standard_width)
        freshwidget.setText(str(1.0))
        label = QLabel("refresh interval (s)")
        label.setStyleSheet("color:white")
        layoutfresh.addWidget(freshwidget)
        layoutfresh.addWidget(label)
        layoutfresh.addStretch()

        self.app.normal_button(layoutfresh,"Live",self.live_mode)

        self.dropdown.addLayout(layoutfresh)
        layoutmax=QHBoxLayout()
        btn=self.app.normal_button(layoutmax,"Maximize View",self.maximize)
        btn.setFixedWidth(110)
        layoutmax.addStretch()
        self.dropdown.addLayout(layoutmax)

        layoutright.addLayout(self.dropdown)
        self.app.set_layout_visible(self.dropdown,False)
        layoutright.addItem(self.app.vspace)


    def power_on(self):
        if self.output_on:
            self.output_on=True
            self.psu.write ("OUTP OFF")
        else:
            self.output_on=False
            self.psu.write ("OUTP ON")

    def maximize(self):
        pass

    def live_mode(self):
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