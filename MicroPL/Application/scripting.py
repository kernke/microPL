from PyQt5.QtWidgets import QHBoxLayout,QFileDialog,QLabel,QComboBox,QApplication,QVBoxLayout,QApplication
from PyQt5.QtCore import QTimer,pyqtSignal,QRunnable,pyqtSlot,QObject
import numpy as np
import time
import threading

class Update_Signal(QObject):

    update = pyqtSignal(bool)   

class Grid_Mapping(QRunnable):

    def __init__(self, stage,keysight,orca,pixis,spatial_bool,spectral_bool,stagex,stagey):
        super().__init__()
        self.stage = stage
        self.orca=orca
        self.pixis=pixis
        self.keysight=keysight
        self.stagex=stagex
        self.stagey=stagey
        self.spectral_bool=spectral_bool
        self.spatial_bool=spatial_bool
        self.signals=Update_Signal()

    @pyqtSlot()
    def run(self): # A slot takes no params

        self.stage.xpos_set=self.stagex
        self.stage.ypos_set=self.stagey
        self.stage.stage_goto()      

        done_event = threading.Event()
        self.stage.thread_task(done_event)
        done_event.wait()
        if self.keysight.connected:
            if self.keysight.output_on:
                done_event = threading.Event()
                self.keysight.thread_task(done_event)
                done_event.wait()

        QApplication.processEvents()

        if self.spatial_bool:
            done_event = threading.Event()
            self.orca.acquire_clicked_spatial(done_event)
            done_event.wait()
            QApplication.processEvents()

        if self.spectral_bool:
            done_event = threading.Event()
            self.pixis.acquire_clicked_spectral(done_event)
            done_event.wait()
            QApplication.processEvents()

        self.signals.update.emit(True)
 

class IV_Measurement(QRunnable):

    def __init__(self, keysight,orca,pixis,spatial_bool,spectral_bool,set_volt,settling_time):
        super().__init__()
        self.orca=orca
        self.pixis=pixis
        self.keysight=keysight
        self.spectral_bool=spectral_bool
        self.spatial_bool=spatial_bool
        self.set_volt=set_volt
        self.settling_time=settling_time
        self.signals=Update_Signal()

    @pyqtSlot()
    def run(self): # A slot takes no params
        self.keysight.voltage=self.set_volt
        self.keysight.setvoltage_confirmed()
        time.sleep(self.settling_time)

        done_event = threading.Event()
        self.keysight.thread_task(done_event)
        done_event.wait()
        
        QApplication.processEvents()


        if self.spatial_bool:
            done_event = threading.Event()
            self.orca.acquire_clicked_spatial(done_event)
            done_event.wait()
            QApplication.processEvents()

        if self.spectral_bool:
            done_event = threading.Event()
            self.pixis.acquire_clicked_spectral(done_event)
            done_event.wait()
            QApplication.processEvents()

            
        self.signals.update.emit(True)


