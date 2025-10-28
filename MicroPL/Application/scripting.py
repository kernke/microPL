from PyQt5.QtWidgets import QHBoxLayout,QFileDialog,QLabel,QComboBox,QApplication,QVBoxLayout,QApplication
from PyQt5.QtCore import QTimer,pyqtSignal,QRunnable,pyqtSlot,QObject
import numpy as np
import time
import pyqtgraph as pg
import threading

class Update_Signal(QObject):

    update = pyqtSignal(bool)   
    update_empty = pyqtSignal()
    #update_with_event=pyqtSignal(object)

class Sleep_Worker(QRunnable):
    def __init__(self,sleep_duration):#,event=None):
        super().__init__()
        self.sleep_duration=sleep_duration
        self.signals=Update_Signal()
        #self.event=event

    @pyqtSlot()
    def run(self):
        time.sleep(self.sleep_duration)
        #
        self.signals.update_empty.emit()
        #QApplication.processEvents()
        #if self.event:
        #    self.signals.update_with_event.emit(self.event)
        
        #QApplication.processEvents()

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
                self.keysight.thread_task_script(done_event)
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

    def __init__(self,keyword, keysight,orca,pixis,spatial_bool,spectral_bool,set_value,settling_time):
        super().__init__()
        self.keyword=keyword
        self.orca=orca
        self.pixis=pixis
        self.keysight=keysight
        self.spectral_bool=spectral_bool
        self.spatial_bool=spatial_bool
        self.set_value=set_value
        self.settling_time=settling_time
        self.signals=Update_Signal()

    @pyqtSlot()
    def run(self): # A slot takes no params
        if self.keyword == "set_voltages":
            self.keysight.voltage=self.set_value

            done_event = threading.Event()
            self.keysight.thread_set_voltage_script(done_event)
            done_event.wait()
        elif self.keyword == "set_currents":
            self.keysight.current=self.set_value

            done_event = threading.Event()
            self.keysight.thread_set_current_script(done_event)
            done_event.wait()


        time.sleep(self.settling_time)

        done_event = threading.Event()
        self.keysight.thread_task_script(done_event)
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
        #QApplication.processEvents()

