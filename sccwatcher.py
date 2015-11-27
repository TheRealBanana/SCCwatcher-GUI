## SCCwatcher 2.0         ##
##                        ##
## sccwatcher.py          ##
##                        ##
## Everything starts here ##
############################

import sys
from settings_ui import *
from PyQt4 import QtGui, QtCore

#This is required to override the closeEvent
class SCCMainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(SCCMainWindow, self).__init__(parent)
        self._user_accept_close = False

    def closeEvent(self, event):
        #We first emit the closing signal, then we actually close
        self.emit(QtCore.SIGNAL("appClosing"))
        if self._user_accept_close is True:
            super(SCCMainWindow, self).closeEvent(event)
        else:
            event.ignore()

def main():
    app = QtGui.QApplication(sys.argv)
    Window = SCCMainWindow()
    ui = Ui_sccw_SettingsUI()
    ui.setupUi(Window)
    Window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