class Scripting:
    def __init__(self,app):
        self.app=app

        self.script_canceled=False
        self.script_selected=0
        self.script_index=None
        self.script_settings_prepared=False
        self.script_paused=False

        self.sleep_start=None
        self.sleep_duration=0

        # stage mapping
        self.script_x_entries=[0,50,10]
        self.script_y_entries=[0,50,10]

        self.grid_spatial=True
        self.grid_spectral=False


        self.IV_end_voltage=10
        self.IV_start_voltage=0
        self.IV_step_voltage=0.25
        self.IV_settling_time=0.05

        self.IV_spatial=True
        self.IV_spectral=True

        self.IV_curve_voltages=[0]
        self.IV_curve_currents=[0]
        self.IV_optical_spatial=[0]

    def grid_mapping_on_thread(self,step_done):
        if step_done:
            if self.script_canceled:
                self.script_end()
            self.script_index +=1
            if self.script_index==self.number_of_points:
                self.script_end()
            elif self.script_paused:
                self.app.add_log("script paused")
                return None
            else:
                self.app.add_log(str(self.script_index)+" from "+str(self.number_of_points))
                stagex=self.script_positions_x[self.script_index]
                stagey=self.script_positions_y[self.script_index]
                self.grid_mapper =Grid_Mapping(self.app.stage,self.app.keysight,self.app.orca,self.app.pixis,
                                            self.grid_spatial,self.grid_spectral,stagex,stagey) 
                self.grid_mapper.signals.update.connect(self.grid_mapping_on_thread)
                self.app.threadpool.start(self.grid_mapper)

    def expand(self):
        if not self.expanded:
            self.expanded=True
            self.app.set_layout_visible(self.dropdown,True)
        else:
            self.expanded=False
            self.app.set_layout_visible(self.dropdown,False)

    def script_ui(self,layoutright):
        self.expanded=False
        self.app.heading_label(layoutright,"Scripts   ",self.expand)

        self.dropdown=QVBoxLayout()

        #self.labelscr = QLabel("")
        #self.labelscr.setStyleSheet("color:white")
        #self.labelscr.setFixedWidth(100)
        
        widget = QComboBox()
        widget.addItems(["choose script","from settings txt","grid mapping","I-V-curve","calibrate spatial camera via stage (not implemented)"])
        widget.setStyleSheet("background-color: lightGray")
        widget.setFixedHeight(25)
        widget.currentIndexChanged.connect(self.script_changed )        
        self.dropdown.addWidget(widget)

        layoutscriptbuttons=QHBoxLayout()

        self.btnexec = self.app.normal_button(layoutscriptbuttons,"Set",self.script_button_set)

        layoutscriptbuttons.addStretch()
        self.btnstart = self.app.normal_button(layoutscriptbuttons,"Start",self.script_button_start)


        layoutscriptbuttons.addStretch()

        
        self.btnpause = self.app.normal_button(layoutscriptbuttons,"Pause",self.script_button_pause)
        
        self.dropdown.addLayout(layoutscriptbuttons)
        layoutright.addLayout(self.dropdown)
        self.app.set_layout_visible(self.dropdown,False)
        layoutright.addItem(self.app.vspace)

    def script_changed(self,i):
        self.script_selected=i
        self.script_settings_prepared=False
        if i>0:
            self.btnexec.setStyleSheet("background-color:cyan;")
            self.btnstart.setStyleSheet("background-color:lightgrey;")
        else:
            self.btnexec.setStyleSheet("background-color:lightgrey;")
            self.btnstart.setStyleSheet("background-color:lightgrey;")

    def script_button_pause(self):
        if not self.script_paused:
            self.btnpause.setText("Continue")
            #self.script_execution=False
            self.script_paused=True
        else:
            self.btnpause.setText("Pause")
            self.script_paused=False
            #self.script_execution=True
            if self.script_selected==1:
                self.script_from_txt()
            elif self.script_selected==2:
                self.grid_mapping_script()
            elif self.script_selected==2:
                self.grid_mapping_script()

    def script_end(self):
        self.script_index=None
        if self.app.pixis.connected:
            self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", self.app.pixis.remember_shutter)
            if self.app.pixis.remember_shutter == "Always Open":
                self.app.pixis.shutterbtn.setText("Shutter (Open)")
            elif self.app.pixis.remember_shutter == "Always Closed":
                self.app.pixis.shutterbtn.setText("Shutter (Closed)")
            elif self.app.pixis.remember_shutter == "Normal":
                self.app.pixis.shutterbtn.setText("Shutter (Normal)")

        if self.script_selected==3: # turn off after IV curve
            self.app.keysight.current=0       
            self.app.keysight.voltage=0
            self.app.keysight.currentwidget.setText(str(self.app.keysight.current))
            self.app.keysight.voltwidget.setText(str(self.app.keysight.voltage))
            if self.app.keysight.output_on:
                self.app.keysight.power_on() # turn off

        self.app.h5saving.save_on_acquire()

        if self.app.stage.connected:
            self.app.stage.live_mode()#_running=True
        if self.app.keysight.connected:
            self.app.keysight.live_mode()

        self.app.add_log("script ended")
        self.btnstart.setText("Start")
    
    def script_button_set(self):
        if self.script_selected==0:
            self.app.add_log("no script selected for setting parameters")            
        elif self.script_selected==1:
            self.script_from_txt_window()
        elif self.script_selected==2:
            self.grid_mapping_window()
        elif self.script_selected==3:
            self.acquire_IV_window()
        elif self.script_selected==4:
            pass

    def script_button_start(self):
        self.btnstart.setStyleSheet("background-color:lightgrey;")
        if self.script_paused:
            self.script_canceled=True
        else:
            if self.script_selected==0:
                self.app.add_log("no script selected to execute")
                return None
            if not self.script_settings_prepared:
                self.app.add_log("use 'Set' to initialize the script first")
                return None

            #self.script_execution=True
            self.btnstart.setText("Cancel")
            self.script_index=0

            if self.app.pixis.live_mode_running:
                self.app.pixis.live_mode()
            if self.app.orca.live_mode_running:
                self.app.orca.live_mode()
            if self.app.keysight.live_mode_running:
                self.app.keysight.live_mode()
            if self.app.stage.live_mode_running:
                self.app.stage.live_mode()

            self.app.threadpool.waitForDone()

            if not self.app.h5saving.save_on_acquire_bool:
                self.app.h5saving.save_on_acquire()

            if self.script_selected==1:
                #if self.grid_spectral:
                self.app.pixis.shutterbtn.setText("Shutter (Open)")
                self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", 'Always Open')
                self.script_from_txt()
        
            elif self.script_selected==2:
                if self.grid_spectral:
                    self.app.pixis.shutterbtn.setText("Shutter (Open)")
                    self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", 'Always Open')
                self.grid_mapping_script()
            elif self.script_selected==3:
                if self.IV_spectral:
                    self.app.pixis.shutterbtn.setText("Shutter (Open)")
                    self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", 'Always Open')
                self.acquire_IV()
            elif self.script_selected==4:
                pass

    def sleep_method(self,time_seconds):
        self.sleep_timer=QTimer()
        self.sleep_timer.timeout.connect(self.end_sleep)
        timer_time=int(time_seconds*1000)
        self.sleep_timer.start(timer_time)

    def end_sleep(self):
        self.sleep_timer.stop()

    def check_script(self,fname):
        settings_list=[]
        double_format_keys=["spatial_acquisition_time_s",
                            "spectral_acquisition_time_s",
                            "center_wavelength_nm",
                            "stage_x_mm",
                            "stage_y_mm",
                            "sleep_s,"
                            "voltage_V",
                            "current_A"]
        int_format_keys=["grating_position_int","spatial_binning_int",]
        bool_format_keys=["save_spectral_image_bool","spatial_auto_exposure"]

        comment_required=["sleep_s"]
        spectral_required=["spectral_acquisition_time_seconds",
                           "center_wavelength_nm",
                           "grating_position_int",
                           "save_spectral_image_bool",
                           "stage_x_mm",
                           "stage_y_mm"]
        spatial_required=["spatial_acquisition_time_s",
                          "stage_x_mm",
                          "stage_y_mm"]
        
        with open(fname, "r") as f:
            lines=f.read().splitlines()
        for line in lines:
            settings=dict()
            expressions=line.split(",")
            for expr in expressions:
                try:
                    key,value=expr.split(":")
                except ValueError:
                    print("ERROR missing ':'")
                    return None
                if key in double_format_keys:
                    settings[key]=np.double(value)
                elif key in int_format_keys:
                    settings[key]=int(value)
                elif key in bool_format_keys:
                    settings[key]=bool(value)
                else:
                    settings[key]=value
            if "mode" not in settings:
                print("mode is necessary in every line")
                return None
            check=True
            if settings["mode"]=="comment":
                for requirement in comment_required:
                    if requirement not in settings:
                        check=False
                        print("sleep false")
            elif settings["mode"]=="spectral":
                for requirement in spectral_required:
                    if requirement not in settings:
                        check=False
                        print("spectral false")
            elif settings["mode"]=="spatial":
                for requirement in spatial_required:
                    if requirement not in settings:
                        check=False
                        print("spatial false")
            if not check:
                print("settings requirements not fulfilled")
                return None
            
            settings_list.append(settings)
        return settings_list

    def script_from_txt_window(self):
        self.fname,ftype = QFileDialog.getOpenFileName(self.app, 'Open file', 
               self.app.h5saving.save_folder,"settings list (*.txt)")
        #print(fname)

    def script_from_txt(self):
        if self.fname:
            settings_list=self.check_script(self.fname)
            if settings_list is None:
                print("script includes errors")
            else:

                #self.script_execution=True
                if self.script_index is None:
                    self.script_index=0
                self.btnexec.setText("Cancel")
                    
                if not self.app.h5saving.save_on_acquire_bool:
                    self.app.h5saving.save_on_acquire()
                
                
                number_of_points=len(settings_list)        
                for i in range(self.script_index,number_of_points):
                    settings=settings_list[i]
                    if "comment_text" in settings:
                        self.app.h5saving.widgetcomment.setText(settings["comment_text"])
                        self.app.h5saving.comment_edited(settings["comment_text"])
                    if "heading_text" in settings:
                        self.app.h5saving.group=settings["heading_text"]
                        self.app.h5saving.widgeth5group.setText(self.app.h5saving.group)
                    if settings["mode"]=="comment":
                        sleep_time=settings["sleep_seconds"]*1000
                        self.sleep_method(sleep_time)
                    elif settings["mode"]=="spectral":
                        self.app.pixis.acqtime_spectral=settings["spectral_acquisition_time_s"]
                        self.app.monochromator.wavelength=settings["center_wavelength_nm"]
                        self.app.monochromator.wavelength_edited() ###################################################
                        self.app.pixis.save_full_image=settings["save_spectral_image_bool"]
                        self.app.pixis.checkbox.setChecked(self.app.pixis.save_full_image)
                        self.app.monochromatorgrating_changed(settings["grating_position_int"]-1)
                        self.app.stage.xpos=settings["stage_x_mm"]
                        self.app.stage.ypos=settings["stage_y_mm"]
                        self.app.stage.stage_goto()

                        QApplication.processEvents()
                        if not self.script_execution:
                            return None            
                        
                        self.app.pixis.acquire_clicked_spectral()


                    elif settings["mode"]=="spatial":
                        self.app.pixis.acqtime_spectral=settings["spatial_acquisition_time_seconds"]
                        self.app.stage.xpos=settings["stage_x_mm"]
                        self.app.stage.ypos=settings["stage_y_mm"]
                        self.app.stage.stage_goto()

                        QApplication.processEvents()
                        if not self.script_execution:
                            return None            

                        self.app.orca.acquire_clicked_spatial()

                    
                    self.script_index+=1
                    print(str(i+1)+" from "+str(number_of_points))
                    self.labelscr.setText(str(i+1)+"/"+str(number_of_points))
                    
                    QApplication.processEvents()
                    if not self.script_execution:
                        return None
                    
                self.script_end()

    def grid_mapping_window(self):
        #if self.script_index is None:
        text="Measurement grid with current settings\nChoose the grid via start position (min), "
        text+="end position (max)\nand number of points (num) in each dimension. "
        text+="(Note: If 'Spectral image' is selected, the shutter is set to always open.)"
        labellist=["X min","Y min","X max","Y max","X num","Y num"]
        defaultlist=[self.script_x_entries[0],self.script_y_entries[0],self.script_x_entries[1],
                        self.script_y_entries[1],self.script_x_entries[2],self.script_y_entries[2]]
        self.w = self.app.entrymaskmapping(self.app,defaultlist,labellist,text)
        self.w.location_on_the_screen()
        self.w.show()

    def grid_mapping_script(self):
        self.app.add_log("grid mapping script starting")

        self.number_of_points=len(self.script_positions_x)
        self.app.add_log(str(self.script_index)+" from "+str(self.number_of_points))
        stagex=self.script_positions_x[self.script_index]
        stagey=self.script_positions_y[self.script_index]
        self.grid_mapper =Grid_Mapping(self.app.stage,self.app.keysight,self.app.orca,self.app.pixis,
                                       self.grid_spatial,self.grid_spectral,stagex,stagey) 
        self.grid_mapper.signals.update.connect(self.grid_mapping_on_thread)
        self.app.threadpool.start(self.grid_mapper)

    def acquire_IV_window(self):
        heading_string="Acquire I-V-Curve by stepwise increasing the voltage from 0 to the set maximum value"
        heading_string+=" and measuring the corresponding current after a given settling time. "
        heading_string+="(Note: If 'Spectral image' is selected, the shutter is set to always open.)"
        defaultlist=[self.IV_start_voltage,self.IV_end_voltage,self.IV_step_voltage,self.IV_settling_time]
        labellist=["Voltage-Start (V)","Voltage-End (V)","Voltage-Step (V)","Settling Time (s)"]
        self.window = self.app.entrymaskiv(self.app,defaultlist,labellist,heading_string)
        self.window.location_on_the_screen()
        self.window.show()

    def iv_curve_on_thread(self,step_done):
        if step_done:
            if self.script_canceled:
                self.script_end()
            self.script_index +=1
            if self.script_index==self.number_of_points:
                self.script_end()
            elif self.script_paused:
                self.app.add_log("script paused")
                return None
            else:
                self.app.add_log(str(self.script_index)+" from "+str(self.number_of_points))

                self.IV_curve_currents.append(self.app.keysight.currentA_actual)        
                self.IV_curve_voltages.append(self.app.keysight.voltage_actual)
                self.app.keysight.IVcurveplot.setData(self.IV_curve_voltages,self.IV_curve_currents)

                set_volt=self.IV_set_voltages[self.script_index]
                self.iv_worker=IV_Measurement(self.app.keysight,self.app.orca,self.app.pixis,
                                              self.IV_spatial,self.IV_spectral,set_volt,self.IV_settling_time)
                self.iv_worker.signals.update.connect(self.iv_curve_on_thread)
                self.app.threadpool.start(self.iv_worker)

    def acquire_IV(self):

        self.app.add_log("(wait) Acquiring I-V-Curve")

        self.app.keysight.show_IV()

        self.IV_curve_voltages=[]
        self.IV_curve_currents=[]
        if self.app.orca.connected:
            self.IV_optical_spatial=[]
        
        if self.app.keysight.output_on:
            self.app.keysight.power_on() #turn off any output
        time.sleep(0.1) # give atleast 100ms between switching off and on
        self.app.keysight.current=self.app.keysight.max_currentmA -0.01       
        self.app.keysight.voltage=0
        self.app.keysight.currentwidget.setText(str(self.app.keysight.current))
        self.app.keysight.voltwidget.setText(str(self.app.keysight.voltage))
        self.app.keysight.power_on() #turn on


        self.number_of_points=int((self.IV_end_voltage-self.IV_start_voltage)/self.IV_step_voltage)   

        self.IV_set_voltages=[]
        for i in range(self.number_of_points):
            self.IV_set_voltages.append(self.IV_start_voltage+i*self.IV_step_voltage)

        set_volt=self.IV_set_voltages[self.script_index]
        self.iv_worker=IV_Measurement(self.app.keysight,self.app.orca,self.app.pixis,
                                      self.IV_spatial,self.IV_spectral,set_volt,self.IV_settling_time)
        self.iv_worker.signals.update.connect(self.iv_curve_on_thread)
        self.app.threadpool.start(self.iv_worker)