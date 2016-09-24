# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'net_options_dialog.ui'
#
# Created: Tue Sep 20 01:37:39 2016
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_netOptionsDialog(object):
    def setupUi(self, netOptionsDialog, context, state_data):
        self.context = context
        self.netOptionsDialog = netOptionsDialog
        netOptionsDialog.setObjectName(_fromUtf8("netOptionsDialog"))
        netOptionsDialog.resize(352, 179)
        netOptionsDialog.setMinimumSize(QtCore.QSize(352, 179))
        netOptionsDialog.setMaximumSize(QtCore.QSize(352, 179))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/guiIcons/icons/logo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        netOptionsDialog.setWindowIcon(icon)
        netOptionsDialog.setModal(False)
        self.acceptCancelButtons = QtGui.QDialogButtonBox(netOptionsDialog)
        self.acceptCancelButtons.setGeometry(QtCore.QRect(15, 145, 321, 32))
        self.acceptCancelButtons.setOrientation(QtCore.Qt.Horizontal)
        self.acceptCancelButtons.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.acceptCancelButtons.setCenterButtons(True)
        self.acceptCancelButtons.setObjectName(_fromUtf8("acceptCancelButtons"))
        self.localRadio = QtGui.QRadioButton(netOptionsDialog)
        self.localRadio.setGeometry(QtCore.QRect(25, 10, 131, 26))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setKerning(False)
        self.localRadio.setFont(font)
        self.localRadio.setAutoExclusive(True)
        self.localRadio.setObjectName(_fromUtf8("localRadio"))
        self.localRadio.setChecked(True)
        self.remoteScriptGroupBox = QtGui.QGroupBox(netOptionsDialog)
        self.remoteScriptGroupBox.setEnabled(True)
        self.remoteScriptGroupBox.setGeometry(QtCore.QRect(15, 45, 321, 96))
        self.remoteScriptGroupBox.setTitle(_fromUtf8(""))
        self.remoteScriptGroupBox.setObjectName(_fromUtf8("remoteScriptGroupBox"))
        self.remoteRadio = QtGui.QRadioButton(self.remoteScriptGroupBox)
        self.remoteRadio.setEnabled(True)
        self.remoteRadio.setGeometry(QtCore.QRect(10, 5, 121, 21))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("MS Shell Dlg 2"))
        font.setPointSize(10)
        font.setKerning(False)
        font.setStyleStrategy(QtGui.QFont.PreferDefault)
        self.remoteRadio.setFont(font)
        self.remoteRadio.setMouseTracking(False)
        self.remoteRadio.setStatusTip(_fromUtf8(""))
        self.remoteRadio.setAutoExclusive(False)
        self.remoteRadio.setObjectName(_fromUtf8("remoteRadio"))
        self.remoteRadio.setChecked(False)
        self.RSGB_ipHostnameLabel = QtGui.QLabel(self.remoteScriptGroupBox)
        self.RSGB_ipHostnameLabel.setEnabled(True)
        self.RSGB_ipHostnameLabel.setGeometry(QtCore.QRect(18, 30, 101, 26))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.RSGB_ipHostnameLabel.setFont(font)
        self.RSGB_ipHostnameLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.RSGB_ipHostnameLabel.setObjectName(_fromUtf8("RSGB_ipHostnameLabel"))
        self.RSGB_ipHostnameLabel.setDisabled(True)
        self.RSGB_portLabel = QtGui.QLabel(self.remoteScriptGroupBox)
        self.RSGB_portLabel.setGeometry(QtCore.QRect(70, 60, 46, 26))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.RSGB_portLabel.setFont(font)
        self.RSGB_portLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.RSGB_portLabel.setObjectName(_fromUtf8("RSGB_portLabel"))
        self.RSGB_portLabel.setDisabled(True)
        self.RSGB_ipHostnameTextbox = QtGui.QLineEdit(self.remoteScriptGroupBox)
        self.RSGB_ipHostnameTextbox.setGeometry(QtCore.QRect(122, 32, 200, 20))
        self.RSGB_ipHostnameTextbox.setObjectName(_fromUtf8("RSGB_ipHostnameTextbox"))
        self.RSGB_ipHostnameTextbox.setDisabled(True)
        self.RSGB_portTextbox = QtGui.QLineEdit(self.remoteScriptGroupBox)
        self.RSGB_portTextbox.setGeometry(QtCore.QRect(122, 62, 61, 20))
        self.RSGB_portTextbox.setObjectName(_fromUtf8("RSGB_portTextbox"))
        self.RSGB_portTextbox.setDisabled(True)
        self.RSGB_ipHostnameLabel.setBuddy(self.RSGB_ipHostnameTextbox)
        self.RSGB_portLabel.setBuddy(self.RSGB_portTextbox)
        
        self.loadState(state_data)
        
        self.retranslateUi(netOptionsDialog)
        ##Connections##
        QtCore.QObject.connect(self.acceptCancelButtons, QtCore.SIGNAL(_fromUtf8("accepted()")), self.accept)
        QtCore.QObject.connect(self.acceptCancelButtons, QtCore.SIGNAL(_fromUtf8("rejected()")), netOptionsDialog.reject)
        QtCore.QObject.connect(self.localRadio, QtCore.SIGNAL(_fromUtf8("released()")), self.radioToggle)
        QtCore.QObject.connect(self.remoteRadio, QtCore.SIGNAL(_fromUtf8("released()")), self.radioToggle)
        QtCore.QMetaObject.connectSlotsByName(netOptionsDialog)
        ##Tab Order##
        netOptionsDialog.setTabOrder(self.localRadio, self.remoteRadio)
        netOptionsDialog.setTabOrder(self.remoteRadio, self.RSGB_ipHostnameTextbox)
        netOptionsDialog.setTabOrder(self.RSGB_ipHostnameTextbox, self.RSGB_portTextbox)
        netOptionsDialog.setTabOrder(self.RSGB_portTextbox, self.acceptCancelButtons)

    def loadState(self, state_data):
        self.radioToggle(int(state_data["state"]))
        self.RSGB_ipHostnameTextbox.setText(state_data["address"])
        self.RSGB_portTextbox.setText(str(state_data["port"]))
        
    
    def radioToggle(self, state=None):
        element = self.context.context.MainWindow.sender()
        
        if state == None:
            state = element.isChecked()
        else:
            self.localRadio.setChecked(state)
        
        if element == self.remoteRadio:
            self.localRadio.setChecked(state^1)
        else:
            self.remoteRadio.setChecked(state^1)
            state = 1^state
        
        self.RSGB_ipHostnameLabel.setEnabled(state)
        self.RSGB_ipHostnameTextbox.setEnabled(state)
        self.RSGB_portLabel.setEnabled(state)
        self.RSGB_portTextbox.setEnabled(state)
    
    def accept(self):
        net_options = {}
        net_options["state"] = self.localRadio.isChecked()
        net_options["address"] = self.RSGB_ipHostnameTextbox.text()
        net_options["port"] = self.RSGB_portTextbox.text()
        self.context.context.MainWindow.emit(QtCore.SIGNAL("updateNetworkOptions"), net_options)
        self.netOptionsDialog.accept()

    def retranslateUi(self, netOptionsDialog):
        netOptionsDialog.setWindowTitle(_translate("netOptionsDialog", "Network Options", None))
        self.localRadio.setToolTip(_translate("netOptionsDialog", "Connect to a locally running SCCwatcher script.", None))
        self.localRadio.setText(_translate("netOptionsDialog", "Local Script", None))
        self.remoteRadio.setToolTip(_translate("netOptionsDialog", "Connect to an SCCwatcher script on a remote computer.", None))
        self.remoteRadio.setText(_translate("netOptionsDialog", "Remote Script", None))
        self.RSGB_ipHostnameLabel.setToolTip(_translate("netOptionsDialog", "IP or hostname of the remote computer where the SCCwatcher script is running.", None))
        self.RSGB_ipHostnameLabel.setText(_translate("netOptionsDialog", "IP/Hostname: ", None))
        self.RSGB_portLabel.setToolTip(_translate("netOptionsDialog", "Port number of the remote computer where the SCCwatcher script is running.", None))
        self.RSGB_portLabel.setText(_translate("netOptionsDialog", "Port:", None))
        self.RSGB_ipHostnameTextbox.setToolTip(_translate("netOptionsDialog", "IP or hostname of the remote computer where the SCCwatcher script is running.", None))
        self.RSGB_portTextbox.setToolTip(_translate("netOptionsDialog", "Port number of the remote computer where the SCCwatcher script is running.", None))

import icon_resources_rc
