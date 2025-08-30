from PyQt5.QtWidgets import QHBoxLayout,QFileDialog,QLabel,QComboBox,QApplication,QVBoxLayout
from PyQt5.QtCore import QTimer
import numpy as np
import time

class Scripting:
    def __init__(self,app):
        self.app=app
        
        # stage mapping
        self.script_x_entries=None
        self.script_y_entries=None
        self.script_execution=False
        self.script_index=None


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

        self.labelscr = QLabel("")
        self.labelscr.setStyleSheet("color:white")
        self.labelscr.setFixedWidth(100)
        
        widget = QComboBox()
        self.script_selected=0
        widget.addItems(["choose script","from settings txt","grid mapping","I-V-curve"])
        widget.setStyleSheet("background-color: lightGray")
        widget.setFixedHeight(25)
        widget.currentIndexChanged.connect(self.script_changed )        
        self.dropdown.addWidget(widget)

        layoutscriptbuttons=QHBoxLayout()

        self.btnexec = self.app.normal_button(layoutscriptbuttons,"Execute",self.script_button_execute)
        #self.btnexec.set

        layoutscriptbuttons.addStretch()
        label = QLabel("click only once ->\n(wait one acq-time)")
        label.setStyleSheet("color:white")
        label.setWordWrap(True)
        layoutscriptbuttons.addWidget(label)
        
        self.btnpause = self.app.normal_button(layoutscriptbuttons,"Pause",self.script_button_pause)
        
        self.dropdown.addLayout(layoutscriptbuttons)
        layoutright.addLayout(self.dropdown)
        self.app.set_layout_visible(self.dropdown,False)
        layoutright.addItem(self.app.vspace)



    def script_button_pause(self):
        if self.script_execution:
            self.btnpause.setText("Continue")
            self.script_execution=False
        else:
            self.btnpause.setText("Pause")
            self.script_execution=True
            if self.script_selected==1:
                self.script_from_txt()
            elif self.script_selected==2:
                self.entry_window_script_grid()

    def script_end(self):
        self.script_execution=False
        self.script_index=None
        self.app.h5saving.save_on_acquire()
        self.btnexec.setText("Execute")
        self.labelscr.setText("")
    
    def script_button_execute(self):
        if self.app.pixis.live_mode_running or self.app.orca.live_mode_running:
            print("Live mode needs to be stopped before executing scripts")
        else:
            if self.script_selected==0:
                print("no script selected to execute")
                
            elif self.script_selected==1:
                if not self.script_execution and self.script_index is None:
                    self.script_from_txt()
                else:
                    self.script_end()

            elif self.script_selected==2:
                if not self.script_execution and self.script_index is None:
                    self.entry_window_script_grid()
                else:
                    self.script_end()
            else:
                if not self.script_execution and self.script_index is None:
                    self.acquire_IV()
                else:
                    self.script_end()


    def sleep_method(self,time_seconds):
        self.sleep_timer=QTimer()
        self.sleep_timer.timeout.connect(self.end_sleep)
        timer_time=int(time_seconds*1000)
        self.sleep_timer.start(timer_time)

    def end_sleep(self):
        self.sleep_timer.stop()

    def check_script(self,fname):
        settings_list=[]
        double_format_keys=["spatial_acquisition_time_seconds",
                            "spectral_acquisition_time_seconds",
                            "center_wavelength_nm",
                            "stage_x_mm",
                            "stage_y_mm",
                            "sleep_seconds"]
        int_format_keys=["grating_position_int"]
        bool_format_keys=["save_spectral_image_bool"]
        comment_required=["sleep_seconds"]
        spectral_required=["spectral_acquisition_time_seconds",
                           "center_wavelength_nm",
                           "grating_position_int",
                           "save_spectral_image_bool",
                           "stage_x_mm",
                           "stage_y_mm"]
        spatial_required=["spatial_acquisition_time_seconds",
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

    def script_from_txt(self):
        fname,ftype = QFileDialog.getOpenFileName(self, 'Open file', 
               self.app.h5saving.save_folder,"settings list (*.txt)")
        #print(fname)
        if fname:
            settings_list=self.check_script(fname)
            if settings_list is None:
                print("script includes errors")
            else:

                self.script_execution=True
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
                        self.app.pixis.acqtime_spectral=settings["spectral_acquisition_time_seconds"]
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

            
    def script_changed(self,i):
        self.script_selected=i

            
    def entry_window_script_grid(self):
        if self.script_index is None:
            self.w = self.app.entrymask6(self.app)
            self.w.location_on_the_screen()
            self.w.exec()

        # execute script
        if self.script_execution:
            if self.script_index is None:
                self.script_index=0
            self.btnexec.setText("Cancel")
            if not self.app.h5saving.save_on_acquire_bool:
                self.app.h5saving.save_on_acquire()
            number_of_points=len(self.script_positions_x)        
            for i in range(self.script_index,number_of_points):
                self.app.stage.xpos=self.script_positions_x[i]
                self.app.stage.ypos=self.script_positions_y[i]
                self.app.stage.stage_goto()      
                xcheck,ycheck=self.app.stage.get_position()
                print("check position: "+str(xcheck)+","+str(ycheck))
                
                QApplication.processEvents()
                if not self.script_execution:
                    return None
                
                if self.script_selected==2:
                    self.app.orca.acquire_clicked_spatial()
                elif self.script_selected==3:
                    self.app.pixis.acquire_clicked_spectral()
                else:
                    self.app.orca.acquire_clicked_spatial()
                    self.app.threadpool.waitForDone()
                    self.app.pixis.acquire_clicked_spectral()
                
                self.app.threadpool.waitForDone()
                self.script_index+=1
                print(str(i+1)+" from "+str(number_of_points))
                self.labelscr.setText(str(i+1)+"/"+str(number_of_points))
                QApplication.processEvents()
                if not self.script_execution:
                    return None
                    
            self.script_end()


    def acquire_IV(self):
        if not self.IV_settings_prepared:
            self.window = self.app.entrymask4b(self.app,"IVcurve")#device,roi
            heading_string="Acquire I-V-Curve by stepwise increasing the voltage from 0 to the set maximum value"
            heading_string+=" and measuring the corresponding current after a given settling time. "
            heading_string+="After pressing 'Confirm', which closes this window, press 'Acq. I-V-Curve' in the main window again "
            heading_string+="to start the measurement."
            self.window.setHeading(heading_string)
            self.window.setLabels(["Voltage-Start (V)","Voltage-Step (V)","Voltage-End (V)","Settling Time (s)"])
            defaultlist=[self.IV_start_voltage,self.IV_step_voltage,self.IV_end_voltage,self.IV_settling_time]
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
                self.currentA_actual=float(self.psu.query("MEAS:CURR?").strip())
                self.voltage_actual=float(self.psu.query("MEAS:VOLT?").strip())
                self.timeline_time = time.time()-self.timeline_start
                
                self.IV_curve_currents.append(self.currentA_actual)        
                self.IV_curve_voltages.append(self.voltage_actual)
                
                self.voltage_list.append(self.voltage_actual)
                self.currentA_list.append(self.currentA_actual)

                self.timeline_list.append(self.timeline_time)
                
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
