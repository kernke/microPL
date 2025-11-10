import sys
from PyQt5.QtWidgets import QApplication
import MicroPL as MPL

# Check if an application instance already exists
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# Create and show your main window
window = MPL.MainWindow()
window.show()

# Start the Qt event loop
sys.exit(app.exec_())