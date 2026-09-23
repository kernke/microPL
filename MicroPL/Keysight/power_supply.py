import pyvisa
import datetime
import numpy as np
import time
import pyqtgraph as pg

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


# =============================================================
# SIGNALS
# =============================================================

class Update_Signal(QObject):

    string_update = pyqtSignal(object)
    update = pyqtSignal()


# =============================================================
# PSU VOLTAGE
# =============================================================

class PSU_voltage(QRunnable):

    def __init__(self, psu, voltage, event=None):

        super().__init__()

        self.psu = psu
        self.voltage = voltage

        self.signals = Update_Signal()

        self.event = event

    @pyqtSlot()
    def run(self):

        try:

            self.psu.write(
                f"SOUR:VOLT {self.voltage}"
            )

        except Exception as e:

            print("PSU voltage error:", e)

        self.signals.update.emit()

        if self.event:

            self.event.set()


# =============================================================
# PSU CURRENT
# =============================================================

class PSU_current(QRunnable):

    def __init__(self, psu, current, event=None):

        super().__init__()

        self.psu = psu

        # GUI current is mA
        self.current = current

        self.signals = Update_Signal()

        self.event = event

    @pyqtSlot()
    def run(self):

        try:

            # Keysight expects A
            self.psu.write(
                f"SOUR:CURR {self.current / 1000}"
            )

        except Exception as e:

            print("PSU current error:", e)

        self.signals.update.emit()

        if self.event:

            self.event.set()


# =============================================================
# PSU POWER
# =============================================================

class PSU_power(QRunnable):

    def __init__(
        self,
        psu,
        on_bool,
        voltage,
        current,
        event=None
    ):

        super().__init__()

        self.psu = psu
        self.on_bool = on_bool
        self.voltage = voltage
        self.current = current

        self.signals = Update_Signal()

        self.event = event

    @pyqtSlot()
    def run(self):

        try:

            if self.on_bool:

                self.psu.write(
                    f"SOUR:VOLT {self.voltage}"
                )

                self.psu.write(
                    f"SOUR:CURR {self.current / 1000}"
                )

                self.psu.write(
                    "OUTP ON"
                )

            else:

                self.psu.write(
                    "OUTP OFF"
                )

        except Exception as e:

            print("PSU power error:", e)

        self.signals.update.emit()

        if self.event:

            self.event.set()


# =============================================================
# HP 34401A STATUS WORKER
# =============================================================

class Status_update(QRunnable):

    """
    Reads:

        Voltage -> Keysight E36105B
        Current -> HP 34401A through Prologix

    Voltage is returned in V.

    Current is returned in A.
    """

    def __init__(
            self,
            psu,
            event=None
        ):
            super().__init__()
            self.psu = psu
            self.signals = Update_Signal()
            self.event = event


    # =========================================================
    # WORKER
    # =========================================================

    @pyqtSlot()
    def run(self):

        # -----------------------------------------------------
        # READ KEYSIGHT VOLTAGE
        # -----------------------------------------------------

        try:

            voltage_actual = float(
                self.psu.query(
                    "MEAS:VOLT?"
                ).strip()
            )

        except Exception as e:

            print(
                "Keysight voltage reading error:",
                e
            )

            voltage_actual = 0.0

        # -----------------------------------------------------
        # READ KEYSIGHT Current
        # -----------------------------------------------------
        currentA_actual=float(self.psu.query("MEAS:CURR?").strip())



        # -----------------------------------------------------
        # STATUS STRING
        # -----------------------------------------------------

        statusstring = (
            "Voltage: "
            + str(
                np.round(
                    voltage_actual,
                    3
                )
            )
            + " V\n"
        )


        if currentA_actual is not None:

            statusstring += (
                "Current: "
                + str(
                    np.round(
                        currentA_actual * 1000,
                        3
                    )
                )
                + " mA"
            )

        else:

            statusstring += (
                "Current: HP 34401A error"
            )


        # -----------------------------------------------------
        # SEND RESULT TO GUI
        # -----------------------------------------------------

        self.signals.string_update.emit(
            (
                statusstring,
                voltage_actual,
                currentA_actual,
            )
        )


        if self.event:

            self.event.set()


# =============================================================
# MAIN KEYSIGHT CLASS
# =============================================================