class Master_Script(QRunnable):
    def __init__(self,app,command):
        super().__init__()
        self.app=app
        self.command=command
        self.signals=Update_Signal()

    @pyqtSlot()
    def run(self): # A slot takes no params    
        if self.command[0]=="spatial_acquisition_time_s":
            if self.app.pixis.auto_exposure_activated:
                self.app.pixis.auto_exposure_activated=False
                self.app.pixis.acqtime_spectral=self.command[1]
            self.app.pixis.cam.set_exposure(self.command[1])
            self.app.pixis.acqwidget.setText(str(self.command[1]))
        elif self.command[0]=="spectral_acquisition_time_s":
            if self.app.orca.auto_exposure_activated:
                self.app.orca.auto_exposure_activated=False
            self.app.orca.acqtime_spatial=self.command[1]
            self.app.orca.cam.set_exposure(self.command[1])
            self.app.orca.acqwidget.setText(str(self.command[1]))
        elif self.command[0]=="center_wavelength_nm":
            self.app.monochromator.wavelength=self.command[1]
            self.app.monochromator.wavelength_edited()
        elif self.command[0]=="stage_x_mm":
            self.app.stage.xpos_set=self.command[1]
            self.app.stage.stage_goto()      
            done_event = threading.Event()
            self.app.stage.thread_task(done_event)
            done_event.wait()
        elif self.command[0]=="stage_y_mm":
            self.app.stage.ypos_set=self.command[1]
            self.app.stage.stage_goto()      
            done_event = threading.Event()
            self.app.stage.thread_task(done_event)
            done_event.wait()            
        elif self.command[0]=="sleep_s":
            self.app.scripting.sleep_long_script(self.command[1])
        elif self.command[0]=="voltage_V":
            self.app.keysight.voltage=self.command[1]
            done_event = threading.Event()
            self.app.keysight.thread_set_voltage_script(done_event)
            done_event.wait()
            self.app.keysight.voltwidget.setText(str(self.command[1]))
            done_event = threading.Event()
            self.app.keysight.thread_task_script(done_event)
            done_event.wait()
        elif self.command[0]=="current_mA":
            self.app.keysight.current=self.command[1]
            done_event = threading.Event()
            self.app.keysight.thread_set_current_script(done_event)
            done_event.wait()
            self.app.keysight.currentwidget.setText(str(self.command[1]))
            done_event = threading.Event()
            self.app.keysight.thread_task_script(done_event)
            done_event.wait()

        elif self.command=="electric_measurement_to_timeline":
            done_event = threading.Event()
            self.app.keysight.thread_task_script(done_event)
            done_event.wait()

        elif self.command=="spatial_acquire":
            done_event = threading.Event()
            self.app.orca.acquire_clicked_spatial(done_event)
            done_event.wait()
            
        elif self.command=="spectral_acquire":
            done_event = threading.Event()
            self.app.pixis.acquire_clicked_spectral(done_event)
            done_event.wait()

        elif self.command=="spectral_auto_exposure_stop":
            self.app.pixis.auto_exposure_activated=False
            self.app.pixis.autobtn.setStyleSheet("background-color:lightGray")

        elif self.command=="spatial_auto_exposure_stop":
            self.app.orca.auto_exposure_activated=False
            self.app.orca.autobtn.setStyleSheet("background-color:lightGray")


        elif self.command[0]=="save_spectral_image_bool":
            self.app.pixis.save_full_image=self.command[1]
            self.app.pixis.checkbox.setChecked(self.command[1])

        elif self.command[0]=="electric_output_bool":
            self.app.keysight.output_on=self.command[1]
            done_event = threading.Event()
            self.app.keysight.thread_power_script(done_event)
            done_event.wait()
            done_event = threading.Event()
            self.app.keysight.thread_task_script(done_event)
            done_event.wait()


        elif self.command[0]=="comment":
            self.app.metadata_spatial["comment"]=self.command[1]
            self.app.metadata_spectral["comment"]=self.command[1]
            self.app.metadata_timeline["comment"]=self.command[1]
            self.app.h5saving.widgetcomment.setText(self.command[1])

        elif self.command[0]=="group_name":
            self.app.h5saving.group=self.command[1]
        elif self.command[0]=="acquistion_name":
            self.app.h5saving.acq_name=self.command[1]

        elif self.command[0]=="spectral_shutter_mode":
            if self.command[1]=="open":
                self.app.pixis.shutterbtn.setText("Shutter (Open)")
                self.app.pixis.shutter_value="Always Open"
                self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", 'Always Open')
            elif self.command[1]=="closed":
                self.app.pixis.shutterbtn.setText("Shutter (Closed)")
                self.app.pixis.shutter_value="Always Closed"
                self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", 'Always Closed')
            elif self.command[1]=="normal":
                self.app.pixis.shutterbtn.setText("Shutter (Normal)")
                self.app.pixis.shutter_value="Normal"
                self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", 'Normal')

        elif self.command[0]=="grating":
            done_event = threading.Event()
            self.app.monochromator.grating_change_script(int(self.command[1]),done_event)
            done_event.wait()
        elif self.command[0]=="filter":
            done_event = threading.Event()
            self.app.monochromator.filter_change_script(int(self.command[1]),done_event)
            done_event.wait()

        elif self.command[0]=="spatial_resolution":
            if self.command[1]=="2048":
                self.app.orca.binning=1  
                self.app.orca.resbtn.setText("Resolution (2048)")

            elif self.command[1]=="1024":
                self.app.orca.binning=2  
                self.app.orca.resbtn.setText("Resolution (1024)")

            elif self.command[1]=="512":
                self.app.orca.binning=4  
                self.app.orca.resbtn.setText("Resolution (512)")

        elif self.command=="save_timeline":
            self.app.h5saving.save_to_h5_timeline()

        elif self.command=="reset_timeline":
            self.app.keysight.reset_pressed()

        #elif self.command=="pause_timeline":
        #    self.app.keysight.live_mode()
        #    self.app.keysight.live_mode_running=False

        #elif self.command=="continue_timeline":
        #    self.app.keysight.live_mode()
        #    self.app.keysight.live_mode_running=True

        elif self.command[0]=="spectral_roi":
            params=self.command[1]
            self.app.pixis.roi.setPos(pg.Point([int(params["x_min_int"]),int(params["y_min_int"])]))
            deltax=int(params["x_max_int"])-int(params["x_min_int"])
            deltay=int(params["y_max_int"])-int(params["y_min_int"])
            self.app.pixis.roi.setSize([deltax,deltay])


        elif self.command[0]=="spectral_auto_exposure":
            params=self.command[1]
            self.app.pixis.auto_exposure_activated=True
            self.app.pixis.auto_expose_start=params["start_s"]
            self.app.pixis.auto_expose_min=params["min_s"]
            self.app.pixis.auto_expose_max=params["max_s"]
            self.app.pixis.autobtn.setStyleSheet("background-color:green")

        elif self.command[0]=="spatial_auto_exposure":
            params=self.command[1]
            self.app.orca.auto_exposure_activated=True
            self.app.orca.auto_expose_start=params["start_s"]
            self.app.orca.auto_expose_min=params["min_s"]
            self.app.orca.auto_expose_max=params["max_s"]
            self.app.orca.autobtn.setStyleSheet("background-color:green")
        
        elif self.command[0]=="save_comment_only":
            self.app.h5saving.save_comment()

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

        self.master_script_index=None

        self.sleep_start=None
        self.sleep_duration=0

        # stage mapping
        self.script_x_entries=[0,50,10]
        self.script_y_entries=[0,50,10]

        self.grid_spatial=True
        self.grid_spectral=False


        self.IV_end_current_mA=300
        self.IV_start_current_mA=0
        self.IV_step_current_mA=5

        self.IV_end_voltage=10
        self.IV_start_voltage=0
        self.IV_step_voltage=0.25

        self.IV_settling_time=0.05

        self.IV_spatial=True
        self.IV_spectral=True

        self.IV_curve_voltages=[0]
        self.IV_curve_currents=[0]
        self.IV_optical_spatial=[0]

        self.float_keys=set(["spatial_acquisition_time_s",
                            "spectral_acquisition_time_s",
                            "center_wavelength_nm",
                            "stage_x_mm",
                            "stage_y_mm",
                            "sleep_s",
                            "voltage_V",
                            "current_mA"])
        self.bool_keys=set(["save_spectral_image_bool","electric_output_bool"])

        self.string_keys_any=set(["comment","group_name","acquisition_name"])#,"add_to_acquisition_name"])
        self.string_keys=dict()
        self.string_keys["spectral_shutter_mode"]=set(["normal","open","closed"])
        self.string_keys["grating"]=set(["1","2","3","4","5","6"])
        self.string_keys["filter"]=set(["1","2","3","4","5","6"])
        self.string_keys["spatial_resolution"]=set(["2048","1024","512"])
        self.none_keys=set(["save_timeline","reset_timeline","save_comment_only","spectral_acquire",
                       "spatial_acquire","spatial_auto_exposure_stop",
                       "spectral_auto_exposure_stop","electric_measurement_to_timeline"])
                        #"show_timeline","show_iv_curve","pause_timeline","continue_timeline"
        self.object_keys=dict()
        self.object_keys["spatial_auto_exposure"]=set(["start_s","min_s","max_s"])
        self.object_keys["spectral_auto_exposure"]=set(["start_s","min_s","max_s"])
        self.object_keys["stage_mapping"]=set(["spectral_bool","spatial_bool","x_min_mm","x_max_mm",
                                          "x_num_int","y_min_mm","y_max_mm","y_num_int"])
        self.object_keys["measure_iv_curve_set_voltages"]=set(["spectral_bool","spatial_bool","start_voltage_V",
                                             "end_voltage_V","step_voltage_V","settling_time_s"])
        self.object_keys["measure_iv_curve_set_currents"]=set(["spectral_bool","spatial_bool","start_current_mA",
                                             "end_current_mA","step_current_mA","settling_time_s"])
        self.object_keys["spectral_roi"]=set(["x_min_int","x_max_int","y_min_int","y_max_int"])
 
        self.sub_script_keys=set(["measure_iv_curve_set_currents","measure_iv_curve_set_voltages","stage_mapping"])



    def grid_mapping_on_thread(self,step_done):
        if step_done:
            if self.script_canceled:
                self.script_end()
                return None
            self.script_index +=1
            #print(str(self.script_index)+"   "+str(self.number_of_points))
            if self.script_index==self.number_of_points:
                if self.master_script_index is None:
                    self.script_end()
                else:
                    self.script_index=0
                    self.master_script_thread(True)
                #self.script_end()
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
                self.app.h5saving.acq_name += "_map_"+str(self.script_index)
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
        
        widget = QComboBox()
        widget.addItems(["choose script","from settings txt","grid mapping","I-V-curve voltages","I-V-curve currents",
                         "calibrate spatial camera via stage (not implemented)"])
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
                self.master_script_thread(True)
            elif self.script_selected==2:
                self.grid_mapping_script()
            elif self.script_selected==3:
                self.acquire_IV_voltages()
            elif self.script_selected==4:
                self.acquire_IV_currents()
              
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

        if self.script_selected==3 or self.script_selected==4: # turn off after IV curve
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
            self.acquire_IV_window_voltages()
        elif self.script_selected==4:
            self.acquire_IV_window_currents()

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
                self.master_script_thread(True)
        
            elif self.script_selected==2:
                if self.grid_spectral:
                    self.app.pixis.shutterbtn.setText("Shutter (Open)")
                    self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", 'Always Open')
                self.grid_mapping_script()
            elif self.script_selected==3:
                if self.IV_spectral:
                    self.app.pixis.shutterbtn.setText("Shutter (Open)")
                    self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", 'Always Open')
                self.acquire_IV_voltages()
            elif self.script_selected==4:
                if self.IV_spectral:
                    self.app.pixis.shutterbtn.setText("Shutter (Open)")
                    self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", 'Always Open')
                self.acquire_IV_currents()
                

    def sleep_long_script(self,time_seconds):
        self.sleep_start=time.time()
        self.sleep_duration=time_seconds
        while self.sleep_duration>0:
            time.sleep(0.5)
            self.sleep_duration -= 0.5
            QApplication.processEvents()

    def check_script(self,fname):
        
        with open(fname, "r") as f:
            lines=f.read().splitlines()

        error_found=False
        commands=[]
        for counter,line in enumerate(lines):
            if len(line)==0:#line in ['\n', '\r\n']:
                #empty lines
                pass
            elif line[0]=="#":
                pass
            else: 
                expressions=line.split(",")
                if len(expressions)==1:
                    print(expressions[0])
                    key_value=expressions[0].split(":")
                    print(key_value)
                    if len(key_value)==1:
                        if key_value[0].strip() in self.none_keys:
                            commands.append(key_value[0].strip())
                        elif len(key_value.strip())==0:
                            #just white spaces
                            pass
                        else:
                            self.app.add_log("Error in line "+str(counter+1))
                            error_found=True

                    elif len(key_value)>2:
                        self.app.add_log("Error in line "+str(counter+1))
                        error_found=True
                    else:
                        key,value=key_value
                        key=key.strip()
                        value=value.strip()
                        if key in self.float_keys:
                            try:
                                num_value=np.double(value)
                                if num_value>0:
                                    commands.append((key,num_value))
                                else:
                                    self.app.add_log("Error in line "+str(counter+1))
                                    error_found=True

                            except:
                                self.app.add_log("Error in line "+str(counter+1))
                                error_found=True
                        elif key in self.bool_keys:
                            if value=="True" or value=="1":
                                commands.append((key,True))
                            elif value=="False" or value=="0":
                                commands.append((key,False))
                            else:
                                self.app.add_log("Error in line "+str(counter+1))
                                error_found=True
                        elif key in self.string_keys_any:
                            commands.append((key,value))
                        elif key in self.string_keys:
                            if value in self.string_keys[key]:
                                commands.append((key,value))
                            else:
                                self.app.add_log("Error in line "+str(counter+1))
                                error_found=True
                        else:
                            self.app.add_log("Error (invalid keyword)in line "+str(counter+1))
                else:
                    method=expressions[0].strip()
                    if method in self.object_keys:
                        try:
                            method_dict=dict()
                            for expr in expressions[1:]:
                                key,value=expr.split(":")

                                if key.strip() == "spectral_bool" or key.strip()=="spatial_bool":
                                    if value.strip()=="True" or value.strip()=="1":
                                        method_dict[key.strip()]=True
                                    elif value.strip()=="False" or value.strip()=="0":
                                        method_dict[key.strip()]=False
                                    else:
                                        self.app.add_log("Error (bool) in line "+str(counter+1))
                                        error_found=True
                                else:
                                    num_value=np.double(value)
                                    if num_value<0:
                                        self.app.add_log("Error (float) in line "+str(counter+1))
                                        error_found=True
                                    else:
                                        method_dict[key.strip()]=num_value

                            if set(method_dict.keys()) == self.object_keys[method]:
                                commands.append((method,method_dict))
                            else:
                                self.app.add_log("Error (invalid args) in line "+str(counter+1))
                                error_found=True

                        except:
                            self.app.add_log("Error in line "+str(counter+1))
                            error_found=True
                            
                    else:
                        self.app.add_log("Error (invalid method) in line "+str(counter+1))
                        error_found=True

        if error_found:
            commands=None
        else:
            self.app.add_log("Script containing "+str(len(commands))+" commands")
            for i in commands:
                print(i)
        return commands

    def script_from_txt_window(self):
        self.fname,ftype = QFileDialog.getOpenFileName(self.app, 'Open file', 
               self.app.h5saving.save_folder,"settings list (*.txt)")
        #print(fname)
        if self.fname:
            settings_list=self.check_script(self.fname)
            if settings_list is not None:
                self.settings_list=settings_list
                self.master_number_of_points=len(settings_list)
                self.master_script_index=-1
                self.script_settings_prepared=True
                self.btnexec.setStyleSheet("background-color:lightgrey;")
                self.btnstart.setStyleSheet("background-color:cyan;")


    def master_script_thread(self,step_done):
        if step_done:
            if self.script_canceled:
                self.script_end()
                return None
            self.master_script_index +=1
            if self.master_script_index==self.master_number_of_points:
                self.app.add_log(str(self.master_script_index)+" from "+str(self.master_number_of_points))
                #self.app.add_log(str(self.script_index)+" from "+str(self.number_of_points))
                self.master_script_index =0
                self.script_end()
            elif self.script_paused:
                self.app.add_log("script paused")
                return None
            else:
                if self.master_script_index==0:
                    self.app.add_log("master script from .txt starting")
                
                self.app.add_log(str(self.master_script_index)+" from "+str(self.master_number_of_points))

                command=self.settings_list[self.master_script_index]

                if command[0] in self.sub_script_keys:
                    self.app.add_log("sub_script started")
                    params=command[1]
                    if command[0]=="stage_mapping":
                        #print("this is for test prupose")
                        xmin=params["x_min_mm"]
                        xmax=params["x_max_mm"]
                        xnum=int(params["x_num_int"])

                        ymin=params["y_min_mm"]
                        ymax=params["y_max_mm"]
                        ynum=int(params["y_num_int"])

                        xcoords=np.linspace(xmin,xmax,xnum)
                        ycoords=np.linspace(ymin,ymax,int(ynum))
                        xx,yy=np.meshgrid(xcoords,ycoords)

                        newx=np.zeros(xx.shape[0]*xx.shape[1])
                        newy=np.zeros(yy.shape[0]*yy.shape[1])
                        counter=0
                        orderbool=True
                        for i in range(xx.shape[0]):
                            orderbool=not orderbool
                            for j in range(xx.shape[1]):
                                if orderbool:
                                    jnum=xx.shape[1]-1-j
                                else:
                                    jnum=j        
                                newx[counter]=xx[i,jnum]
                                newy[counter]=yy[i,jnum]
                                counter+=1

                        self.grid_spatial=params["spatial_bool"]
                        self.grid_spectral=params["spectral_bool"]
                        self.script_positions_x=newx
                        self.script_positions_y=newy  
                        self.script_settings_prepared=True
                        self.btnexec.setStyleSheet("background-color:lightgrey;")
                        self.btnstart.setStyleSheet("background-color:cyan;")
                        self.grid_mapping_script()

                    elif command[0]=="measure_iv_curve_set_currents":

                        self.IV_start_current_mA=params["start_current_mA"]
                        self.IV_end_current_mA=params["end_current_mA"]
                        self.IV_step_current_mA=params["step_current_mA"]

                        self.IV_settling_time=params["settling_time_s"]
                        self.IV_spatial=params["spatial_bool"]
                        self.IV_spectral=params["spectral_bool"]
                        self.acquire_IV_currents()

                    elif command[0]=="measure_iv_curve_set_voltages":

                        self.IV_start_voltage=params["start_voltage_V"]
                        self.IV_end_voltage=params["end_voltage_V"]
                        self.IV_step_voltage=params["step_voltage_V"]
            
                        self.IV_settling_time=params["settling_time_s"]
                        self.IV_spatial=params["spatial_bool"]
                        self.IV_spectral=params["spectral_bool"]
                        self.acquire_IV_voltages()

                else:
                    self.mworker=Master_Script(self.app,command)
                    self.mworker.signals.update.connect(self.master_script_thread)
                    self.app.threadpool.start(self.mworker)


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
        self.app.h5saving.acq_name += "_map_"+str(self.script_index)
        self.app.threadpool.start(self.grid_mapper)

    def acquire_IV_window_voltages(self):
        heading_string="Acquire I-V-Curve by stepwise increasing the voltage from the set minimum to maximum value"
        heading_string+=" and measuring the corresponding current after a given settling time. "
        heading_string+="(Note: If 'Spectral image' is selected, the shutter is set to always open.)"
        defaultlist=[self.IV_start_voltage,self.IV_end_voltage,self.IV_step_voltage,self.IV_settling_time]
        labellist=["Voltage-Start (V)","Voltage-End (V)","Voltage-Step (V)","Settling Time (s)"]
        self.window = self.app.entrymaskiv(self.app,"set_voltages",defaultlist,labellist,heading_string)
        self.window.location_on_the_screen()
        self.window.show()

    def acquire_IV_window_currents(self):
        heading_string="Acquire I-V-Curve by stepwise increasing the current from the set minimum to maximum value"
        heading_string+=" and measuring the corresponding voltage after a given settling time. "
        heading_string+="(Note: If 'Spectral image' is selected, the shutter is set to always open.)"
        defaultlist=[self.IV_start_current_mA,self.IV_end_current_mA,self.IV_step_current_mA,self.IV_settling_time]
        labellist=["Current-Start (mA)","Current-End (mA)","Current-Step (mA)","Settling Time (s)"]
        self.window = self.app.entrymaskiv(self.app,"set_currents",defaultlist,labellist,heading_string)
        self.window.location_on_the_screen()
        self.window.show()


    def iv_curve_on_thread_voltages(self,step_done):
        if step_done:
            if self.script_canceled:
                self.script_end()
                return None
            self.script_index +=1
            if self.script_index==self.number_of_points:
                self.app.add_log(str(self.script_index)+" from "+str(self.number_of_points))
                self.IV_curve_currents.append(self.app.keysight.currentA_actual)        
                self.IV_curve_voltages.append(self.app.keysight.voltage_actual)
                self.app.keysight.IVcurveplot.setData(self.IV_curve_voltages,self.IV_curve_currents)
                self.app.metadata_timeline["IV_current"]=self.IV_curve_currents
                self.app.metadata_timeline["IV_voltage"]=self.IV_curve_voltages
                #self.app.metadata_timeline["IV_curve"]=np.zeros([len(self.IV_curve_currents),2])
                #self.app.metadata_timeline["IV_curve"][:,0]=self.IV_curve_voltages
                #self.app.metadata_timeline["IV_curve"][:,1]=self.IV_curve_currents
                self.app.h5saving.save_to_h5_timeline()
                if self.master_script_index is None:
                    self.script_end()
                else:
                    # turn off after

                    self.app.keysight.current=0       
                    self.app.keysight.voltage=0
                    self.app.keysight.currentwidget.setText(str(self.app.keysight.current))
                    self.app.keysight.voltwidget.setText(str(self.app.keysight.voltage))

                    done_event = threading.Event()
                    self.app.keysight.thread_set_current_script(done_event)
                    done_event.wait()

                    done_event = threading.Event()
                    self.app.keysight.thread_set_voltage_script(done_event)
                    done_event.wait()


                    self.app.keysight.output_on=False
                    done_event = threading.Event()
                    self.app.keysight.thread_power_script(done_event)
                    done_event.wait()

                    self.script_index=0
                    self.master_script_thread(True)
            elif self.script_paused:
                self.app.add_log("script paused")
                return None
            else:
                self.app.add_log(str(self.script_index)+" from "+str(self.number_of_points))

                self.IV_curve_currents.append(self.app.keysight.currentA_actual)        
                self.IV_curve_voltages.append(self.app.keysight.voltage_actual)
                #print(self.IV_curve_voltages)
                self.app.keysight.IVcurveplot.setData(self.IV_curve_voltages,self.IV_curve_currents)

                set_volt=self.IV_set_voltages[self.script_index]
                self.app.keysight.voltwidget.setText(str(set_volt))
                self.iv_worker=IV_Measurement("set_voltages",self.app.keysight,self.app.orca,self.app.pixis,
                                              self.IV_spatial,self.IV_spectral,set_volt,self.IV_settling_time)
                self.iv_worker.signals.update.connect(self.iv_curve_on_thread_voltages)
                self.app.h5saving.acq_name += "_IV_"+str(self.script_index)
                self.app.threadpool.start(self.iv_worker)

    def iv_curve_on_thread_currents(self,step_done):
        if step_done:
            if self.script_canceled:
                self.script_end()
                return None
            self.script_index +=1
            if self.script_index==self.number_of_points:
                self.app.add_log(str(self.script_index)+" from "+str(self.number_of_points))
                self.IV_curve_currents.append(self.app.keysight.currentA_actual)        
                self.IV_curve_voltages.append(self.app.keysight.voltage_actual)
                self.app.keysight.IVcurveplot.setData(self.IV_curve_voltages,self.IV_curve_currents)
                self.app.metadata_timeline["IV_current"]=self.IV_curve_currents
                self.app.metadata_timeline["IV_voltage"]=self.IV_curve_voltages
                #self.app.metadata_timeline["IV_curve"]=np.zeros([len(self.IV_curve_currents),2])
                #self.app.metadata_timeline["IV_curve"][:,0]=self.IV_curve_voltages
                #self.app.metadata_timeline["IV_curve"][:,1]=self.IV_curve_currents
                self.app.h5saving.save_to_h5_timeline()
                if self.master_script_index is None:
                    self.script_end()
                else:
                    # turn off after
                    
                    self.app.keysight.current=0       
                    self.app.keysight.voltage=0
                    self.app.keysight.currentwidget.setText(str(self.app.keysight.current))
                    self.app.keysight.voltwidget.setText(str(self.app.keysight.voltage))

                    done_event = threading.Event()
                    self.app.keysight.thread_set_current_script(done_event)
                    done_event.wait()

                    done_event = threading.Event()
                    self.app.keysight.thread_set_voltage_script(done_event)
                    done_event.wait()


                    self.app.keysight.output_on=False
                    done_event = threading.Event()
                    self.app.keysight.thread_power_script(done_event)
                    done_event.wait()

                    self.script_index=0
                    self.master_script_thread(True)

            elif self.script_paused:
                self.app.add_log("script paused")
                return None
            else:
                self.app.add_log(str(self.script_index)+" from "+str(self.number_of_points))

                self.IV_curve_currents.append(self.app.keysight.currentA_actual)        
                self.IV_curve_voltages.append(self.app.keysight.voltage_actual)
                self.app.keysight.IVcurveplot.setData(self.IV_curve_voltages,self.IV_curve_currents)

                set_current_mA=self.IV_set_currents_mA[self.script_index]

                self.app.keysight.currentwidget.setText(str(set_current_mA))
                self.iv_worker=IV_Measurement("set_currents",self.app.keysight,self.app.orca,self.app.pixis,
                                              self.IV_spatial,self.IV_spectral,set_current_mA,self.IV_settling_time)
                self.iv_worker.signals.update.connect(self.iv_curve_on_thread_currents)
                self.app.h5saving.acq_name += "_IV_"+str(self.script_index)
                self.app.threadpool.start(self.iv_worker)



    def acquire_IV_voltages(self):

        self.app.add_log("Acquiring I-V-Curve")

        self.app.keysight.show_IV()

        self.IV_curve_voltages=[]
        self.IV_curve_currents=[]
        if self.app.orca.connected:
            self.IV_optical_spatial=[]
        
        if self.app.keysight.output_on:
            self.app.keysight.output_on =False
            done_event = threading.Event()
            self.app.keysight.thread_power_script(done_event)
            done_event.wait()

        self.app.keysight.current=self.app.keysight.max_currentmA #-0.01       
        self.app.keysight.voltage=0
        self.app.keysight.currentwidget.setText(str(self.app.keysight.current))
        self.app.keysight.voltwidget.setText(str(self.app.keysight.voltage))

        self.app.keysight.powerbtn.setStyleSheet("background-color: green;color: black")
        self.app.keysight.output_on =True

        done_event = threading.Event()
        self.app.keysight.thread_power_script(done_event)
        done_event.wait()        

        self.number_of_points=int((self.IV_end_voltage-self.IV_start_voltage)/self.IV_step_voltage)+1 

        self.IV_set_voltages=[]
        for i in range(self.number_of_points):
            self.IV_set_voltages.append(self.IV_start_voltage+i*self.IV_step_voltage)
        set_volt=self.IV_set_voltages[self.script_index]
        self.app.keysight.voltwidget.setText(str(set_volt))
        self.iv_worker=IV_Measurement("set_voltages",self.app.keysight,self.app.orca,self.app.pixis,
                                      self.IV_spatial,self.IV_spectral,set_volt,self.IV_settling_time)
        self.iv_worker.signals.update.connect(self.iv_curve_on_thread_voltages)
        self.app.h5saving.acq_name += "_IV_"+str(self.script_index)
        self.app.threadpool.start(self.iv_worker)

    def acquire_IV_currents(self):

        self.app.add_log("Acquiring I-V-Curve")

        self.app.keysight.show_IV()

        self.IV_curve_voltages=[]
        self.IV_curve_currents=[]
        if self.app.orca.connected:
            self.IV_optical_spatial=[]
        
        if self.app.keysight.output_on:
            self.app.keysight.output_on =False
            done_event = threading.Event()
            self.app.keysight.thread_power_script(done_event)
            done_event.wait()

        self.app.keysight.current=0      
        self.app.keysight.voltage=self.app.keysight.max_voltage# -0.01
        self.app.keysight.currentwidget.setText(str(self.app.keysight.current))
        self.app.keysight.voltwidget.setText(str(self.app.keysight.voltage))

        self.app.keysight.powerbtn.setStyleSheet("background-color: green;color: black")
        self.app.keysight.output_on =True

        done_event = threading.Event()
        self.app.keysight.thread_power_script(done_event)
        done_event.wait()
        self.number_of_points=int((self.IV_end_current_mA-self.IV_start_current_mA)/self.IV_step_current_mA)+1 

        self.IV_set_currents_mA=[]
        for i in range(self.number_of_points):
            self.IV_set_currents_mA.append(self.IV_start_current_mA+i*self.IV_step_current_mA)
        #print(self.IV_set_currents_mA)
        set_current_mA=self.IV_set_currents_mA[self.script_index]
        self.iv_worker=IV_Measurement("set_currents",self.app.keysight,self.app.orca,self.app.pixis,
                                      self.IV_spatial,self.IV_spectral,set_current_mA,self.IV_settling_time)
        self.iv_worker.signals.update.connect(self.iv_curve_on_thread_currents)
        self.app.h5saving.acq_name += "_IV_"+str(self.script_index)
        self.app.threadpool.start(self.iv_worker)