import pyvisa
#import time
import numpy as np
#import time
import pyqtgraph as pg
from PyQt5.QtWidgets import QHBoxLayout,  QLineEdit,QLabel,QVBoxLayout
from PyQt5.QtCore import pyqtSignal, QTimer,QRunnable,pyqtSlot,QObject

class Update_Signal(QObject):

    string_update = pyqtSignal(object)   

class Status_update(QRunnable):

    def __init__(self, psu):
        super().__init__()
        self.psu = psu
        self.signals=Update_Signal()

    @pyqtSlot()
    def run(self): # A slot takes no params
        voltage_actual= float(self.psu.query("MEAS:VOLT?").strip())
        statusstring="Voltage: "+str(np.round(voltage_actual,3))+" V\n"
        currentA_actual=float(self.psu.query("MEAS:CURR?").strip())
        statusstring+="Current: "+str(np.round(currentA_actual*1000,2))+" mA"

        self.signals.string_update.emit((statusstring,voltage_actual,currentA_actual))
 
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
            print("dummy mode for keysight")
            self.app.add_log("Keysight dummy mode")


        self.voltage=0
        self.current=0
        self.output_on=False

        self.refresh_rate=1.
        self.voltage_actual=0
        self.currentA_actual=0

        self.maximized=False

    def disconnect(self):
        if self.live_mode_running:
            self.live_mode_running=False
            self.timer.stop()
        self.psu.close() 
        print("Keysight disconnected")

    def thread_task(self):
        self.worker=Status_update(self.psu)
        self.worker.signals.string_update.connect(self.status_update_from_thread)
        self.app.threadpool.start(self.worker)


    def status_update_from_thread(self,string_volt_curr_tuple):
        self.app.status_electric.setText(string_volt_curr_tuple[0])
        self.voltage_actual=string_volt_curr_tuple[1]
        self.currentA_actual=string_volt_curr_tuple[2]


    #def measure_electric(self):
    #    self.voltage_actual= float(self.psu.query("MEAS:VOLT?").strip())
    #    self.app.status_voltage.setText("Voltage: "+str(np.round(self.voltage_actual,3))+" V")
    #    print("sdf")
    #    self.currentA_actual=float(self.psu.query("MEAS:CURR?").strip())
    #    self.app.status_current.setText("Current: "+str(np.round(self.currentA_actual*1000,2))+" mA")
    


    def measure_IV(self, voltage_step, max_voltage):
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

    def expand2(self):
        if not self.expanded2:
            self.expanded2=True
            self.app.set_layout_visible(self.dropdown2,True)
        else:
            self.expanded2=False
            self.app.set_layout_visible(self.dropdown2,False)

    def setvoltage_edited(self,s):
        if s:
            self.voltage=np.double(s)
            self.psu.write(f"SOUR:VOLT {self.voltage}")

    def setcurrent_edited(self,s):
        if s:
            self.current=np.double(s)
            self.psu.write(f"SOUR:CURR {self.current/1000}")

    def refreshrate_edited(self,s):
        if s:
            if self.live_mode_running:
                self.refresh_rate=np.double(s)
                self.timer.stop()
                self.timer.start(int(1000*self.refresh_rate))
            else:
                self.refresh_rate=np.double(s)



    def power_ui(self,layoutright):
        #self.measure_electric()

        self.timer=QTimer()
        self.timer.timeout.connect(self.thread_task)
        self.live_mode_running=False
        if self.connected:
            self.live_mode()


        self.expanded=False
        self.app.heading_label(layoutright,"Electric Power Supply",self.expand)

        self.dropdown=QVBoxLayout()
        
        layoutoutput=QHBoxLayout()
        self.powerbtn=self.app.normal_button(layoutoutput,"Output",self.power_on)
        label = QLabel("grey   -> off\ngreen -> on         cyan -> limited by")
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
        voltwidget.setText(str(np.round(self.voltage_actual,3)))

        voltwidget.textEdited.connect(self.setvoltage_edited)
        label = QLabel("voltage (V)")
        label.setStyleSheet("color:white")
        layoutset.addWidget(voltwidget)
        layoutset.addWidget(label)
        layoutset.addStretch()
        currentwidget = QLineEdit()
        currentwidget.setStyleSheet("background-color: lightGray")
        currentwidget.setMaxLength(7)
        currentwidget.setFixedWidth(self.app.standard_width)
        currentwidget.setText(str(np.round(self.currentA_actual*1000,1)))
        currentwidget.textEdited.connect(self.setcurrent_edited)
        label = QLabel("current (mA)")
        label.setStyleSheet("color:white")
        layoutset.addWidget(label)
        layoutset.addWidget(currentwidget)
        
        self.dropdown.addLayout(layoutset)

        layoutsafe=QHBoxLayout()
        btn=self.app.normal_button(layoutsafe,"Safety limits",self.maximize)
        btn.setFixedWidth(110)
        layoutsafe.addStretch()
        self.dropdown.addLayout(layoutsafe)

        layoutright.addLayout(self.dropdown)
        self.app.set_layout_visible(self.dropdown,False)
        layoutright.addItem(self.app.vspace)


    def timeline_ui(self,layoutright):
        self.expanded2=False
        self.app.heading_label(layoutright,"Timeline / I-V-Curve",self.expand2)

        self.dropdown2=QVBoxLayout()

        layoutfresh=QHBoxLayout()
        freshwidget = QLineEdit()
        freshwidget.setStyleSheet("background-color: lightGray")
        freshwidget.setMaxLength(7)
        freshwidget.setFixedWidth(self.app.standard_width)
        freshwidget.setText(str(self.refresh_rate))
        freshwidget.textEdited.connect(self.refreshrate_edited)
        label = QLabel("refresh interval (s)")
        label.setStyleSheet("color:white")
        layoutfresh.addWidget(freshwidget)
        layoutfresh.addWidget(label)
        layoutfresh.addStretch()

        #self.btnlive=self.app.normal_button(layoutfresh,"Status Live",self.live_mode)

        self.dropdown2.addLayout(layoutfresh)

        layouttimeline=QHBoxLayout()
        btn=self.app.normal_button(layouttimeline,"Reset Timeline",self.measure_IV)
        btn.setFixedWidth(110)
        layouttimeline.addStretch()
        btn=self.app.normal_button(layouttimeline,"Save Timeline",self.measure_IV)
        btn.setFixedWidth(110)
        self.dropdown2.addLayout(layouttimeline)


        layoutIVor=QHBoxLayout()
        #label = QLabel("Show ")
        #label.setStyleSheet("color:white")

        #layoutIVor.addWidget(label)
        layoutIVor.addStretch()
        btn=self.app.normal_button(layoutIVor,"Timeline",self.measure_IV)
        btn.setFixedWidth(70)
        layoutIVor.addStretch()
        label = QLabel("<- Show -> ")
        label.setStyleSheet("color:white")
        layoutIVor.addWidget(label)
        layoutIVor.addStretch()
        btn=self.app.normal_button(layoutIVor,"I-V-Curve",self.measure_IV)
        btn.setFixedWidth(70)
        layoutIVor.addStretch()
        self.dropdown2.addLayout(layoutIVor)

        layoutIV=QHBoxLayout()
        self.acqivbtn=self.app.normal_button(layoutIV,"Acq. I-V-Curve",self.maximize)
        self.acqivbtn.setFixedWidth(110)
        layoutIV.addStretch()
        savbtn=self.app.normal_button(layoutIV,"Save I-V-Curve",self.maximize)
        savbtn.setFixedWidth(110)
        
        self.dropdown2.addLayout(layoutIV)

        layoutmax=QHBoxLayout()
        self.maxbtn=self.app.normal_button(layoutmax,"Maximize View",self.maximize)
        self.maxbtn.setFixedWidth(110)
        layoutmax.addStretch()
        self.dropdown2.addLayout(layoutmax)

        #layoutread=QHBoxLayout()
        #btn=self.app.normal_button(layoutread,"Measure",self.measure_electric)
        #layoutread.addStretch()

        #self.dropdown.addLayout(layoutread)

        layoutright.addLayout(self.dropdown2)
        self.app.set_layout_visible(self.dropdown2,False)
        layoutright.addItem(self.app.vspace)



    ## Handle view resizing 
    def updateViews(self):
        ## view has resized; update auxiliary views to match
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        
        ## need to re-update linked axes since this was called
        ## incorrectly while views had different shapes.
        ## (probably this should be handled in ViewBox.resizeEvent)
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)

    def power_graphics_show(self,layout):
        pw = pg.PlotWidget()
        pw.setTitle("Electric Power Timeline / I-V-Curve")
        pw.setBackground(None)
        self.p1 = pw.plotItem
        self.p1.setLabel('bottom', 'time', units='s')
        self.p1.setLabel('left', 'Voltage', units='V')
        ## create a new ViewBox, link the right axis to its coordinate system
        self.p2 = pg.ViewBox()
        self.p1.showAxis('right')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p1)
        self.p1.getAxis('right').setLabel('Current',units="mA", color="#0fef38")


        self.updateViews()
        self.p1.vb.sigResized.connect(self.updateViews)


        self.p1.plot([1,2,4,8,16,32])
        self.p2.addItem(pg.PlotCurveItem([10,20,40,80,40,20], pen="#0fef38"))

        layout.addWidget(pw,2)



    def power_on(self):
        if self.output_on:
            print("turning off")
            self.output_on=False
            self.psu.write("OUTP OFF")
            self.powerbtn.setStyleSheet("background-color: lightGray;color: black")
        else:
            print("turning on")
            self.output_on=True
            self.psu.write("OUTP ON")
            self.powerbtn.setStyleSheet("background-color: green;color: black")


    def maximize(self):
        if self.maximized:
            self.maximized=False
            self.app.stage.plot.setHidden(False)
            self.app.midright.setHidden(False)
            self.maxbtn.setText("Maximize View")
        else:
            self.maximized=True
            self.app.stage.plot.setHidden(True)
            self.app.midright.setHidden(True)
            self.maxbtn.setText("Minimize View")

    def live_mode(self):
        if not self.live_mode_running:
            self.live_mode_running=True
            self.timer.start(int(self.refresh_rate)*1000)
            #self.btnlive.setText("Status Live")
            #self.btnlive.setStyleSheet("background-color: green;color: black")
        else:

            self.live_mode_running=False
            self.timer.stop()
            #self.btnlive.setText("StatLive")
            #self.btnlive.setStyleSheet("background-color: lightGray;color: black")
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