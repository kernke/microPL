import pyvisa
import datetime
import numpy as np
import time
import pyqtgraph as pg
from PyQt5.QtWidgets import QHBoxLayout,  QLineEdit,QLabel,QVBoxLayout,QApplication
from PyQt5.QtCore import pyqtSignal, QTimer,QRunnable,pyqtSlot,QObject

class Update_Signal(QObject):

    string_update = pyqtSignal(object)   
    update = pyqtSignal()

class PSU_voltage(QRunnable):
    def __init__(self, psu,voltage,event=None):
        super().__init__()
        self.psu = psu
        self.voltage=voltage
        self.signals=Update_Signal()
        self.event=event

    @pyqtSlot()
    def run(self): # A slot takes no params
        self.psu.write(f"SOUR:VOLT {self.voltage}")
        self.signals.update.emit()
        if self.event:
            self.event.set()

class PSU_current(QRunnable):
    def __init__(self, psu,current,event=None):
        super().__init__()
        self.psu = psu
        self.current=current
        self.signals=Update_Signal()
        self.event=event

    @pyqtSlot()
    def run(self): # A slot takes no params
        self.psu.write(f"SOUR:CURR {self.current/1000}")
        self.signals.update.emit()
        if self.event:
            self.event.set()

class PSU_power(QRunnable):
    def __init__(self, psu,on_bool,voltage,current,event=None):
        super().__init__()
        self.psu = psu
        self.on_bool=on_bool
        self.voltage=voltage
        self.current=current
        self.signals=Update_Signal()
        self.event=event

    @pyqtSlot()
    def run(self): # A slot takes no params
        if self.on_bool:
            self.psu.write(f"SOUR:VOLT {self.voltage}")
            self.psu.write(f"SOUR:CURR {self.current/1000}")
            self.psu.write("OUTP ON")
        else:
            self.psu.write("OUTP OFF")
        self.signals.update.emit()
        if self.event:
            self.event.set()

