import pyvisa
import datetime
import numpy as np
import time
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
            # for safety
            self.psu.write("OUTP OFF")
        except:
            self.connected=False
            print("dummy mode for keysight")
            self.app.add_log("Keysight dummy mode")


        self.voltage=0
        self.current=0
        self.output_on=False
        self.max_voltage=20
        self.max_currentmA=500
        self.max_powermW=5000

        self.refresh_rate=1.
        self.voltage_actual=0
        self.currentA_actual=0

        self.voltage_list=[]
        self.currentA_list=[]
        self.timeline_list=[]
        self.timeline_time=0
        self.timeline_start=time.time()
        self.timeline_start_date=datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")
        self.timeline_reset_pressed=False
        self.maximized=False

        self.IV_settings_prepared=False
        self.IV_end_voltage=10
        self.IV_start_voltage=0
        self.IV_step_voltage=0.25
        self.IV_settling_time=0.2

        self.IV_curve_voltages=[0]
        self.IV_curve_currents=[0]

    def disconnect(self):
        if self.live_mode_running:
            self.live_mode_running=False
            self.timer.stop()
        self.psu.write("OUTP OFF")
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
        if self.timeline_reset_pressed:
            self.timeline_reset_pressed=False
            self.voltage_list=[self.voltage_actual]
            self.currentA_list=[self.currentA_actual]
            self.timeline_time=0
            self.timeline_list=[self.timeline_time]
            self.timeline_start=time.time()
            self.timeline_start_date=datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")
            
            #self.timeline_time = time.time()-self.timeline_start#self.refresh_rate

        else:
            self.voltage_list.append(self.voltage_actual)
            self.currentA_list.append(self.currentA_actual)
            self.timeline_time = time.time()-self.timeline_start
            self.timeline_list.append(self.timeline_time)
            #self.refresh_rate
        self.Acurve.setData(self.timeline_list,self.currentA_list)
        self.Vcurve.setData(self.timeline_list,self.voltage_list)
        self.p1.setXRange(0,self.timeline_time)


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
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                self.voltage=np.double(s)
                self.voltwidget.setStyleSheet("background-color: lightGray;color: red")


    def setvoltage_confirmed(self):
        if self.voltage<self.max_voltage and self.voltage*self.current<self.max_powermW:
            if self.live_mode_running:
                self.timer.stop()
                self.psu.write(f"SOUR:VOLT {self.voltage}")
                self.timer.start(int(self.refresh_rate*1000))
            else:
                self.psu.write(f"SOUR:VOLT {self.voltage}")
            self.voltwidget.setStyleSheet("background-color: lightGray;color: black")
            self.app.add_log("set: "+str(np.round(self.voltage,3))+" V")


    def setcurrent_confirmed(self):
        if self.current<self.max_currentmA and self.voltage*self.current<self.max_powermW:
            if self.live_mode_running:
                self.timer.stop()
                self.psu.write(f"SOUR:CURR {self.current/1000}")
                self.timer.start(int(self.refresh_rate*1000))
            else:
                self.psu.write(f"SOUR:CURR {self.current/1000}")
            self.currentwidget.setStyleSheet("background-color: lightGray;color: black")
            self.app.add_log("set: "+str(np.round(self.current,1))+" mA")


    def setcurrent_edited(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                self.current=np.double(s)
                if self.output_on:
                    self.currentwidget.setStyleSheet("background-color: lightGray;color: red")


    def power_on(self):
        if self.output_on:
            self.output_on=False
            if self.live_mode_running:
                self.timer.stop()
                self.psu.write("OUTP OFF")
                self.timer.start(int(self.refresh_rate*1000))
            else:
                self.psu.write("OUTP OFF")
            self.powerbtn.setStyleSheet("background-color: lightGray;color: black")
            self.app.add_log("Electric Power Output OFF")
        else:
            cond0=self.voltage<self.max_voltage
            cond1=self.voltage*self.current<self.max_powermW
            cond2=self.current<self.max_currentmA
            if cond0 and cond1 and cond2:
                self.output_on=True
                if self.live_mode_running:
                    self.timer.stop()
                    self.psu.write(f"SOUR:CURR {self.current/1000}")
                    self.psu.write(f"SOUR:VOLT {self.voltage}")
                    self.psu.write("OUTP ON")
                    self.timer.start(int(self.refresh_rate*1000))
                else:
                    self.psu.write(f"SOUR:CURR {self.current/1000}")
                    self.psu.write(f"SOUR:VOLT {self.voltage}")
                    self.psu.write("OUTP ON")

                self.powerbtn.setStyleSheet("background-color: green;color: black")
                self.app.add_log("set: "+str(np.round(self.voltage,3))+" V ; "+str(np.round(self.current,1))+" mA")
                self.app.add_log("Electric Power Output ON")
            else:
                self.app.add_log("Safety limits violated")
                self.app.add_log("Electric Power not turned ON")


    def refreshrate_edited(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                if np.double(s)<0.5:
                    self.refresh_rate=0.5
                else:
                    self.refresh_rate=np.double(s)
                    
                if self.live_mode_running:
                    self.timer.stop()
                    self.timer.start(int(1000*self.refresh_rate))



    def power_ui(self,layoutright):

        self.expanded=False
        self.app.heading_label(layoutright,"Electric Power Supply",self.expand)

        self.dropdown=QVBoxLayout()
        
        layoutoutput=QHBoxLayout()
        self.powerbtn=self.app.normal_button(layoutoutput,"Output",self.power_on)
        label = QLabel("grey   -> off\ngreen -> on")#         cyan -> limited by")
        label.setStyleSheet("color:white")
        label.setWordWrap(True)
        layoutoutput.addWidget(label)
        layoutoutput.addStretch()

        
        self.dropdown.addLayout(layoutoutput)
        layoutset=QHBoxLayout()
        self.voltwidget = QLineEdit()
        self.voltwidget.setStyleSheet("background-color: lightGray")
        self.voltwidget.setMaxLength(7)
        self.voltwidget.setFixedWidth(self.app.standard_width)
        self.voltwidget.setText(str(np.round(self.voltage_actual,3)))
        self.voltwidget.returnPressed.connect(self.setvoltage_confirmed)
        self.voltwidget.textEdited.connect(self.setvoltage_edited)
        label = QLabel("voltage (V)")
        label.setStyleSheet("color:white")
        layoutset.addWidget(self.voltwidget)
        layoutset.addWidget(label)
        layoutset.addStretch()
        self.currentwidget = QLineEdit()
        self.currentwidget.setStyleSheet("background-color: lightGray")
        self.currentwidget.setMaxLength(7)
        self.currentwidget.setFixedWidth(self.app.standard_width)
        self.currentwidget.setText(str(np.round(self.currentA_actual*1000,1)))
        self.currentwidget.textEdited.connect(self.setcurrent_edited)
        self.currentwidget.returnPressed.connect(self.setcurrent_confirmed)
        label = QLabel("current (mA)")
        label.setStyleSheet("color:white")
        layoutset.addWidget(label)
        layoutset.addWidget(self.currentwidget)
        
        self.dropdown.addLayout(layoutset)

        layoutinfo=QHBoxLayout()
        layoutinfo.addStretch()
        label = QLabel("(if Output is on, confirm changes with enter)")
        label.setStyleSheet("color:white")
        layoutinfo.addWidget(label)
        layoutinfo.addStretch()        
        self.dropdown.addLayout(layoutinfo)
        

        layoutsafe=QHBoxLayout()
        btn=self.app.normal_button(layoutsafe,"Safety limits",self.set_safety)
        btn.setFixedWidth(110)
        layoutsafe.addStretch()
        self.dropdown.addLayout(layoutsafe)

        layoutright.addLayout(self.dropdown)
        self.app.set_layout_visible(self.dropdown,False)
        layoutright.addItem(self.app.vspace)

    def set_safety(self):
        self.window = self.app.entrymask3(self.app,"safety")#device,roi
        self.window.setHeading("Set safety limits to the output of the electric power supply")
        self.window.setLabels(["Voltage (V)","Current (mA)","Power (mW)"])
        self.window.setDefaults([str(self.max_voltage),str(self.max_currentmA),str(self.max_powermW)])
        self.window.location_on_the_screen()
        self.window.show()


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

        self.btnlive=self.app.normal_button(layoutfresh,"Status Live",self.live_mode)

        self.dropdown2.addLayout(layoutfresh)

        layouttimeline=QHBoxLayout()
        btn=self.app.normal_button(layouttimeline,"Reset Timeline",self.reset_pressed)
        btn.setFixedWidth(110)
        layouttimeline.addStretch()
        btn=self.app.normal_button(layouttimeline,"Save Timeline",self.maximize) ################
        btn.setFixedWidth(110)
        self.dropdown2.addLayout(layouttimeline)


        layoutIVor=QHBoxLayout()

        layoutIVor.addStretch()
        self.btntimelineshow=self.app.normal_button(layoutIVor,"Timeline",self.show_timline)
        self.btntimelineshow.setFixedWidth(70)
        self.btntimelineshow.setStyleSheet("background-color: green")
        layoutIVor.addStretch()
        label = QLabel("<- Show -> ")
        label.setStyleSheet("color:white")
        layoutIVor.addWidget(label)
        layoutIVor.addStretch()
        self.btnIVshow=self.app.normal_button(layoutIVor,"I-V-Curve",self.show_IV)
        self.btnIVshow.setFixedWidth(70)
        layoutIVor.addStretch()
        self.dropdown2.addLayout(layoutIVor)

        layoutIV=QHBoxLayout()
        self.acqivbtn=self.app.normal_button(layoutIV,"Acq. I-V-Curve",self.acquire_IV)
        self.acqivbtn.setFixedWidth(110)
        layoutIV.addStretch()
        ivresetbtn=self.app.normal_button(layoutIV,"Reset I-V-settings",self.maximize) ###############
        ivresetbtn.setFixedWidth(120)
        
        self.dropdown2.addLayout(layoutIV)

        layoutmax=QHBoxLayout()
        self.maxbtn=self.app.normal_button(layoutmax,"Maximize View",self.maximize)
        self.maxbtn.setFixedWidth(110)
        layoutmax.addStretch()
        savbtn=self.app.normal_button(layoutmax,"Save I-V-Curve",self.maximize) ###############
        savbtn.setFixedWidth(110)

        self.dropdown2.addLayout(layoutmax)

        layoutright.addLayout(self.dropdown2)
        self.app.set_layout_visible(self.dropdown2,False)
        layoutright.addItem(self.app.vspace)

        self.timer=QTimer()
        self.timer.timeout.connect(self.thread_task)
        self.live_mode_running=False
        if self.connected:
            self.live_mode()

    def reset_iv_settings(self):
        self.acqivbtn.setStyleSheet("background-color:LightGray")
        self.IV_settings_prepared=False                   

    def acquire_IV(self):
        if not self.IV_settings_prepared:
            self.window = self.app.entrymask4b(self.app,"IVcurve")#device,roi
            heading_string="Acquire I-V-Curve by stepwise increasing the voltage from 0 to the set maximum value"
            heading_string+=" and measuring the corresponding current after a given settling time. "
            heading_string+="After pressing 'Confirm', which closes this window, press 'Acq. I-V-Curve' in the main window again "
            heading_string+="to start the measurement."
            self.window.setHeading(heading_string)
            self.window.setLabels(["Voltage-Start (V)","Voltage-End (V)","Voltage-Step (V)","Settling Time (s)"])
            defaultlist=[str(self.IV_start_voltage),str(self.IV_end_voltage),str(self.IV_step_voltage)]
            defaultlist.append(str(self.IV_settling_time))
            self.window.setDefaults(defaultlist)
            self.window.location_on_the_screen()
            self.window.show()
        else:
            self.app.add_log("(wait) Acquiring I-V-Curve")
            self.acqivbtn.setStyleSheet("background-color:LightGray")
            self.IV_settings_prepared=False
            
            self.show_IV()

            self.IV_curve_voltages=[]
            self.IV_curve_currents=[]
            if self.live_mode_running:
                self.timer.stop()
            if self.app.orca.live_mode_running:
                self.app.orca.timer.stop()
                self.app.orca.live_mode_running=False
            if self.app.pixis.live_mode_running:
                self.app.pixis.timer.stop()
                self.app.pixis.live_mode_running=False
            if self.app.stage.live_mode_running:
                self.app.stage.timer.stop()

            self.psu.write("OUTP OFF")
            self.psu.write(f"SOUR:CURR {self.max_currentmA/1000}")
            self.psu.write(f"SOUR:VOLT {0}")
            self.psu.write("OUTP ON")

            number_of_steps=int((self.IV_end_voltage-self.IV_start_voltage)/self.IV_step_voltage)
            for i in range(number_of_steps):
                IV_set_voltage=self.IV_start_voltage+i*self.IV_step_voltage
                self.psu.write(f"SOUR:VOLT {IV_set_voltage}")
                time.sleep(self.IV_settling_time)
                self.IV_curve_currents.append(float(self.psu.query("MEAS:CURR?").strip()))        
                self.IV_curve_voltages.append(float(self.psu.query("MEAS:VOLT?").strip()))
                self.IVcurveplot.setData(self.IV_curve_voltages,self.IV_curve_currents)
            
            self.psu.write(f"SOUR:CURR {0}")
            self.psu.write(f"SOUR:VOLT {0}")
            self.psu.write("OUTP OFF")
            
            self.voltwidget.setText("0")
            self.currentwidget.setText("0")

            self.app.add_log("(continue) I-V-Curve finished")
            if self.live_mode_running:
                self.timer.start(int(self.refresh_rate)*1000)
            if self.app.stage.live_mode_running:
                self.app.stage.timer.start(int(self.app.stage.refresh_rate)*1000)

                
    def reset_pressed(self):
        self.timeline_reset_pressed=True

    def show_IV(self):
        self.btntimelineshow.setStyleSheet("background-color: lightGray")
        self.btnIVshow.setStyleSheet("background-color: green")
        self.pw.setHidden(True)
        self.pw2.setHidden(False)

    def show_timline(self):
        self.btnIVshow.setStyleSheet("background-color: lightGray")
        self.btntimelineshow.setStyleSheet("background-color: green")

        self.pw.setHidden(False)
        self.pw2.setHidden(True)

        #self.p1.plot([1,2,4,8,16,32])

    ## Handle view resizing 
    def updateViews(self):
        ## view has resized; update auxiliary views to match
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        
        ## need to re-update linked axes since this was called
        ## incorrectly while views had different shapes.
        ## (probably this should be handled in ViewBox.resizeEvent)
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)

    def power_graphics_show(self,layout):
        self.pw2=pg.PlotWidget()
        self.pw2.setBackground(None)

        self.pw2.setTitle("I-V-Curve")
        self.pw2.setLabel('bottom', 'Voltage', units='V')
        self.pw2.setLabel('left', 'Current', units='A')
        #pw2vb = pg.ViewBox()
        #pw2p1 = self.pw.
        self.IVcurveplot=pg.PlotCurveItem(self.IV_curve_voltages,self.IV_curve_currents)
        self.pw2.addItem(self.IVcurveplot)#plot([1,2,4,8,16,32])
        layout.addWidget(self.pw2)
        self.pw2.setHidden(True)

        self.pw = pg.PlotWidget()
        self.pw.setTitle("Electric Power Timeline / I-V-Curve")
        self.pw.setBackground(None)
        self.p1 = self.pw.plotItem
        self.p1.setLabel('bottom', 'time', units='s')
        self.p1.setLabel('left', 'Voltage', units='V')
        ## create a new ViewBox, link the right axis to its coordinate system
        self.p2 = pg.ViewBox()
        self.p1.showAxis('right')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p1)
        self.p1.getAxis('right').setLabel('Current',units="A", color="#0fef38")
        self.p1.getAxis("right").enableAutoSIPrefix(True)

        self.updateViews()
        self.p1.vb.sigResized.connect(self.updateViews)


        #self.p1.plot([1,2,4,8,16,32])
        self.Vcurve=pg.PlotCurveItem([0],[0])#, pen="#0fef38")
        self.p1.addItem(self.Vcurve)
        self.Acurve=pg.PlotCurveItem([0],[0], pen="#0fef38")
        self.p2.addItem(self.Acurve)
        self.p1.setXRange(0,1)#self.timeline_time)
        layout.addWidget(self.pw,2)



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
            self.btnlive.setStyleSheet("background-color: green;color: black")
        else:

            self.live_mode_running=False
            self.timer.stop()
            #self.btnlive.setText("StatLive")
            self.btnlive.setStyleSheet("background-color: lightGray;color: black")
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