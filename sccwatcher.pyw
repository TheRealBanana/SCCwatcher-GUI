#!/bin/env python2.7
## SCCwatcher 2.0         ##
##                        ##
## sccwatcher.py          ##
##                        ##
## Everything starts here ##
############################

import sys
import re
from settings_ui import *
from PyQt4 import QtGui, QtCore

#This is required to override the closeEvent
class SCCMainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(SCCMainWindow, self).__init__(parent)
        self._user_accept_close = False
        self.setAcceptDrops(True)
        self.ui = None

    def closeEvent(self, event):
        #We first emit the closing signal, then we actually close
        self.emit(QtCore.SIGNAL("appClosing"))
        if self._user_accept_close is True:
            super(SCCMainWindow, self).closeEvent(event)
        else:
            event.ignore()
    
    def dropEvent(self, event):
        #Got a file drop!
        filepath = str(event.mimeData().urls()[0].path())
        #Check if we have a windows path and remove the prepended forward slash if necessary
        if re.search("^/[a-zA-Z]:", filepath):
            #Technically, because of the regex we should already know index 0 is a forward slash, but meh can't hurt.
            if filepath[0] == "/":
                filepath = filepath[1:]
        #Now we emit a signal so our main app can handle it
        self.emit(QtCore.SIGNAL("gotFileDrop"), filepath)
        
    def dragEnterEvent(self, event):
        #We don't relly need to do any checks here for file type since the loader function does it all for us.
        event.acceptProposedAction()

def main():
    app = QtGui.QApplication(sys.argv)
    Window = SCCMainWindow()
    #Window.setAcceptDrops(True)
    ui = Ui_sccw_SettingsUI()
    Window.ui = ui
    ui.setupUi(Window)
    Window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