class Keysight:

    def __init__(self, app):

        self.app = app


        # =====================================================
        # INITIAL STATE
        # =====================================================

        self.psu = None

        self.rm = None

        self.connected = False

        self.communication_running = False

        self.live_mode_running = False

        self.expanded = False
        self.expanded2 = False

        self.maximized = False


        # =====================================================
        # KEYSIGHT CONFIGURATION
        # =====================================================

        self.model_name = "E36105B"

        self.resource_str = (
            "USB0::0x2A8D::0x1602::MY61003313::0::INSTR"
        )


        # =====================================================
        # SAFETY LIMITS
        # =====================================================

        self.max_voltage = 20

        self.max_currentmA = 2000

        self.max_powermW = 20000


        # =====================================================
        # LIVE MEASUREMENT SETTINGS
        # =====================================================

        self.refresh_rate = 0.55

        self.voltage_actual = 0.0

        # Actual current is stored in A.

        self.currentA_actual = 0.0


        # =====================================================
        # TIMELINE
        # =====================================================

        self.voltage_list = []

        self.currentA_list = []

        self.timeline_list = []

        self.timeline_time = 0

        self.timeline_start = time.time()

        self.timeline_start_date = (
            datetime.datetime.now()
            .strftime(
                "%m/%d/%Y, %H:%M:%S.%f"
            )
        )

        self.timeline_reset_pressed = False


        # =====================================================
        # COMMUNICATION
        # =====================================================

        self.latency_time = 0.3


        # =====================================================
        # CONNECT KEYSIGHT
        # =====================================================

        try:

            self.rm = (
                pyvisa.ResourceManager()
            )

            self.psu = (
                self.rm.open_resource(
                    self.resource_str
                )
            )

            print(
                "Keysight connected"
            )

            self.connected = True

            self.app.add_log(
                "Keysight connected"
            )


            # -------------------------------------------------
            # INITIAL VALUES
            # -------------------------------------------------

            self.output_on = bool(
                np.double(
                    self.psu.query(
                        "OUTP?"
                    ).strip()
                )
            )


            # Keysight reports current in A.
            # GUI stores current in mA.

            self.current = (
                np.double(
                    self.psu.query(
                        "SOUR:CURR?"
                    ).strip()
                )
                * 1000
            )


            self.voltage = np.double(
                self.psu.query(
                    "SOUR:VOLT?"
                ).strip()
            )


        except Exception as e:

            self.connected = False

            print(
                "dummy mode for keysight"
            )

            print(
                "Keysight connection error:",
                e
            )

            self.app.add_log(
                "Keysight dummy mode"
            )

            self.voltage = 0

            self.current = 0

            self.output_on = False



    # =========================================================
    # DISCONNECT
    # =========================================================

    def disconnect(self):

        if self.live_mode_running:

            self.live_mode_running = False

            self.psleep_worker = (
                self.app.sleep_worker_class(
                    self.latency_time
                )
            )

            self.psleep_worker.signals.update_empty.connect(
                self.disconnect
            )

            self.app.threadpool.start(
                self.psleep_worker
            )

            self.app.add_log(
                "wait shortly for instruments to finish"
            )

            return


        if self.communication_running:

            self.psleep_worker = (
                self.app.sleep_worker_class(
                    self.latency_time
                )
            )

            self.psleep_worker.signals.update_empty.connect(
                self.disconnect
            )

            self.app.threadpool.start(
                self.psleep_worker
            )

            return


        # =====================================================
        # CLOSE KEYSIGHT
        # =====================================================

        try:

            if self.psu is not None:

                self.psu.close()

            print(
                "Keysight disconnected"
            )

        except Exception as e:

            print(
                "Error closing Keysight:",
                e
            )



    # =============================================================
    # LIVE MODE
    # =============================================================

    def live_mode(self):

        if not self.live_mode_running:

            self.live_mode_running = True

            self.btnlive.setStyleSheet(
                "background-color: green;color: black"
            )

            self.thread_task()

        else:

            self.live_mode_running = False

            self.btnlive.setStyleSheet(
                "background-color: lightGray;color: black"
            )

    # =============================================================
    # START STATUS MEASUREMENT
    # =============================================================

    def thread_task(self):

        if self.communication_running:

            self.sleep_worker = (
                self.app.sleep_worker_class(
                    self.latency_time
                )
            )

            self.sleep_worker.signals.update_empty.connect(
                self.thread_task
            )

            self.app.threadpool.start(
                self.sleep_worker
            )

        else:

            self.communication_running = True

            self.worker = Status_update(
                self.psu,
            )

            self.worker.signals.string_update.connect(
                self.status_update_from_thread
            )

            self.app.threadpool.start(
                self.worker
            )

    # =============================================================
    # SCRIPT STATUS MEASUREMENT
    # =============================================================

    def thread_task_script(self, event):

        while self.communication_running:

            time.sleep(0.1)

            QApplication.processEvents()

        self.communication_running = True

        self.worker = Status_update(
            self.psu,
            event=event
        )

        self.worker.signals.string_update.connect(
            self.status_update_from_thread
        )

        self.app.threadpool.start(
            self.worker
        )

    # =============================================================
    # SCRIPT SET CURRENT
    # =============================================================

    def thread_set_current_script(self, event):

        while self.communication_running:

            time.sleep(0.1)

            QApplication.processEvents()

        if (
            not self.current > self.max_currentmA
            and
            not self.voltage * self.current > self.max_powermW
        ):

            self.communication_running = True

            self.cworker = PSU_current(
                self.psu,
                self.current,
                event
            )

            self.cworker.signals.update.connect(
                self.thread_done_empty
            )

            self.app.threadpool.start(
                self.cworker
            )

        else:

            self.app.add_log(
                "Current not changed"
            )

            self.app.add_log(
                "Safety limits violated"
            )

    # =============================================================
    # SCRIPT SET VOLTAGE
    # =============================================================

    def thread_set_voltage_script(self, event):

        while self.communication_running:

            time.sleep(0.1)

            QApplication.processEvents()

        if (
            not self.voltage > self.max_voltage
            and
            not self.voltage * self.current > self.max_powermW
        ):

            self.communication_running = True

            if self.voltage<0:
                if self.app.switcher.mode_state != "negative":
                    self.app.switcher.set_negative()
            else:
                if self.app.switcher.mode_state != "positive":
                    self.app.switcher.set_positive()


            self.vworker = PSU_voltage(
                self.psu,
                abs(self.voltage),
                event
            )

            self.vworker.signals.update.connect(
                self.thread_done_empty
            )

            self.app.threadpool.start(
                self.vworker
            )

        else:

            self.app.add_log(
                "Voltage not changed"
            )

            self.app.add_log(
                "Safety limits violated"
            )

    # =============================================================
    # SCRIPT POWER
    # =============================================================

    def thread_power_script(
        self,
        event
    ):

        while self.communication_running:

            time.sleep(0.1)

            QApplication.processEvents()

        if self.output_on:

            cond1 = self.voltage > self.max_voltage
            cond2 = self.current > self.max_currentmA
            cond3 = (
                self.voltage * self.current
                > self.max_powermW
            )

            if not cond1 and not cond2 and not cond3:

                self.communication_running = True

                self.pworker = PSU_power(
                    self.psu,
                    self.output_on,
                    self.voltage,
                    self.current,
                    event
                )

                self.pworker.signals.update.connect(
                    self.thread_done_empty
                )

                self.powerbtn.setStyleSheet(
                    "background-color: green;color: black"
                )

                self.voltwidget.setStyleSheet(
                    "background-color: lightGray"
                )

                self.currentwidget.setStyleSheet(
                    "background-color: lightGray"
                )

                self.app.add_log(
                    "set: "
                    + str(np.round(self.voltage, 3))
                    + " V ; "
                    + str(np.round(self.current, 1))
                    + " mA"
                )

                self.app.add_log(
                    "Electric Power Output ON"
                )

                self.app.threadpool.start(
                    self.pworker
                )

            else:

                self.app.add_log(
                    "Electric Power not turned ON"
                )

                self.app.add_log(
                    "Safety limits violated"
                )

        else:

            self.communication_running = True

            self.pworker = PSU_power(
                self.psu,
                self.output_on,
                self.voltage,
                self.current,
                event
            )

            self.pworker.signals.update.connect(
                self.thread_done_empty
            )

            self.app.add_log(
                "Electric Power Output OFF"
            )

            self.powerbtn.setStyleSheet(
                "background-color: lightGray;color: black"
            )

            self.app.threadpool.start(
                self.pworker
            )

    # =============================================================
    # COMMUNICATION DONE
    # =============================================================

    def thread_done_empty(self):

        self.communication_running = False

    # =============================================================
    # SET VOLTAGE
    # =============================================================

    def thread_set_voltage(self):

        if self.communication_running:

            self.vsleep_worker = (
                self.app.sleep_worker_class(
                    self.latency_time
                )
            )

            self.vsleep_worker.signals.update_empty.connect(
                self.thread_set_voltage
            )

            self.app.threadpool.start(
                self.vsleep_worker
            )

        else:

            self.communication_running = True

            if self.voltage<0:
                if self.app.switcher.mode_state != "negative":
                    self.app.switcher.set_negative()
            else:
                if self.app.switcher.mode_state != "positive":
                    self.app.switcher.set_positive()

        
            self.vworker = PSU_voltage(
                self.psu,
                abs(self.voltage)
            )

            self.vworker.signals.update.connect(
                self.thread_done_empty
            )

            self.app.threadpool.start(
                self.vworker
            )

    # =============================================================
    # SET CURRENT
    # =============================================================

    def thread_set_current(self):

        if self.communication_running:

            self.csleep_worker = (
                self.app.sleep_worker_class(
                    self.latency_time
                )
            )

            self.csleep_worker.signals.update_empty.connect(
                self.thread_set_current
            )

            self.app.threadpool.start(
                self.csleep_worker
            )

        else:

            self.communication_running = True

            self.cworker = PSU_current(
                self.psu,
                self.current
            )

            self.cworker.signals.update.connect(
                self.thread_done_empty
            )

            self.app.threadpool.start(
                self.cworker
            )

    # =============================================================
    # POWER ON/OFF
    # =============================================================

    def thread_power_on_off(self):

        if self.communication_running:

            self.psleep_worker = (
                self.app.sleep_worker_class(
                    self.latency_time
                )
            )

            self.psleep_worker.signals.update_empty.connect(
                self.thread_power_on_off
            )

            self.app.threadpool.start(
                self.psleep_worker
            )

        else:

            self.communication_running = True

            self.pworker = PSU_power(
                self.psu,
                self.output_on,
                self.voltage,
                self.current
            )

            self.pworker.signals.update.connect(
                self.thread_done_empty
            )

            self.app.threadpool.start(
                self.pworker
            )

    # =============================================================
    # SLEEP BETWEEN MEASUREMENTS
    # =============================================================

    def thread_sleep(self):

        self.sleep_worker = (
            self.app.sleep_worker_class(
                self.refresh_rate
            )
        )

        self.sleep_worker.signals.update_empty.connect(
            self.thread_task
        )

        self.app.threadpool.start(
            self.sleep_worker
        )

    # =============================================================
    # STATUS UPDATE
    # =============================================================

    def status_update_from_thread(
        self,
        string_volt_curr_tuple
    ):

        status_string = string_volt_curr_tuple[0]

        voltage_actual = string_volt_curr_tuple[1]

        currentA_actual = string_volt_curr_tuple[2]

        # ---------------------------------------------------------
        # UPDATE STATUS LABEL
        # ---------------------------------------------------------

        self.app.status_electric.setText(
            status_string
        )

        # ---------------------------------------------------------
        # STORE ACTUAL VALUES
        # ---------------------------------------------------------
        
        if self.app.switcher.mode_state == "positive":
            self.voltage_actual = voltage_actual
        elif self.app.switcher.mode_state == "negative":
            self.voltage_actual = -voltage_actual
        else:
            self.voltage_actual = voltage_actual
            #print("error: switcher should be positive or negative to read out voltage")

        #if currentA_actual is not None:

        self.currentA_actual = currentA_actual


        # ---------------------------------------------------------
        # TIMELINE
        # ---------------------------------------------------------

        if self.timeline_reset_pressed:

            self.timeline_reset_pressed = False

            self.voltage_list = [
                self.voltage_actual
            ]

            self.currentA_list = [
                self.currentA_actual
            ]

            self.timeline_time = 0

            self.timeline_list = [
                self.timeline_time
            ]

            self.timeline_start = time.time()

            self.timeline_start_date = (
                datetime.datetime.now()
                .strftime(
                    "%m/%d/%Y, %H:%M:%S.%f"
                )
            )

        else:

            self.voltage_list.append(
                self.voltage_actual
            )

            self.currentA_list.append(
                self.currentA_actual
            )

            self.timeline_time = (
                time.time()
                - self.timeline_start
            )

            self.timeline_list.append(
                self.timeline_time
            )

        # ---------------------------------------------------------
        # UPDATE GUI COLOR FOR VOLTAGE/CURRENT
        # ---------------------------------------------------------

        if self.output_on:

            # =====================================================
            # VOLTAGE
            # =====================================================

            stsh = self.voltwidget.styleSheet()

            if np.isclose(
                self.voltage,
                self.voltage_actual,
                rtol=0.01,
                atol=0.01
            ):

                if "red" in stsh:

                    self.voltwidget.setStyleSheet(
                        "color:red;background-color: cyan;"
                    )

                else:

                    self.voltwidget.setStyleSheet(
                        "color:black;background-color: cyan;"
                    )

            else:

                if "red" in stsh:

                    self.voltwidget.setStyleSheet(
                        "color:red;background-color: lightGray;"
                    )

                else:

                    self.voltwidget.setStyleSheet(
                        "color:black;background-color: lightGray;"
                    )

            # =====================================================
            # CURRENT
            # =====================================================

            stsh = self.currentwidget.styleSheet()

            # self.current is mA.
            # currentA_actual is A.
            #
            # Therefore:
            #
            # self.current / 1000
            #
            # is the Keysight current setting in A.

            if (
                currentA_actual is not None
                and
                np.isclose(
                    self.current / 1000,
                    self.currentA_actual,
                    rtol=0.01,
                    atol=0.001
                )
            ):

                if "red" in stsh:

                    self.currentwidget.setStyleSheet(
                        "color:red;background-color: cyan;"
                    )

                else:

                    self.currentwidget.setStyleSheet(
                        "color:black;background-color: cyan;"
                    )

            else:

                if "red" in stsh:

                    self.currentwidget.setStyleSheet(
                        "color:red;background-color: lightGray;"
                    )

                else:

                    self.currentwidget.setStyleSheet(
                        "color:black;background-color: lightGray;"
                    )

        # ---------------------------------------------------------
        # SAVE STATUS
        # ---------------------------------------------------------

        self.app.metadata_timeline["unsaved"] = True

        # ---------------------------------------------------------
        # UPDATE PLOTS
        # ---------------------------------------------------------

        self.Acurve.setData(
            self.timeline_list,
            self.currentA_list
        )

        self.Vcurve.setData(
            self.timeline_list,
            self.voltage_list
        )

        self.p1.setXRange(
            0,
            self.timeline_time
        )

        self.communication_running = False

        # ---------------------------------------------------------
        # CONTINUE LIVE MODE
        # ---------------------------------------------------------

        if self.live_mode_running:

            self.thread_sleep()

    # =============================================================
    # EXPAND GUI
    # =============================================================

    def expand(self):

        if not self.expanded:

            self.expanded = True

            self.app.set_layout_visible(
                self.dropdown,
                True
            )

        else:

            self.expanded = False

            self.app.set_layout_visible(
                self.dropdown,
                False
            )

    # =============================================================
    # EXPAND TIMELINE
    # =============================================================

    def expand2(self):

        if not self.expanded2:

            self.expanded2 = True

            self.app.set_layout_visible(
                self.dropdown2,
                True
            )

        else:

            self.expanded2 = False

            self.app.set_layout_visible(
                self.dropdown2,
                False
            )

    # =============================================================
    # VOLTAGE EDITED
    # =============================================================

    def setvoltage_edited(self, s):

        if s:

            try:

                itsanumber = np.double(s)
                itsanumber = True

            except:

                itsanumber = False

            if itsanumber:

                self.voltage = np.double(s)

                if self.output_on:

                    stsh = (
                        self.voltwidget.styleSheet()
                    )

                    if "cyan" in stsh:

                        self.voltwidget.setStyleSheet(
                            "color:red;background-color: cyan;"
                        )

                    else:

                        self.voltwidget.setStyleSheet(
                            "color:red;background-color: lightGray;"
                        )

    # =============================================================
    # VOLTAGE CONFIRMED
    # =============================================================

    def setvoltage_confirmed(self):

        if (
            not self.voltage > self.max_voltage
            and
            not self.voltage * self.current
            > self.max_powermW
        ):  
            
            self.thread_set_voltage()

            self.voltwidget.setStyleSheet(
                "color: black;background-color: lightGray;"
            )

            self.app.add_log(
                "set: "
                + str(np.round(self.voltage, 3))
                + " V"
            )

        else:

            self.app.add_log(
                "Safety limits violated"
            )

    # =============================================================
    # CURRENT CONFIRMED
    # =============================================================

    def setcurrent_confirmed(self):

        if (
            not self.current > self.max_currentmA
            and
            not self.voltage * self.current
            > self.max_powermW
        ):

            self.thread_set_current()

            self.currentwidget.setStyleSheet(
                "color: black;background-color: lightGray;"
            )

            self.app.add_log(
                "set: "
                + str(np.round(self.current, 1))
                + " mA"
            )

        else:

            self.app.add_log(
                "Safety limits violated"
            )

    # =============================================================
    # CURRENT EDITED
    # =============================================================

    def setcurrent_edited(self, s):

        if s:

            try:

                itsanumber = np.double(s)
                itsanumber = True

            except:

                itsanumber = False

            if itsanumber:

                self.current = np.double(s)

                if self.output_on:

                    stsh = (
                        self.currentwidget.styleSheet()
                    )

                    if "cyan" in stsh:

                        self.currentwidget.setStyleSheet(
                            "color:red;background-color: cyan;"
                        )

                    else:

                        self.currentwidget.setStyleSheet(
                            "color:red;background-color: lightGray;"
                        )

    # =============================================================
    # POWER ON/OFF
    # =============================================================

    def power_on(self):

        if self.output_on:

            self.output_on = False

            self.thread_power_on_off()

            self.powerbtn.setStyleSheet(
                "background-color: lightGray;color: black"
            )

            self.voltwidget.setStyleSheet(
                "background-color: lightGray"
            )

            self.currentwidget.setStyleSheet(
                "background-color: lightGray"
            )

            self.app.add_log(
                "Electric Power Output OFF"
            )

        else:

            cond0 = (
                self.voltage
                > self.max_voltage
            )

            cond1 = (
                self.voltage * self.current
                > self.max_powermW
            )

            cond2 = (
                self.current
                > self.max_currentmA
            )

            if not cond0 and not cond1 and not cond2:

                self.output_on = True

                self.thread_power_on_off()

                self.powerbtn.setStyleSheet(
                    "background-color: green;color: black"
                )

                self.app.add_log(
                    "set: "
                    + str(np.round(self.voltage, 3))
                    + " V ; "
                    + str(np.round(self.current, 1))
                    + " mA"
                )

                self.app.add_log(
                    "Electric Power Output ON"
                )

            else:

                self.app.add_log(
                    "Electric Power not turned ON"
                )

                self.app.add_log(
                    "Safety limits violated"
                )

    # =============================================================
    # REFRESH RATE
    # =============================================================

    def refreshrate_edited(self, s):

        if s:

            try:

                itsanumber = np.double(s)
                itsanumber = True

            except:

                itsanumber = False

            if itsanumber:

                if np.double(s) < 0.5:

                    self.refresh_rate = 0.5

                else:

                    self.refresh_rate = np.double(s)

    # =============================================================
    # DUMMY
    # =============================================================

    def dummy_func(self):

        self.app.add_log(
            "device not connected"
        )

    # =============================================================
    # POWER SUPPLY GUI
    # =============================================================

    def power_ui(self, layoutright):

        self.expanded = False

        self.app.heading_label(
            layoutright,
            "Electric Power Supply",
            self.expand
        )

        self.dropdown = QVBoxLayout()

        # =========================================================
        # SWITCHER
        # =========================================================

        layoutswitcher = QHBoxLayout()

        if self.app.switcher.connected:

            self.btn_IVmode = (
                self.app.normal_button(
                    layoutswitcher,
                    "IV-Curve Mode",
                    self.app.switcher.set_IVcurve_mode
                )
            )

            self.btn_IVmode.setStyleSheet(
                "background-color: green"
            )

        else:

            self.btn_IVmode = (
                self.app.normal_button(
                    layoutswitcher,
                    "IV-Curve Mode",
                    self.dummy_func
                )
            )

            self.btn_IVmode.setStyleSheet(
                "background-color: red"
            )

        self.btn_IVmode.setFixedWidth(110)

        layoutswitcher.addStretch()

        if self.app.switcher.connected:

            self.btn_LCRmode = (
                self.app.normal_button(
                    layoutswitcher,
                    "LCR Mode",
                    self.app.switcher.set_LCR_mode
                )
            )

        else:

            self.btn_LCRmode = (
                self.app.normal_button(
                    layoutswitcher,
                    "LCR Mode",
                    self.dummy_func
                )
            )

            self.btn_LCRmode.setStyleSheet(
                "background-color: red"
            )

        self.btn_LCRmode.setFixedWidth(110)

        self.dropdown.addLayout(
            layoutswitcher
        )

        # =========================================================
        # POLARITY
        # =========================================================

        layoutswitcher2 = QHBoxLayout()

        if self.app.switcher.connected:

            self.btn_positive = (
                self.app.normal_button(
                    layoutswitcher2,
                    "Positive",
                    self.app.switcher.set_positive
                )
            )

        else:

            self.btn_positive = (
                self.app.normal_button(
                    layoutswitcher2,
                    "Positive",
                    self.dummy_func
                )
            )

            self.btn_positive.setStyleSheet(
                "background-color: red"
            )

        layoutswitcher2.addStretch()

        if self.app.switcher.connected:

            self.btn_negative = (
                self.app.normal_button(
                    layoutswitcher2,
                    "Negative",
                    self.app.switcher.set_negative
                )
            )

        else:

            self.btn_negative = (
                self.app.normal_button(
                    layoutswitcher2,
                    "Negative",
                    self.dummy_func
                )
            )

            self.btn_negative.setStyleSheet(
                "background-color: red"
            )

        layoutswitcher2.addStretch()

        if self.app.switcher.connected:

            self.btn_off = (
                self.app.normal_button(
                    layoutswitcher2,
                    "Off",
                    self.app.switcher.set_off
                )
            )

            self.btn_off.setStyleSheet(
                "background-color: green"
            )

        else:

            self.btn_off = (
                self.app.normal_button(
                    layoutswitcher2,
                    "Off",
                    self.dummy_func
                )
            )

            self.btn_off.setStyleSheet(
                "background-color: red"
            )

        self.dropdown.addLayout(
            layoutswitcher2
        )

        # =========================================================
        # OUTPUT
        # =========================================================

        layoutoutput = QHBoxLayout()

        if self.connected:

            self.powerbtn = (
                self.app.normal_button(
                    layoutoutput,
                    "Output",
                    self.power_on
                )
            )

            if self.output_on:

                self.powerbtn.setStyleSheet(
                    "background-color: green;color: black"
                )

        else:

            self.powerbtn = (
                self.app.normal_button(
                    layoutoutput,
                    "Output",
                    self.dummy_func
                )
            )

            self.powerbtn.setStyleSheet(
                "background-color: red;color: black"
            )

        label = QLabel(
            "grey   -> off\n"
            "green -> on         "
            "cyan -> limited by"
        )

        label.setStyleSheet(
            "color:white"
        )

        label.setWordWrap(True)

        layoutoutput.addWidget(label)

        layoutoutput.addStretch()

        self.dropdown.addLayout(
            layoutoutput
        )

        # =========================================================
        # VOLTAGE / CURRENT SET VALUES
        # =========================================================

        layoutset = QHBoxLayout()

        self.voltwidget = QLineEdit()

        self.voltwidget.setMaxLength(7)

        self.voltwidget.setFixedWidth(
            self.app.standard_width
        )

        self.voltwidget.setText(
            str(np.round(self.voltage, 3))
        )

        if self.connected:

            self.voltwidget.setStyleSheet(
                "background-color: lightGray"
            )

            self.voltwidget.returnPressed.connect(
                self.setvoltage_confirmed
            )

        else:

            self.voltwidget.setStyleSheet(
                "background-color: red"
            )

            self.voltwidget.returnPressed.connect(
                self.dummy_func
            )

        self.voltwidget.textEdited.connect(
            self.setvoltage_edited
        )

        label = QLabel(
            "voltage (V)"
        )

        label.setStyleSheet(
            "color:white"
        )

        layoutset.addWidget(
            self.voltwidget
        )

        layoutset.addWidget(
            label
        )

        layoutset.addStretch()

        # =========================================================
        # CURRENT SET VALUE
        # =========================================================

        self.currentwidget = QLineEdit()

        self.currentwidget.setMaxLength(7)

        self.currentwidget.setFixedWidth(
            self.app.standard_width
        )

        self.currentwidget.setText(
            str(np.round(self.current, 1))
        )

        self.currentwidget.textEdited.connect(
            self.setcurrent_edited
        )

        if self.connected:

            self.currentwidget.setStyleSheet(
                "background-color: lightGray"
            )

            self.currentwidget.returnPressed.connect(
                self.setcurrent_confirmed
            )

        else:

            self.currentwidget.setStyleSheet(
                "background-color: red"
            )

            self.currentwidget.returnPressed.connect(
                self.dummy_func
            )

        label = QLabel(
            "current (mA)"
        )

        label.setStyleSheet(
            "color:white"
        )

        layoutset.addWidget(
            label
        )

        layoutset.addWidget(
            self.currentwidget
        )

        self.dropdown.addLayout(
            layoutset
        )

        # =========================================================
        # INFORMATION
        # =========================================================

        layoutinfo = QHBoxLayout()

        layoutinfo.addStretch()

        label = QLabel(
            "(if Output is on, confirm changes with enter)"
        )

        label.setStyleSheet(
            "color:white"
        )

        layoutinfo.addWidget(label)

        layoutinfo.addStretch()

        self.dropdown.addLayout(
            layoutinfo
        )

        # =========================================================
        # SAFETY / UPDATE VALUES
        # =========================================================

        layoutsafe = QHBoxLayout()

        btn = self.app.normal_button(
            layoutsafe,
            "Safety limits",
            self.set_safety
        )

        btn.setFixedWidth(110)

        layoutsafe.addStretch()

        if self.connected:

            btn = self.app.normal_button(
                layoutsafe,
                "Update Set Values",
                self.set_values
            )

        else:

            btn = self.app.normal_button(
                layoutsafe,
                "Update Set Values",
                self.dummy_func
            )

            btn.setStyleSheet(
                "background-color: red"
            )

        btn.setFixedWidth(110)

        self.dropdown.addLayout(
            layoutsafe
        )

        layoutright.addLayout(
            self.dropdown
        )

        self.app.set_layout_visible(
            self.dropdown,
            False
        )

        layoutright.addItem(
            self.app.vspace
        )

    # =============================================================
    # UPDATE KEYSIGHT SET VALUES
    # =============================================================

    def set_values(self):

        self.output_on = bool(
            np.double(
                self.psu.query("OUTP?").strip()
            )
        )

        # Keysight returns A.
        # self.current is stored as mA.

        self.current = (
            np.double(
                self.psu.query("SOUR:CURR?").strip()
            )
        )

        self.voltage = np.double(
            self.psu.query("SOUR:VOLT?").strip()
        )

        self.voltwidget.setText(
            str(np.round(self.voltage, 3))
        )

        self.currentwidget.setText(
            str(np.round(self.current * 1000, 1))
        )

        # Keep original behavior:
        # after querying SOUR:CURR?, convert to mA.

        self.current *= 1000

        if self.output_on:

            self.powerbtn.setStyleSheet(
                "background-color: green;color: black"
            )

        else:

            self.powerbtn.setStyleSheet(
                "background-color: lightGray;color: black"
            )

    # =============================================================
    # SAFETY SETTINGS
    # =============================================================

    def set_safety(self):

        text = (
            "Set safety limits to the output "
            "of the electric power supply"
        )

        defaultlist = [
            self.max_voltage,
            self.max_currentmA,
            self.max_powermW
        ]

        labellist = [
            "Voltage (V)",
            "Current (mA)",
            "Power (mW)"
        ]

        self.window = self.app.entrymask3(
            self.app,
            "safety",
            defaultlist,
            labellist,
            text
        )

        self.window.location_on_the_screen()

        self.window.show()

    # =============================================================
    # TIMELINE GUI
    # =============================================================

    def timeline_ui(self, layoutright):

        self.expanded2 = False

        self.app.heading_label(
            layoutright,
            "Timeline / I-V-Curve",
            self.expand2
        )

        self.dropdown2 = QVBoxLayout()

        layoutIVor = QHBoxLayout()

        layoutIVor.addStretch()

        self.btntimelineshow = (
            self.app.normal_button(
                layoutIVor,
                "Timeline",
                self.show_timline
            )
        )

        self.btntimelineshow.setFixedWidth(70)

        self.btntimelineshow.setStyleSheet(
            "background-color: green"
        )

        layoutIVor.addStretch()

        label = QLabel(
            "<- Show -> "
        )

        label.setStyleSheet(
            "color:white"
        )

        layoutIVor.addWidget(label)

        layoutIVor.addStretch()

        self.btnIVshow = (
            self.app.normal_button(
                layoutIVor,
                "I-V-Curve",
                self.show_IV
            )
        )

        self.btnIVshow.setFixedWidth(70)

        layoutIVor.addStretch()

        self.dropdown2.addLayout(
            layoutIVor
        )

        # =========================================================
        # REFRESH RATE
        # =========================================================

        layoutfresh = QHBoxLayout()

        freshwidget = QLineEdit()

        freshwidget.setStyleSheet(
            "background-color: lightGray"
        )

        freshwidget.setMaxLength(7)

        freshwidget.setFixedWidth(
            self.app.standard_width
        )

        freshwidget.setText(
            str(self.refresh_rate)
        )

        freshwidget.textEdited.connect(
            self.refreshrate_edited
        )

        label = QLabel(
            "refresh interval (s)"
        )

        label.setStyleSheet(
            "color:white"
        )

        layoutfresh.addWidget(
            freshwidget
        )

        layoutfresh.addWidget(
            label
        )

        layoutfresh.addStretch()

        if self.connected:

            self.btnlive = (
                self.app.normal_button(
                    layoutfresh,
                    "Status Live",
                    self.live_mode
                )
            )

        else:

            self.btnlive = (
                self.app.normal_button(
                    layoutfresh,
                    "Status Live",
                    self.dummy_func
                )
            )

            self.btnlive.setStyleSheet(
                "background-color: red"
            )

        self.dropdown2.addLayout(
            layoutfresh
        )

        # =========================================================
        # TIMELINE BUTTONS
        # =========================================================

        layouttimeline = QHBoxLayout()

        btn = self.app.normal_button(
            layouttimeline,
            "Reset Timeline",
            self.reset_pressed
        )

        btn.setFixedWidth(110)

        layouttimeline.addStretch()

        btn = self.app.normal_button(
            layouttimeline,
            "Save Timeline",
            self.app.h5saving.save_to_h5_timeline
        )

        btn.setFixedWidth(110)

        self.dropdown2.addLayout(
            layouttimeline
        )

        # =========================================================
        # MAXIMIZE
        # =========================================================

        layoutmax = QHBoxLayout()

        self.maxbtn = (
            self.app.normal_button(
                layoutmax,
                "Maximize View",
                self.maximize
            )
        )

        self.maxbtn.setFixedWidth(110)

        layoutmax.addStretch()

        self.dropdown2.addLayout(
            layoutmax
        )

        layoutright.addLayout(
            self.dropdown2
        )

        self.app.set_layout_visible(
            self.dropdown2,
            False
        )

        layoutright.addItem(
            self.app.vspace
        )

        # =========================================================
        # START LIVE MODE
        # =========================================================

        self.live_mode_running = False

        if self.connected and self.hp34401a_connected:

            self.live_mode()

        elif self.connected and not self.hp34401a_connected:

            self.app.add_log(
                "Live current measurement unavailable: "
                "HP 34401A not connected"
            )


    # =============================================================
    # RESET TIMELINE
    # =============================================================

    def reset_pressed(self):

        self.timeline_reset_pressed = True

    # =============================================================
    # SHOW IV
    # =============================================================

    def show_IV(self):

        self.btntimelineshow.setStyleSheet(
            "background-color: lightGray"
        )

        self.btnIVshow.setStyleSheet(
            "background-color: green"
        )

        self.pw.setHidden(True)

        self.pw2.setHidden(False)

    # =============================================================
    # SHOW TIMELINE
    # =============================================================

    def show_timline(self):

        self.btnIVshow.setStyleSheet(
            "background-color: lightGray"
        )

        self.btntimelineshow.setStyleSheet(
            "background-color: green"
        )

        self.pw.setHidden(False)

        self.pw2.setHidden(True)

    # =============================================================
    # UPDATE VIEWS
    # =============================================================

    def updateViews(self):

        self.p2.setGeometry(
            self.p1.vb.sceneBoundingRect()
        )

        self.p2.linkedViewChanged(
            self.p1.vb,
            self.p2.XAxis
        )

    # =============================================================
    # GRAPHICS
    # =============================================================

    def power_graphics_show(self, layout):

        # =========================================================
        # I-V CURVE
        # =========================================================

        self.pw2 = pg.PlotWidget()

        self.pw2.setBackground(None)

        self.pw2.setTitle(
            "I-V-Curve"
        )

        self.pw2.setLabel(
            'bottom',
            'Voltage',
            units='V'
        )

        self.pw2.setLabel(
            'left',
            'Current',
            units='A'
        )

        self.IVcurveplot = pg.PlotCurveItem(
            self.app.scripting.IV_curve_voltages,
            self.app.scripting.IV_curve_currents
        )

        self.pw2.addItem(
            self.IVcurveplot
        )

        layout.addWidget(
            self.pw2
        )

        self.pw2.setHidden(True)

        # =========================================================
        # TIMELINE PLOT
        # =========================================================

        self.pw = pg.PlotWidget()

        self.pw.setTitle(
            "Electric Power Timeline / I-V-Curve"
        )

        self.pw.setBackground(None)

        self.p1 = self.pw.plotItem

        self.p1.setLabel(
            'bottom',
            'time',
            units='s'
        )

        self.p1.setLabel(
            'left',
            'Voltage',
            units='V'
        )

        # =========================================================
        # SECOND VIEWBOX FOR CURRENT
        # =========================================================

        self.p2 = pg.ViewBox()

        self.p1.showAxis(
            'right'
        )

        self.p1.scene().addItem(
            self.p2
        )

        self.p1.getAxis(
            'right'
        ).linkToView(
            self.p2
        )

        self.p2.setXLink(
            self.p1
        )

        self.p1.getAxis(
            'right'
        ).setLabel(
            'Current',
            units="A",
            color="#0fef38"
        )

        self.p1.getAxis(
            "right"
        ).enableAutoSIPrefix(True)

        self.updateViews()

        self.p1.vb.sigResized.connect(
            self.updateViews
        )

        # =========================================================
        # VOLTAGE CURVE
        # =========================================================

        self.Vcurve = pg.PlotCurveItem(
            [0],
            [0]
        )

        self.p1.addItem(
            self.Vcurve
        )

        # =========================================================
        # CURRENT CURVE
        # =========================================================

        self.Acurve = pg.PlotCurveItem(
            [0],
            [0],
            pen="#0fef38"
        )

        self.p2.addItem(
            self.Acurve
        )

        self.p1.setXRange(
            0,
            1
        )

        layout.addWidget(
            self.pw,
            2
        )

    # =============================================================
    # MAXIMIZE
    # =============================================================

    def maximize(self):

        if self.maximized:

            self.maximized = False

            self.app.stage.plot.setHidden(
                False
            )

            self.app.midright.setHidden(
                False
            )

            self.maxbtn.setText(
                "Maximize View"
            )

            self.maxbtn.setStyleSheet(
                "background-color:lightGray;"
            )

        else:

            if (
                self.app.orca.maximized
                or
                self.app.pixis.maximized
            ):

                self.app.add_log(
                    "Minimize corresponding window first"
                )

            else:

                self.maximized = True

                self.app.stage.plot.setHidden(
                    True
                )

                self.app.midright.setHidden(
                    True
                )

                self.maxbtn.setText(
                    "Minimize View"
                )

                self.maxbtn.setStyleSheet(
                    "background-color:cyan;"
                )

