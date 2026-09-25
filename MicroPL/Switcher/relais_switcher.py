import serial
import time

# documentation / description
# the button to control the switcher are actually in the Keysight class (power supply)

class Switcher:
    """Python interface for the ESP32 relay switch."""

    VALID_COMMANDS = {
        "Kennlin",
        "Impedanz",
        "Positiv",
        "Negativ",
        "Aus",
    }

    def __init__(self, app):
        self.app=app
        self.port = "COM21"
        self.baudrate = 115200
        self.timeout = 1
        self.ser = None
        self.connected=False
        try:
            self.connect()
            print("switcher connected")
            self.connected=True

            self.set_IVcurve_mode(initialization=True)
            self.set_off(initialization=True)
            #self.mode="IV"
            #self.mode_state="off"

        except serial.SerialException:
            print("switcher dummy mode")
            self.app.add_log("Switcher dummy mode")
 
    def connect(self):
        """Open the serial connection."""
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout
        )
        # Wait for the ESP32 to reboot after opening the port
        time.sleep(2)

        # Read the startup message
        while self.ser.in_waiting:
            line_for_print=self.ser.readline().decode(errors="ignore").strip()
        #    print(line_for_print)
        self.app.add_log("Switcher connected")

    def disconnect(self):
        """Close the serial connection."""
        if self.ser is not None and self.ser.is_open:
            self.ser.close()

    def set_IVcurve_mode(self,initialization=False):
        command="Kennlin"
        self.send_command(command)
        self.mode="IV"
        if not initialization:
            self.app.keysight.btn_IVmode.setStyleSheet("background-color: green") 
            self.app.keysight.btn_LCRmode.setStyleSheet("background-color: lightGray")   
            self.app.add_log("Power supply mode")
        time.sleep(0.3)

    def set_LCR_mode(self):
        #self.set_off()
        command="Impedanz"
        self.send_command(command)
        self.mode="LCR"
        self.app.keysight.btn_LCRmode.setStyleSheet("background-color: green")
        self.app.keysight.btn_IVmode.setStyleSheet("background-color: lightGray")   
        self.app.add_log("SMU mode")
        time.sleep(0.3)


    def set_positive(self):
        command="Positiv"
        self.send_command(command)
        self.mode_state="positive"
        self.app.keysight.btn_positive.setStyleSheet("background-color: green")   
        self.app.keysight.btn_negative.setStyleSheet("background-color: lightGray")   
        self.app.keysight.btn_off.setStyleSheet("background-color: lightGray")   
        time.sleep(0.3)



    def set_negative(self):
        command="Negativ"
        self.send_command(command)
        self.mode_state="negative"
        self.app.keysight.btn_positive.setStyleSheet("background-color: lightGray")   
        self.app.keysight.btn_negative.setStyleSheet("background-color: green")   
        self.app.keysight.btn_off.setStyleSheet("background-color: lightGray")   
        time.sleep(0.3)
        
    def set_off(self,initialization=False):
        command="Aus"
        self.send_command(command)
        self.mode_state="off"
        if not initialization:
            self.app.keysight.btn_positive.setStyleSheet("background-color: lightGray")   
            self.app.keysight.btn_negative.setStyleSheet("background-color: lightGray")   
            self.app.keysight.btn_off.setStyleSheet("background-color: green")   
        time.sleep(0.3)            


    def send_command(self, command):
        """
        Send a command to the ESP32.

        Valid commands:
            Kennlin
            Impedanz
            Positiv
            Negativ
            Aus
        """
        if command not in self.VALID_COMMANDS:
            raise ValueError(
                f"Unknown command '{command}'. "
                f"Valid commands are: {', '.join(self.VALID_COMMANDS)}"
            )

        if self.ser is None or not self.ser.is_open:
            raise RuntimeError("Not connected to the device.")

        self.ser.write((command + "\n").encode("utf-8"))
        self.ser.flush()

        # Read all response lines
        time.sleep(0.1)

        responses = []
        while self.ser.in_waiting:
            responses.append(
                self.ser.readline().decode(errors="ignore").strip()
            )

        #print(responses)
        
