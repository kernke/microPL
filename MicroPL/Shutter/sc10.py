import serial
import time
import re


class ThorlabsSC10:

    def __init__(self, app):
        self.app=app
        self.connected=False
        self.state="closed"
        try:
            self.connect()
            self.app.add_log("Shutter connected")
            print("shutter connected")
            self.connected=True
        except serial.SerialException:
            print("shutter dummy mode")
            self.app.add_log("Shutter dummy mode")

    def connect(self):
        self.port="COM11"
        self.ser = serial.Serial(
            port=self.port,
            baudrate=9600,
            bytesize=8,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )

        time.sleep(0.3)

        self.command("mode=1")

        mode = self.command("mode?")
        if not re.search(r"\b1\b", mode):
            raise RuntimeError("SC10 is not in Manual mode")


    def command(self, cmd):
        self.ser.reset_input_buffer()
        self.ser.write((cmd + "\r").encode("ascii"))
        self.ser.flush()

        response = self.ser.read_until(b">")
        return response.decode("ascii", errors="replace")

    def get_status(self):
        response = self.command("ens?")

        # Extract the returned enable state
        response = response.replace("ens?", "")
        response = response.replace(">", "")

        values = re.findall(r"(?<!\d)[01](?!\d)", response)

        if not values:
            raise RuntimeError(
                f"Cannot read SC10 status: {response!r}"
            )

        return int(values[-1])

    def change_state(self):
        if self.state=="open":
            self.close()
            self.app.monochromator.btn_shutter.setStyleSheet("background-color: lightGray")
            self.app.monochromator.btn_shutter.setText("Closed")
        else:
            self.open()
            self.app.monochromator.btn_shutter.setStyleSheet("background-color: green")   
            self.app.monochromator.btn_shutter.setText("Open")

    def open(self):
        if self.get_status() == 0:
            self.command("ens")
            time.sleep(0.1)
        self.state="open"
        self.app.add_log("Shutter OPEN")

    def close(self):
        if self.get_status() == 1:
            self.command("ens")
            time.sleep(0.1)
        self.state="closed"
        self.app.add_log("Shutter CLOSED")

    def expose(self, duration):
        self.open()
        time.sleep(duration)
        self.close()

    def close_connection(self):
        self.ser.close()
        print('Shutter Disconnected')