class Status_update(QRunnable):

    def __init__(self, psu,event=None):
        super().__init__()
        self.psu = psu
        self.signals=Update_Signal()
        self.event=event

    @pyqtSlot()
    def run(self): # A slot takes no params
        voltage_actual= float(self.psu.query("MEAS:VOLT?").strip())
        statusstring="Voltage: "+str(np.round(voltage_actual,3))+" V\n"
        currentA_actual=float(self.psu.query("MEAS:CURR?").strip())
        statusstring+="Current: "+str(np.round(currentA_actual*1000,2))+" mA"

        self.signals.string_update.emit((statusstring,voltage_actual,currentA_actual))
        if self.event:
            self.event.set()

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

        self.refresh_rate=0.55
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

        self.latency_time=0.3
        self.communication_running=False

    def disconnect(self):
        if self.live_mode_running:
            self.live_mode_running=False
            self.psleep_worker=self.app.sleep_worker_class(self.latency_time)
            self.psleep_worker.signals.update_empty.connect(self.disconnect)
            self.app.threadpool.start(self.psleep_worker)
            self.app.add_log("wait shortly for keysight to finish")
            print("wait shortly for keysight to finish")
            return None


        if self.communication_running:
            self.psleep_worker=self.app.sleep_worker_class(self.latency_time)
            self.psleep_worker.signals.update_empty.connect(self.disconnect)
            self.app.threadpool.start(self.psleep_worker)
            self.app.add_log("wait shortly for keysight to finish")
            print("wait shortly for keysight to finish")
            return None
        else:

            self.psu.write("OUTP OFF")

        #self.app.threadpool.waitForDone()
        self.psu.close() 
        print("Keysight disconnected")

    def live_mode(self):
        if not self.live_mode_running:
            self.live_mode_running=True
            self.btnlive.setStyleSheet("background-color: green;color: black")
            self.thread_task()
        else:

            self.live_mode_running=False
            self.btnlive.setStyleSheet("background-color: lightGray;color: black")

    def thread_task(self):#,event):#=False,event=None):
        if self.communication_running:
            self.sleep_worker=self.app.sleep_worker_class(self.latency_time)
            self.sleep_worker.signals.update_empty.connect(self.thread_task)
            self.app.threadpool.start(self.sleep_worker)
        else:  
            self.communication_running=True
            self.worker=Status_update(self.psu)
            self.worker.signals.string_update.connect(self.status_update_from_thread)
            self.app.threadpool.start(self.worker)

    def thread_task_script(self,event):
        while self.communication_running:
            time.sleep(0.1)
            QApplication.processEvents()
            
        self.communication_running=True
        self.worker=Status_update(self.psu,event)
        self.worker.signals.string_update.connect(self.status_update_from_thread)
        self.app.threadpool.start(self.worker)

    def thread_set_current_script(self,event):
        while self.communication_running:
            time.sleep(0.1)
            QApplication.processEvents()

        if not self.current>self.max_currentmA and not self.voltage*self.current>self.max_powermW:
            self.communication_running=True
            self.cworker=PSU_current(self.psu,self.current,event)
            self.cworker.signals.update.connect(self.thread_done_empty)
            self.app.threadpool.start(self.cworker)
        else:
            self.app.add_log("Current not changed")
            self.app.add_log("Safety limits violated")


    def thread_set_voltage_script(self,event):
        while self.communication_running:
            time.sleep(0.1)
            QApplication.processEvents()
        if not self.voltage>self.max_voltage and not self.voltage*self.current>self.max_powermW:
            self.communication_running=True
            self.vworker=PSU_voltage(self.psu,self.voltage,event)
            self.vworker.signals.update.connect(self.thread_done_empty)
            self.app.threadpool.start(self.vworker)
        else:
            self.app.add_log("Voltage not changed")
            self.app.add_log("Safety limits violated")


    def thread_power_script(self,event):
        while self.communication_running:
            time.sleep(0.1)
            QApplication.processEvents()
        cond1=self.voltage>self.max_voltage
        cond2=self.current>self.max_currentmA
        cond3=self.voltage*self.current>self.max_powermW
        if not cond1 and not cond2 and not cond3:
            self.communication_running=True
            self.pworker=PSU_power(self.psu,self.output_on,self.voltage,self.current,event)
            self.pworker.signals.update.connect(self.thread_done_empty)
            self.app.threadpool.start(self.pworker)
        else:
            self.app.add_log("Electric Power not turned ON")
            self.app.add_log("Safety limits violated")


    def thread_done_empty(self):
        self.communication_running=False


    def thread_set_voltage(self):
        if self.communication_running:
            self.vsleep_worker=self.app.sleep_worker_class(self.latency_time)
            self.vsleep_worker.signals.update_empty.connect(self.thread_set_voltage)
            self.app.threadpool.start(self.vsleep_worker)            
        else:
            self.communication_running=True
            self.vworker=PSU_voltage(self.psu,self.voltage)
            self.vworker.signals.update.connect(self.thread_done_empty)
            self.app.threadpool.start(self.vworker)


    def thread_set_current(self):
        if self.communication_running:
            self.csleep_worker=self.app.sleep_worker_class(self.latency_time)
            self.csleep_worker.signals.update_empty.connect(self.thread_set_current)
            self.app.threadpool.start(self.csleep_worker)            
        else:
            self.communication_running=True
            self.cworker=PSU_current(self.psu,self.current)
            self.cworker.signals.update.connect(self.thread_done_empty)
            self.app.threadpool.start(self.cworker)

    

    def thread_power_on_off(self):
        if self.communication_running:
            self.psleep_worker=self.app.sleep_worker_class(self.latency_time)
            self.psleep_worker.signals.update_empty.connect(self.thread_power_on_off)
            self.app.threadpool.start(self.psleep_worker)
        else:                         
            self.communication_running=True
            self.pworker=PSU_power(self.psu,self.output_on,self.voltage,self.current)
            self.pworker.signals.update.connect(self.thread_done_empty)
            self.app.threadpool.start(self.pworker)


    def thread_sleep(self):
        self.sleep_worker=self.app.sleep_worker_class(self.refresh_rate)
        self.sleep_worker.signals.update_empty.connect(self.thread_task)
        self.app.threadpool.start(self.sleep_worker)        


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
            
        else:
            self.voltage_list.append(self.voltage_actual)
            self.currentA_list.append(self.currentA_actual)
            self.timeline_time = time.time()-self.timeline_start
            self.timeline_list.append(self.timeline_time)
            
        if self.output_on:
            stsh=self.voltwidget.styleSheet()
            if np.isclose(self.voltage,self.voltage_actual,rtol=0.01,atol=0.01):
                if "red" in stsh:
                    self.voltwidget.setStyleSheet("color:red;background-color: cyan;")
                else:
                    self.voltwidget.setStyleSheet("color:black;background-color: cyan;")
            else:
                if "red" in stsh:
                    self.voltwidget.setStyleSheet("color:red;background-color: lightGray;")
                else:
                    self.voltwidget.setStyleSheet("color:black;background-color: lightGray;")
                #self.voltwidget.setStyleSheet("background-color: lightGray;")

            stsh=self.currentwidget.styleSheet()
            if np.isclose(self.current/1000,self.currentA_actual,rtol=0.01,atol=0.001):
                if "red" in stsh:
                    self.currentwidget.setStyleSheet("color:red;background-color: cyan;")
                else:
                    self.currentwidget.setStyleSheet("color:black;background-color: cyan;")
            else:
                if "red" in stsh:
                    self.currentwidget.setStyleSheet("color:red;background-color: lightGray;")
                else:
                    self.currentwidget.setStyleSheet("color:black;background-color: lightGray;")
        self.app.metadata_timeline["unsaved"]=True
        self.Acurve.setData(self.timeline_list,self.currentA_list)
        self.Vcurve.setData(self.timeline_list,self.voltage_list)
        self.p1.setXRange(0,self.timeline_time)
        self.communication_running=False
        if self.live_mode_running:
            self.thread_sleep()

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
                if self.output_on:
                    stsh=self.voltwidget.styleSheet()
                    if "cyan" in stsh:
                        self.voltwidget.setStyleSheet("color:red;background-color: cyan;")
                    else:
                        self.voltwidget.setStyleSheet("color:red;background-color: lightGray;")

                    #self.voltwidget.setStyleSheet("color: red;")#background-color: lightGray

    def setvoltage_confirmed(self):
        if not self.voltage>self.max_voltage and not self.voltage*self.current>self.max_powermW:
            self.thread_set_voltage()
            self.voltwidget.setStyleSheet("color: black;background-color: lightGray;")
            self.app.add_log("set: "+str(np.round(self.voltage,3))+" V")
        else:
            self.app.add_log("Safety limits violated")

    def setcurrent_confirmed(self):
        if not self.current>self.max_currentmA and not self.voltage*self.current>self.max_powermW:
            self.thread_set_current()
            self.currentwidget.setStyleSheet("color: black;background-color: lightGray;")
            self.app.add_log("set: "+str(np.round(self.current,1))+" mA")
        else:
            self.app.add_log("Safety limits violated")

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
                    stsh=self.currentwidget.styleSheet()
                    if "cyan" in stsh:
                        self.currentwidget.setStyleSheet("color:red;background-color: cyan;")
                    else:
                        self.currentwidget.setStyleSheet("color:red;background-color: lightGray;")
                    #self.currentwidget.setStyleSheet("color: red;")

    def power_on(self):
        if self.output_on:
            self.output_on=False
            self.thread_power_on_off()
            self.powerbtn.setStyleSheet("background-color: lightGray;color: black")
            self.voltwidget.setStyleSheet("background-color: lightGray")
            self.currentwidget.setStyleSheet("background-color: lightGray")
            self.app.add_log("Electric Power Output OFF")
        else:
            cond0=self.voltage>self.max_voltage
            cond1=self.voltage*self.current>self.max_powermW
            cond2=self.current>self.max_currentmA
            if not cond0 and not cond1 and not cond2:
                self.output_on=True
                self.thread_power_on_off()

                self.powerbtn.setStyleSheet("background-color: green;color: black")
                self.app.add_log("set: "+str(np.round(self.voltage,3))+" V ; "+str(np.round(self.current,1))+" mA")
                self.app.add_log("Electric Power Output ON")
            else:
                self.app.add_log("Electric Power not turned ON")
                self.app.add_log("Safety limits violated")

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
                    

    def power_ui(self,layoutright):

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
        text="Set safety limits to the output of the electric power supply"
        defaultlist=[self.max_voltage,self.max_currentmA,self.max_powermW]
        labellist=["Voltage (V)","Current (mA)","Power (mW)"]
        self.window = self.app.entrymask3(self.app,"safety",defaultlist,labellist,text)
        self.window.location_on_the_screen()
        self.window.show()

    def timeline_ui(self,layoutright):
        self.expanded2=False
        self.app.heading_label(layoutright,"Timeline / I-V-Curve",self.expand2)

        self.dropdown2=QVBoxLayout()

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
        btn=self.app.normal_button(layouttimeline,"Save Timeline",self.app.h5saving.save_to_h5_timeline)
        btn.setFixedWidth(110)
        self.dropdown2.addLayout(layouttimeline)


        layoutmax=QHBoxLayout()
        self.maxbtn=self.app.normal_button(layoutmax,"Maximize View",self.maximize)
        self.maxbtn.setFixedWidth(110)
        layoutmax.addStretch()

        self.dropdown2.addLayout(layoutmax)

        layoutright.addLayout(self.dropdown2)
        self.app.set_layout_visible(self.dropdown2,False)
        layoutright.addItem(self.app.vspace)

        self.live_mode_running=False
        if self.connected:
            self.live_mode()
                
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
        self.IVcurveplot=pg.PlotCurveItem(self.app.scripting.IV_curve_voltages,self.app.scripting.IV_curve_currents)
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
