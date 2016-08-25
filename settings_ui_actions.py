#!/usr/bin/env python
# wanted to move all the ui functions into their own file to make everything look nicer
# otherwise the settings_ui.py file was going to get really crowded.
import re
import cPickle
import threading
import socket
from collections import OrderedDict as OD
from numbers import Number
#from collections import namedtuple as NT
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QDir
from PyQt4.QtCore import SIGNAL
from copy import deepcopy as DC
from ntpath import basename as ntpath_basename
from urllib import urlopen
from ast import literal_eval as safe_eval
from tempfile import gettempdir
from os import sep as OS_SEP
from time import sleep, time


try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

#I didnt think this should be included in each guiActions instance
def regexValidator(expr):
    #This function will take in a string, as expr, and determine if it is a valid regular expression
    #Super simple
    try:
        re.compile(expr)
        return True
    except:
        return False



class Client(threading.Thread):
    def __init__(self, guiActionsReference):
        self.quitting = False
        self.recv_tries = 0
        self.connected = False
        self.data_thread = None
        self.waiting = False
        self.SEND_WAIT = 1
        self.last_send = int(time()) - self.SEND_WAIT
        self.CONNECT_WAIT = 5
        self.last_connect_try = int(time()) - self.CONNECT_WAIT
        self.gref = guiActionsReference
        self.MW = self.gref.context.MainWindow
        #Set our connection status to False for now
        self.MW.emit(SIGNAL("gotScriptStatusUpdate"), "None", False)
        self.main_socket = None
        self.DATA_WAIT_TIMEOUT = 1
        super(Client, self).__init__()
    
    
    def quit_thread(self):
        self.quitting = True
        try:
            self.main_socket.send("CONNECTION_CLOSING")
        except:
            pass
        try:
            self.main_socket.close()
        except:
            pass
    
    def get_connection(self):
        while self.connected is False and self.quitting is False:
            
            if int(time()) - self.last_connect_try > self.CONNECT_WAIT:
                self.last_connect_try = int(time())
                try:
                    portnum = self.gref.get_current_port()
                    if portnum is None:
                        continue
                    self.address = ("127.0.0.1", portnum)
                    self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.main_socket.settimeout(self.DATA_WAIT_TIMEOUT)
                    self.main_socket.connect(self.address)
                    self.connected = True
                    continue
                except:
                    pass
            sleep(0.5)
            
        if self.quitting is True:
            self.connected = False
    
    
    def get_script_status(self):
        if self.connected is True and self.quitting is False:
            try:
                self.main_socket.send("GET_SCRIPT_STATUS")
                self.waiting = True
            except Exception as e:
                if "timed out" not in str(e):
                    self.main_socket.close()
                    self.connected = False
                    self.waiting = False
                    return
                return
        
    def pass_script_cmd(self, cmd):
        if self.connected is True and self.quitting is False and len(cmd) > 0:
            try:
                self.main_socket.send(cmd)
                #Wait for receive confirm
                self.waiting = True
            except Exception as e:
                if "timed out" not in str(e):
                    self.main_socket.close()
                    self.connected = False
                    self.waiting = False
                    return
                
    
    def get_return_data(self):
        if self.connected is True and self.quitting is False and self.recv_tries < 5:
            try:
                rawdata = self.main_socket.recv(8192)
                try:
                    rawdata = rawdata.replace("\\n", "\n")
                    rawdata = rawdata.replace("\\\\", "\\")
                except:
                    self.waiting = False
                    self.recv_tries = 0
                    return None
                try:
                    data = cPickle.loads(rawdata)
                except:
                    return None
                #End our receive operation
                self.waiting = False
                self.recv_tries = 0
                return data
            except Exception as e:
                if "timed out" not in str(e):
                    self.main_socket.close()
                    self.connected = False
                    self.waiting = False
                    return
            self.recv_tries += 1
            return None
        else:
            self.waiting = False #Too many tries, we disconnected, or caught the quit signal.
            self.recv_tries = 0
            return None
    
    
    def run(self):
        while self.quitting is False:
            sleep(0.2) #Limit how fast we run this loop
            
            #Check connection, try to get it back if we lost it
            if self.connected is False:
                #Update our status to disconnected:
                self.MW.emit(SIGNAL("gotScriptStatusUpdate"), "DISCON", False)
                self.get_connection()
                continue
            
            #Request data
            if self.waiting is False:
                if int(time()) - self.last_send > self.SEND_WAIT: 
                    #data = None
                    #data = self.get_script_status()
                    self.get_script_status()
                    self.last_send = int(time())
                continue
            
            #Waiting for data, lets get it
            if self.waiting is True:
                data = self.get_return_data()
                if data is not None:
                    if data == "CONNECTION_CLOSING":
                        self.main_socket.close()
                        self.connected = False
                        continue
                    if isinstance(data, basestring) is True:
                        continue
                    self.MW.emit(SIGNAL("gotScriptStatusUpdate"), data, True)
                continue
            
            sleep(1) #Can we ever even get here?
        try:
            self.main_socket.close()
        except:
            pass
        return
    

class guiActions(object):
    def __init__(self, context):
        self.context = context
        self.client_thread = None
        #this is different from self.context.SettingsManager.isLoaded.
        #This just flags during the load operation itself and gives no indication as to whether or not something is currently loaded.
        self.__is_loading = False
        self.script_status_vars = self.context.SettingsManager.scriptStatusDefaults

    
    def setLabelAndColor(self, element, status):
        if str(status).lower() == "on":
            stylesheet = "<html><head/><body><p align=\"center\"><span style=\" font-weight:600; color:#00c800;\">On</span></p></body></html>"
        elif str(status).lower() == "off" or str(status).lower() == "Not Running" or str(status).lower() == "n/a":
            stylesheet = "<html><head/><body><p align=\"center\"><span style=\" font-weight:600; color:#ff0000;\">Off</span></p></body></html>"
        else:
            stylesheet = "<html><head/><body><p align=\"center\"><span style=\" font-weight:600; color:#000000;\">%s</span></p></body></html>" % (status)
        
        #Now set the element with its data
        element.setText(stylesheet)
    
    def toggleScriptAutodl(self):
        self.client_thread.pass_script_cmd("TOGGLE_AUTODL")
    
    def reloadScriptIniFile(self):
        self.client_thread.pass_script_cmd("RELOAD_SCRIPT_SETTINGS")
    
    def get_current_port(self):
        tmpname =  gettempdir() + OS_SEP + "sccw_port.txt"
        try:
            tempfile = open(tmpname, 'r')
            portNum = tempfile.read()
            tempfile.close()
            
            if len(portNum) > 1:
                return int(portNum)
            else:
                return None
        except:
            return None
    
    def updateScriptStatusCallback(self, script_status, script_connected=True):
        #Our returned data from the script should be at least the size of our default status
        if isinstance(script_status, dict) is False or len(script_status) < len(self.context.SettingsManager.scriptStatusDefaults):
            script_status = self.context.SettingsManager.scriptStatusDefaults
        
        self.script_status_vars = script_status
        
        #Now we update the main page with our data
        self.setLabelAndColor(self.context.ssVersionState, script_status["version"])
        self.setLabelAndColor(self.context.ssStatusState, script_status["autodlstatus"])
        self.setLabelAndColor(self.context.ssSSLDownloadState, script_status["ssl"])
        self.setLabelAndColor(self.context.ssMaxTriesState, script_status["max_dl_tries"])
        self.setLabelAndColor(self.context.ssRetryDelayState, script_status["retry_wait"])
        self.setLabelAndColor(self.context.ssCloudflareState, script_status["cf_workaround"])
        self.setLabelAndColor(self.context.ssDupecheckingState, script_status["dupecheck"])
        self.setLabelAndColor(self.context.ssLoggingState, script_status["logging"])
        self.setLabelAndColor(self.context.ssVerboseState, script_status["verbose"])
        self.setLabelAndColor(self.context.ssRecentState, script_status["recent_list_size"])
        self.setLabelAndColor(self.context.ssWatchAvoidState, script_status["wl_al_size"])
        
        #And enable or disable our control group if we have a good connection
        if script_connected is True:
            self.context.scButtonFrame.setEnabled(True)
            control_status_html = "<html><head/><body><p><span style=\" color:#00c800;\">Connected</span></p></body></html>"
        else:
            self.context.scButtonFrame.setEnabled(False)
            control_status_html = "<html><head/><body><p><span style=\" color:#ff0000;\">Not Connected</span></p></body></html>"
            
        self.context.sccsConStatusState.setText(_translate("sccw_SettingsUI", control_status_html, None))
    
    def startClientThread(self):
        self.client_thread = Client(self)
        self.client_thread.start()  
    
    def loadActiveIni(self):
        if len(self.script_status_vars["ini_path"]) > 1:
            self.loadUiState(dd_filename=self.script_status_vars["ini_path"])
    
    
    def checkRegexContent(self, pElement, pCheckbox):
        #This is a generic function for each box supporting regular expressions.
        #You can just connect the finishedEditing() signal to this function, using partial to fill in the variables.
        
        pCheckbox_value = pCheckbox.checkState()
        regex = str(pElement.text())
        
        #We only operate if the regex checkbox is active
        if pCheckbox_value > 0:
            if regexValidator(regex) is True:
                #Regular expression checks out, we will set the background back to normal
                pElement.setStyleSheet("QLineEdit { background: rgb(255, 255, 255); }")
            else:
                #invalid regex, set the background to orange to indicate the error
                pElement.setStyleSheet("QLineEdit { background: rgb(255, 100, 0); }")
        else:
            #Set the background to normal, just in-case it was set before
            pElement.setStyleSheet("QLineEdit { background: rgb(255, 255, 255); }")
    
    def get_multi(self, sizedetail):
        sizedetail = str(sizedetail).upper()
        if sizedetail == "KB":
            multi=int(1024)
        elif sizedetail == "MB":
            multi=int(1048576)
        elif sizedetail == "GB":
            multi=int(1073741824)
        else:
            multi = int(1)
        return multi
    
    def checkSizeLimitBounds(self, tab):
        #tab should be either gen or wlist
        #this function will make sure the upper and lower are within bounds of each other.
        ul_set = {}
        ul_set["gen"] = {}
        ul_set["gen"]["lower"] = [self.context.globalSizeLimitLowerTextbox, self.context.globalSizeLimitLowerSuffixSelector]
        ul_set["gen"]["upper"] = [self.context.globalSizeLimitUpperTextbox, self.context.globalSizeLimitUpperSuffixSelector]
        ul_set["wlist"] = {}
        ul_set["wlist"]["lower"] = [self.context.WLSGsizeLimitLowerTextbox, self.context.WLSGsizeLimitLowerSuffixSelector]
        ul_set["wlist"]["upper"] = [self.context.WLSGsizeLimitUpperTextbox, self.context.WLSGsizeLimitUpperSuffixSelector]
        
        #Reset to plain white first off, we only want to change color when we know for sure the numbers dont match.
        ul_set[tab]["lower"][0].setStyleSheet("QLineEdit { background: rgb(255, 255, 255); }")
        ul_set[tab]["upper"][0].setStyleSheet("QLineEdit { background: rgb(255, 255, 255); }")
        
        #Sanity checks, we dont want to do anything unless both boxes have integers in them       
        try:
            int(ul_set[tab]["lower"][0].text())
            int(ul_set[tab]["upper"][0].text())
        except:
            return
        
        #First thing we need to do is convert both the upper and lower numbers to bytes
        upper_multi = self.get_multi(self.convertIndex(ul_set[tab]["upper"][1].currentIndex()))
        lower_multi = self.get_multi(self.convertIndex(ul_set[tab]["lower"][1].currentIndex()))
        upper_size_bytes = int(ul_set[tab]["upper"][0].text()) * upper_multi
        lower_size_bytes = int(ul_set[tab]["lower"][0].text()) * lower_multi

        #Now its a simple compare to see which is bigger
        if upper_size_bytes < lower_size_bytes:
            #We got a prob, change the background so we know
            ul_set[tab]["lower"][0].setStyleSheet("QLineEdit { background: rgb(255, 100, 0); }")
            ul_set[tab]["upper"][0].setStyleSheet("QLineEdit { background: rgb(255, 100, 0); }")
        
    
    
    def updateUiTitle(self, text):
        text = "SCCwatcher - %s" % (text)
        self.context.MainWindow.setWindowTitle(_translate("MainWindow", text, None))
    
    def newSettingsFile(self):
        #Start fresh, make sure the user is ok with that
        has_changed, rtn = self.checkUiStateChange()
        #If there were changes, check how the user wanted us to proceed
        if has_changed is True:
            if rtn == QtGui.QMessageBox.Save:
                if self.saveUiToFile() is False:
                    return False
            elif rtn == QtGui.QMessageBox.Discard:
                pass
            elif rtn == QtGui.QMessageBox.Cancel:
                return False
        
        #Now we clear the UI
        self.clearGUIState()
        
        #Just for some other logic stuffs
        return True
    
    def clearGUIState(self):
        self.clearUiData(self.context.SettingsManager.guiDefaults["allOtherDefaults"])
        self.clearUiData(self.context.SettingsManager.guiDefaults["watchlistDefaults"])
        self.clearUiData(self.context.SettingsManager.guiDefaults["avoidlistDefaults"])
        #Remove any watches or avoids
        self.clearList(self.context.WLGwatchlistItemsList)
        self.clearList(self.context.avoidlistItemsList)
        #Reset internal state tracking
        self.context.SettingsManager.guiState["globalOptionsState"] = DC(self.context.SettingsManager.guiDefaults["allOtherDefaults"])
        self.context.SettingsManager.guiState["watchlistState"] = OD()
        self.context.SettingsManager.guiState["avoidlistState"] = OD()
        #Close the current file completely
        self.context.SettingsManager.closeSettingsFile()
        #Clear redo/undo stacks
        self.context.undoRedoSystem.reset()
        
        #Now set the title
        self.updateUiTitle("New Settings File")
        #and finally set the UI state to fresh
        self.updateUiStateInfo()
        
    
    
        
    def checkListChanges(self, list_object, check_dict):
        #This function will take a watchlist object as list_object and compare its items against the data stored in check_dict
        if len(check_dict) == list_object.count():
            #Ok well at least the size matches, now onto the rest
            #Now loop over the items in the list_object and check for differences one by one. (is there a better way?)
            for cur_index in xrange(0, list_object.count()):
                cur_item = list_object.item(cur_index)
                if cur_item == 0: #Could this cause sccwatcher to think a file has no changes when it does, or vice versa, because an item was skipped?
                    continue
                cur_item_title = str(cur_item.text())
                #Do a check to see if the title is in our saved data.
                #If not, we know something has changed and we can quit right now
                if cur_item_title not in check_dict.keys():
                    return True
                #So this name exists in the check_dict dict, we have to check every option now.
                cur_item_data = cur_item.data(Qt.UserRole).toPyObject()
                for cid_option, cid_value in cur_item_data.iteritems():
                    try:
                        check_dict[cur_item_title][cid_option]
                    except:
                        if cid_value != "" and cid_value != 0 and str(cid_value) != "0":
                            return True
                    if str(cid_value) != str(check_dict[cur_item_title][cid_option]):
                        return True
        else:
            #Size is wrong so we know its not the same.
            return True
    
    def checkUiStateChange(self):
        #This function checks to see if the GUI's current state matches the last saved state. If it matches, it returns true. If it doesnt match it returns false.
        is_changed = False
        globalOptions = self.context.SettingsManager.guiState["globalOptionsState"]
        wlOptions = self.context.SettingsManager.guiState["watchlistState"]
        alOptions = self.context.SettingsManager.guiState["avoidlistState"]
        watchlist = self.context.WLGwatchlistItemsList
        avoidlist = self.context.avoidlistItemsList
        
        
        #First we do the easy stuff, all the global options
        for element, old_data in globalOptions.iteritems():
            live_element = eval("self.context." + str(element))
            element_data = self.typeMatcher(live_element, "READ")()
            if old_data != element_data:
                is_changed = True
                break
            
        #Now the more complex bits, we check the watchlist and avoidlist here.
        if is_changed is False:
            if self.checkListChanges(avoidlist, alOptions) is True or self.checkListChanges(watchlist, wlOptions) is True:
                is_changed = True
                    
        if is_changed is True:
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "SCCwatcher", "There are unsaved changes to the current file.", QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
            #msgBox.setTitle("")
            msgBox.setWindowIcon(self.context.icon)
            msgBox.setInformativeText("Do you want to save these changes?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtGui.QMessageBox.Save)
            rtn = msgBox.exec_()
            return [True, rtn]
        else:
            return [False, None]
        
    def updateUiStateInfo(self):
        #This function will loop through all the GUI options, saving the state of all objects.
        #This will allow us to detect whether or not a user has changed anything in the program since the last save/load operation
        
        #Was worried that somehow there would still be an active ref to the old state info so I decided to del() it first
        del(self.context.SettingsManager.guiState["watchlistState"])
        del(self.context.SettingsManager.guiState["avoidlistState"])
        
        wlOptions = OD()
        alOptions = OD()
        
        self.context.SettingsManager.guiState["watchlistState"] = wlOptions
        self.context.SettingsManager.guiState["avoidlistState"] = alOptions
        watchlist = self.context.WLGwatchlistItemsList
        avoidlist = self.context.avoidlistItemsList
        
        globalOptions = self.context.SettingsManager.guiState["globalOptionsState"]
        
        #Global options
        for element, old_data in globalOptions.iteritems():
            #First turn the element live so we can check it
            live_element = eval("self.context." + str(element))
            #Now get the elements current state
            element_data = self.typeMatcher(live_element, "READ")()
            globalOptions[element] = element_data
            
        #Watchlist
        for cur_index in xrange(0, watchlist.count()):
            cur_WL_item = watchlist.item(cur_index)
            if cur_WL_item == 0:
                continue
            cur_WL_title = str(cur_WL_item.text())
            cur_WL_data = cur_WL_item.data(Qt.UserRole).toPyObject()
            #Save it
            wlOptions[cur_WL_title] = cur_WL_data
        
        #Avoidlist
        for cur_index in xrange(0, avoidlist.count()):
            cur_AL_item = avoidlist.item(cur_index)
            if cur_AL_item == 0:
                continue
            cur_AL_title = str(cur_AL_item.text())
            cur_AL_data = cur_AL_item.data(Qt.UserRole).toPyObject()
            #Save it
            alOptions[cur_AL_title] = cur_AL_data
    
    def removeWatchListItem(self):
        #This function will remove the currently selected item in the watch list
        self.removeListItem(self.context.WLGwatchlistItemsList)
    
    def removeAvoidListItem(self):
        #This function will remove the currently selected item in the avoid list
        self.removeListItem(self.context.avoidlistItemsList)
    
    #I really don't like repeating myself so I've made a third function here with all the actual code for removing items from watchlists.
    def removeListItem(self, access_object):
        #Get the currently selected item
        current_selection = access_object.currentItem()
        #Save it to undo/redo stack
        self.context.undoRedoSystem.new_undoredo_QListWidget(access_object, current_selection, op="rem")
        #Get the index of the current item
        current_selection_index = access_object.row(current_selection)
        #And now we remove our watch item from the QListWidget. This also removes any temporary data associated with this item at the same time.
        removed_item = access_object.takeItem(current_selection_index)
        del(removed_item) #Sometimes I don't trust the GC, and it can't hurt to be sure.
        #Set focus to whatever item is below us if possible
        if access_object.count() == current_selection_index:
            access_object.setCurrentRow(current_selection_index-1)
        else:
            access_object.setCurrentRow(current_selection_index)

        
    def addWatchListItem(self):
        #This function will add a new list item to the watch list
        #First thing we do is make a copy of the defaults for the watchlist, then populate it with values from the general options
        #I am wondering now whether or not making a new deep copy each time we add a list item is a good idea or not. Might lead to a memory leak. Hopefully the GC is doin its job.
        #Maybe we should instead create the structure once and then update the values as needed, although this has its own issues (like vestigial options, somehow lol, I dunno)
        updated_wl_defaults = DC(self.context.SettingsManager.guiDefaults["watchlistDefaults"])
        updated_wl_defaults["WLSGsavepathTextbox"] = self.context.ggSavepathTextbox.text()
        updated_wl_defaults["WLSGexternalCommandTextbox"] = self.context.extCmdExeLocation.text()
        updated_wl_defaults["WLSGexternalCommandArgsTextbox"] = self.context.extCmdExeArguments.text()
        updated_wl_defaults["WLSGsizeLimitLowerTextbox"] = self.context.globalSizeLimitLowerTextbox.text()
        updated_wl_defaults["WLSGsizeLimitLowerSuffixSelector"] = self.context.globalSizeLimitLowerSuffixSelector.currentIndex()
        updated_wl_defaults["WLSGsizeLimitUpperTextbox"] = self.context.globalSizeLimitUpperTextbox.text()
        updated_wl_defaults["WLSGsizeLimitUpperSuffixSelector"] = self.context.globalSizeLimitUpperSuffixSelector.currentIndex()
        updated_wl_defaults["WLSGenableExternalCmdCheckbox"] = self.context.extCmdMasterEnableCheck.checkState()
        updated_wl_defaults["WLSGdupecheckingCheckbox"] = self.context.globalDupecheckCheck.checkState()
        updated_wl_defaults["WLSGutWebUiCheckox"] = self.context.utwuiMasterEnableTriCheck.checkState()
        updated_wl_defaults["WLSGftpUploadCheckbox"] = self.context.ftpMasterEnableCheck.checkState()
        updated_wl_defaults["WLSGemailCheckbox"] = self.context.emailMasterEnableCheck.checkState()
        
        self.addNewListItem(self.context.WLGwatchlistItemsList, updated_wl_defaults)
    
    def addAvoidListItem(self):
        #This function will add a new list item to the avoid list
        self.addNewListItem(self.context.avoidlistItemsList)
    
    def addNewListItem(self, access_object, list_defaults=None):
        #Temporarily disable sorting
        __sortingEnabled = access_object.isSortingEnabled()
        access_object.setSortingEnabled(False)
        #Create our QListWidgetItem
        item = QtGui.QListWidgetItem()
        #Make sure our untitled entry isnt going to be a duplicate
        item_title = self.checkForDuplicates(access_object, "Untitled Entry")
        #Set its text
        item.setText(_translate("sccw_SettingsUI", item_title, None))
        #Set the default data items if we are a new watchlist item:
        if list_defaults is not None:
            #Set the title
            list_defaults["WLSGwatchNameTextbox"] = item_title
        else:
            #Avoid, we just set the title, everythign else is default
            list_defaults = {"avoidNameTextbox": item_title, "avoidFilterTextbox": "", "avoidFilterRegexCheck": 0}
            
        item.setData(Qt.UserRole, list_defaults)
        #And add the item to the list
        access_object.addItem(item)
        #We reenable sorting, if it was enabled before
        access_object.setSortingEnabled(__sortingEnabled)
        #Set focus to new object
        access_object.setCurrentItem(item)
        #Save the new item to undo/redo stack
        self.context.undoRedoSystem.new_undoredo_QListWidget(access_object, item, op="add")
    
    def checkForDuplicates(self, access_object, item_text, alt_match=None): #I hate adding params as needed
        #This function will look for duplicate entries in the QWidgetList supplied as access_object
        #If any duplicates are detected the item_text has a number appended to it (or has its appended number incremented) and is returned
        
        #First we loop through each entry and see if its item_text matches anything in the watchlist.
        for cur_index in xrange(0, access_object.count()):
            cur_item = access_object.item(cur_index)
            cur_item_text = cur_item.text()
            
            if alt_match is not None:
                    #We make sure the current item isnt the one supplied by alt_match
                    if cur_item == alt_match: continue
            
            #Check if the titles match
            if cur_item_text == item_text:
                #Ok we got a duplicate. Lets see if this dupe has a number appended or not
                num_reg = re.match("^(.*?)\s\(([0-9]{1,3})\)$", cur_item_text)
                if num_reg is not None:
                    #This dupe does have a number already. We'll get the number, increment it by one, and put it back.
                    num_end = int(num_reg.group(2)) + 1
                    new_title = "%s (%s)" % (num_reg.group(1), num_end)
                else:
                    #Ok there is no number ending, now we just append a number.
                    new_title = "%s (1)" % (item_text)
                #Finally, we recurse to be sure this new title isnt also a dupe.
                final_return = self.checkForDuplicates(access_object, new_title)
                return final_return
        #No titles matched so we don't have a dupe. We return the correct item_text to confirm this.
        return item_text
    
    
    #Update functions for when anything is changed for a watchlist or avoidlist item.
    #These two functions save all the data for the item, not just the piece of data that has changed.
    def saveAllAvoidlistItems(self):
        self.saveAllListItems(self.context.avoidlistItemsList, self.context.avoidNameTextbox, self.context.avoidListElements, self.context.SettingsManager.guiDefaults["avoidlistDefaults"])
    
    def saveAllWatchlistItems(self):
        self.saveAllListItems(self.context.WLGwatchlistItemsList, self.context.WLSGwatchNameTextbox, self.context.watchListElements, self.context.SettingsManager.guiDefaults["watchlistDefaults"])
        
    
    def saveAllListItems(self, access_object, item_title_object, elements_list, defaults):
        #Don't operate during a load operation
        if self.__is_loading is True:
            return
        
        #Get the current list item
        current_list_item = access_object.currentItem()
        if current_list_item is None:
            return
        
        #First thing we do is make sure the title isnt a dupe.
        #We run the title through a dupe checker and return a new title if necessary
        cur_title = current_list_item.text() #I thought about using the item_title_object to get the title, but this is nicer.
        cur_title = self.checkForDuplicates(access_object, cur_title, current_list_item)
        #Now we set the returned title. If it wasnt a dupe it should be the same as before.
        current_list_item.setText(cur_title)
        #And update the textbox with the title in it
        item_title_object.setText(cur_title)
        
        #Now call the saveListData() function with the avoidlist elements and objects passed
        self.saveListData(elements_list, current_list_item, defaults)

    #These Three functions save the data associated with each watch or avoid item whenever the user switches watch items.
    #The third is the master function while the other two just provide unique data tot he master.
    def updateCurrentAvoidListSelection(self, new_listwidget_item, previous_listwidget_item):
        self.updateCurrentListSelection(new_listwidget_item, previous_listwidget_item, self.context.avoidListElements, self.context.SettingsManager.guiDefaults["avoidlistDefaults"], self.context.avoidlistSettingsGroup)
        
    def updateCurrentWatchListSelection(self, new_listwidget_item, previous_listwidget_item):
        self.updateCurrentListSelection(new_listwidget_item, previous_listwidget_item, self.context.watchListElements, self.context.SettingsManager.guiDefaults["watchlistDefaults"], self.context.watchlistSettingsGroup)
    
    def updateCurrentListSelection(self, new_listwidget_item, previous_listwidget_item, listwidget_elements, reset_data, opgrp_access_object):
        #Set the load var so nothing crappy happens
        self.__is_loading = True
        
        #Save data
        #If things go south here, its probably because its an Untitled entry or theres no entry at all.
        #We still want to reset though so we allow it to pass even if it fails
        if previous_listwidget_item is not None:
            self.saveListData(listwidget_elements, previous_listwidget_item, reset_data)

        #reset listwidget
        self.clearUiData(reset_data)
        
        #Finally, load new data if necessary
        if new_listwidget_item is not None:
            new_data = new_listwidget_item.data(Qt.UserRole).toPyObject()
            if new_data is not None:
                self.loadListData(new_data)
            #Set the current selection to this item to be sure
            new_listwidget_item.listWidget().setCurrentItem(new_listwidget_item)
            #Now that we have loaded up our data, we enable the watch/avoid list's option groups if necessary
            if opgrp_access_object.isEnabled() is False:
                opgrp_access_object.setEnabled(True)
            
        else:
            #Ok so we know new_listwidget_item is NoneType, this means the user has no item selected.
            #We will disable the group of options adjacent to the listwidget object
            opgrp_access_object.setDisabled(True)
        
        #Update sizecheck if on tab 2
        if self.context.tabWidget.currentIndex() == 2:
            self.checkSizeLimitBounds("wlist")
        
        #And set the load var again to its normal state
        self.__is_loading = False
        
        
    #These three functions deal with saving, clearing, and loading from watchlists.
    def saveListData(self, listwidget_elements, listwidget_item, defaults):
        item_save_data = DC(defaults)
        
        #Loop through each item in listwidget_elements
        for element in listwidget_elements:
            live_element = eval("self.context." + str(element))
            if len(listwidget_elements[element]) == 3:
                #Special case for size-limit selectors. We have to save the index of the dropdown list.
                #Get data for both elements.
                prefix, suffix = self.typeMatcher(live_element, "SLC_READ", listwidget_elements[element][2], sc=True)
                #Save the data for the textbox
                item_save_data[element] = prefix
                #And store the data for the dropdown box
                item_save_data[listwidget_elements[element][2]] = suffix
            else:
                #Get our access function to read the data from the live element into our save dict
                item_save_data[element] = self.typeMatcher(live_element, "READ")()
                #We may want to now get the write function to "zero out" the form. This may be better put in its own function however. (why?)
             
        #Now we have an OrderedDict with our data to save in it, we store it inside the element using the setData() function.
        #We will be saving the data in the Qt.UserRole role to the previous qlistwidgetitem we just had selected.
        if hasattr(listwidget_item, "setData"): listwidget_item.setData(Qt.UserRole, item_save_data)
    
    def clearUiData(self, reset_data):
        for element, data in reset_data.iteritems():
            live_element = eval("self.context." + str(element))
            write_function, dtype = self.typeMatcher(live_element, "WRITE")
            if dtype == "str": data = str(data)
            if dtype == "int": data = int(data)
            write_function(data)
    
    def loadListData(self, new_data):
        #Ok we do have data, so lets set the form up with this data
        for element, data in new_data.iteritems():
            live_element = eval("self.context." + str(element))
            write_function, datatype = self.typeMatcher(live_element, "WRITE")
            #Handle all checkboxes that aren't tristate. This just converts the 1's to 2's.
            if "QCheckBox" in str(type(live_element)):
                if element != "utwuiMasterEnableTriCheck" and element != "WLSGutWebUiCheckox":
                    if int(data) == 1:
                        data = 2
            if datatype == "str":
                data = str(data)
            if datatype == "int":
                try:
                    data = int(data)
                except:
                    data = 0
            #And now we update the element with the new data
            write_function(data)


    def updateCurrentWatchTitle(self, text):
        current_item = self.context.WLGwatchlistItemsList.currentItem()
        if current_item is not None:
            current_item.setText(text)
    
    def updateCurrentAvoidTitle(self, text):
        current_item = self.context.avoidlistItemsList.currentItem()
        if current_item is not None:
            current_item.setText(text)
    
    def clearList(self, access_object):
        #This function will remove all items from the QListWidget supplied as access_object
        while access_object.count() > 0:
            removed_item = access_object.takeItem(0)
            del(removed_item) #Sometimes I don't trust the GC, and it can't hurt to be sure.
    
    
    def loadUiState(self, dd_filename=None):
        #Takes in the data format of loadSettings() and updates the UI with the data received
        #We will go through data{} and use the access method detailed in the uiElements dictionary.
        #The two's structure are identical, making this task extremely simple.
        
        
        #prompt the user if they want to save or not
        
        #Check if we need to ask the user to save changes
        has_changed, rtn = self.checkUiStateChange()
        #If there were changes, check how the user wanted us to proceed
        if has_changed is True:
            if rtn == QtGui.QMessageBox.Save:
                if self.saveUiToFile() is False:
                    return 
            elif rtn == QtGui.QMessageBox.Discard:
                pass
            elif rtn == QtGui.QMessageBox.Cancel:
                return
        
        #Now that we have either saved or discared any changes made, we prompt the user to open up a new file
        #Get the new file name and tell the SettingsManager to update its QSettings object to use the new file location
        #We bypass this part of the user drag-and-drop'd a file
        if dd_filename is not None:
            filename = dd_filename
        else:
            filename = self.browse_button_loadFile()
        
        #Discontinue if the user canceled selection of a file
        if len(filename) < 1:
            return
        
        
        #close the old file first
        self.context.SettingsManager.closeSettingsFile()
        #Clear UI state
        self.clearGUIState()
        
        #Load up the data
        self.context.SettingsManager.openSettingsFile(filename)
        loaded_data = self.context.SettingsManager.loadSettings()
        #We have to convert the ini option names back into the element object's name.
        converted_data = OD()
        #Set the initial state of the data to the blank-slate defaults. This will catch any options the user forgot to include
        converted_data["GlobalSettings"] = DC(self.context.SettingsManager.guiDefaults["allOtherDefaults"])
        #converted_data["watch"] = DC(self.context.SettingsManager.guiDefaults["watchlistDefaults"])
        #converted_data["avoid"] = DC(self.context.SettingsManager.guiDefaults["avoidlistDefaults"])
        
        #Check if we have the correct settings, if not notify the user and discontinue current operation
        if loaded_data.has_key("GlobalSettings") is False:
            #The settings ini we are trying to load doesnt have our main settings section
            #We will assume this is not a correct file and give an error to the user
            text = "There was an error while trying to load the provided settings file. This file doesn't look like a valid SCCwatcher 2.0 settings file."
            errorbox = QtGui.QMessageBox(QtGui.QMessageBox.Critical, "SCCwatcher", text, QtGui.QMessageBox.Ok)
            errorbox.setWindowIcon(self.context.icon)
            errorbox.exec_()
            self.context.SettingsManager.closeSettingsFile()
            #Set the title because by now we've already closed the old file so we are effectively at a New File state.
            self.updateUiTitle("New Settings File")
            return
        
        #First we do the general options
        converted_data["GlobalSettings"] = OD()
        keys_to_match = self.context.SettingsManager.REVelementsToOptions.keys()
        for key, value in loaded_data["GlobalSettings"].iteritems():
            #While the below seems odd and roundaboutish for simple retrieving of data, I needed to be able to match a dict key against a string that
            #might not be the same case. If I just .lower'd() everything it would make the configs look ugly without caps differentiating the words.
            #At some point, no matter the solution, the lowercase keys must somehow be matched against the cased keys. We then need to return the cased key.
            cased_key = ""
            for i in keys_to_match:
                match_string = re.search("(" + str(key) + ")", i, re.I)
                if match_string is not None:
                    #Got our cased key
                    cased_key = match_string.group(1)
            if len(cased_key) == 0:
                print "SCCv2GUI.ERROR: Couldn't match cased_key against REVelementsToOptions. Erronious entry: %s" % (key,)
                continue
            
            objectname = self.context.SettingsManager.REVelementsToOptions[cased_key]
            converted_data["GlobalSettings"][str(objectname)] = value
        
        
        #Clean up loaded_data so we are left with just watches and avoids.
        del(loaded_data["GlobalSettings"])
        
        
        
        tmpwatch = OD()
        tmpavoid = OD()
        converted_data["watch"] = OD()
        converted_data["avoid"] = OD()
        
        
        #Sort the watches and avoids as well as fix the casing on options, like the global options above
        #Again, this isn't elegant but I'm done with elegant. Now I just want this working and done.
        for key, val in loaded_data.iteritems():
            if key[0] == "-":
                #Avoid item
                tmpavoid[key] = val
            else:
                #Watch item
                tmpwatch[key] = val
        
        #Watchlist first
        for entry in tmpwatch:
            converted_data["watch"][entry] = OD()
            for key, value in tmpwatch[entry].iteritems():
                cased_key = ""
                for i in self.context.SettingsManager.REVwatchListElements.keys():
                    match_string = re.search("(" + str(key) + ")", i, re.I)
                    if match_string is not None:
                        cased_key = match_string.group(1)
                if len(cased_key) == 0:
                    print "SCCv2GUI.ERROR: Couldn't match cased_key against REVwatchListElements. Erronious entry: %s" % (key,)
                    continue
                converted_data["watch"][entry][cased_key] = value
                
        #Avoidlist second. And yes I know this should probably be its own function but its being used twice and I'm super braindead right now
        #If it works it works, JUST DO IT
        for entry in tmpavoid:
            converted_data["avoid"][entry] = OD()
            for key, value in tmpavoid[entry].iteritems():
                cased_key = ""
                for i in self.context.SettingsManager.REVavoidListElements.keys():
                    match_string = re.search("(" + str(key) + ")", i, re.I)
                    if match_string is not None:
                        cased_key = match_string.group(1)
                if len(cased_key) == 0:
                    print "SCCv2GUI.ERROR: Couldn't match cased_key against REVavoidListElements. Erronious entry: %s" % (key,)
                    continue
                objectname = self.context.SettingsManager.REVavoidListElements[cased_key]
                converted_data["avoid"][entry][cased_key] = value
        
        #Remove temp stuffs
        del(tmpavoid)
        del(tmpwatch)

        #Ok now converted_data has three subdicts called: GlobalSettings, watch, and avoid.
        #We now go about the business of setting the GUI up with the loaded data.
        #First we do the GlobalSettings.
        #We look through our elementsToOptions dict and set each options as we come upon it.
        for element, einfos in self.context.SettingsManager.elementsToOptions.iteritems():
            #If we come upon an option in our element list that doesn't exist in the ini file, we just skip it.
            #The defaults in the GUI will take over from there.
            if converted_data["GlobalSettings"].has_key(element) is False:
                continue
            data = converted_data["GlobalSettings"][element]
            
            #Check if there is any data. If there isn't, then the defaults will kick in again
            if len(data) == 0:
                continue
            
            #Make a live access object from element and then use its type to get our access function
            access_string = "self.context." + str(element)
            live_element_obj = eval(access_string)
            #we use typeMatcher() to return our write function
            access_function, datatype = self.typeMatcher(live_element_obj, "WRITE")
            
            #Handle all checkboxes that aren't tristate. This just converts the 1's to 2's.
            if "QCheckBox" in str(type(live_element_obj)):
                if element != "utwuiMasterEnableTriCheck" and element != "WLSGutWebUiCheckox":
                    if int(data) == 1:
                        data = 2
            
            #special case for size limit selector
            if len(einfos) > 2:
                prefix = ""
                suffix = ""
                #Check if we have any data, if not we just move along
                if len(data) < 1:
                    continue
                #Split up the data into two part, prefix and suffix
                try:
                    prefix, suffix = re.match("([0-9]{1,9})(?:\s+)?([A-Za-z]{2})?", data).groups()
                    if len(suffix) > 0:
                        suffix = self.convertIndex(suffix)
                    
                except:
                    #Probably set weird
                    pass
                #Get the live function for the suffix
                suffix_access_string = "self.context." + str(einfos[2])
                live_suffix_obj = eval(suffix_access_string)
                suffix_access_function = self.typeMatcher(live_suffix_obj, "WRITE")[0]
                #Now we set the data for the prefix
                access_function(prefix)
                if type(suffix) is not int:
                    try:
                        suffix = int(suffix)
                    except:
                        suffix = 0
                suffix_access_function(int(suffix))
                
            else:
                #Get and set the needed type for the data we plan to set
                if datatype == "str": data = str(data)
                if datatype == "int": data = int(data)
                #update the element with the data
                access_function(data)
        
        #Now we do the watchlist. We do this a little differently.
        #We loop through each key in converted_data["watch"] and create new watchlist items for each one
        #Then we set the data for that item and move onto the next one. We shouldn't have to actually update the GUI since that happens automatically when you click an item.
        for item_name, item_data in converted_data["watch"].iteritems():
            __sortingEnabled = self.context.WLGwatchlistItemsList.isSortingEnabled()
            self.context.WLGwatchlistItemsList.setSortingEnabled(False)
            #Create a new QListWidgetItem with the name item_name
            new_item = QtGui.QListWidgetItem()
            #Make sure the item_name isnt a duplicate
            item_name = self.checkForDuplicates(self.context.WLGwatchlistItemsList, item_name)
            new_item.setText(_translate("sccw_SettingsUI", item_name, None))
            #Add the item to the list
            self.context.WLGwatchlistItemsList.addItem(new_item)
            self.context.WLGwatchlistItemsList.setSortingEnabled(__sortingEnabled)
            #Fix the data's options name so they are element names
            item_data = self.fixElementsToOptionsLoad(item_data, self.context.SettingsManager.watchListElements, ["WLSGwatchNameTextbox", item_name])
            
            #I hate doing this but sometimes you just have to fix something the hard way. Loop through the data and add in any missing defaults:
            missing_keys = [key for key in self.context.SettingsManager.guiDefaults["watchlistDefaults"].keys() if key not in item_data.keys()]
            for key in missing_keys:
                print "WARNING, ADDING IN DEFAULT KEY FOR %s ON WATCH %s" % (key, item_name)
                item_data[key] = self.context.SettingsManager.guiDefaults["watchlistDefaults"][key]
            
            #Add the data to the item for the user role. We're using a new item to be sure
            actual_item = self.context.WLGwatchlistItemsList.findItems(item_name, Qt.MatchFixedString)[0]
            actual_item.setData(Qt.UserRole, item_data)
        
        #Same thing for the avoidlist
        for item_name, item_data in converted_data["avoid"].iteritems():
            __sortingEnabled = self.context.avoidlistItemsList.isSortingEnabled()
            self.context.avoidlistItemsList.setSortingEnabled(False)
            #Create our QListWidgetItem
            new_item = QtGui.QListWidgetItem()
            #Remove the minus sign from the beginning of the watch title
            if item_name[0] == "-": item_name = self.removeMinusSignPrefix(item_name)
            #Make sure the title isnt a dupe
            item_name = self.checkForDuplicates(self.context.avoidlistItemsList, item_name)
            #Set its text
            new_item.setText(_translate("sccw_SettingsUI", item_name, None))
            #Add to the list
            self.context.avoidlistItemsList.addItem(new_item)
            #Finally we reenable sorting, if it was enabled before
            self.context.avoidlistItemsList.setSortingEnabled(__sortingEnabled)
            #Fix the data
            item_data = self.fixElementsToOptionsLoad(item_data, self.context.SettingsManager.avoidListElements, ["avoidNameTextbox", item_name])
            #Set the data using a new item from the qlistwidget to be sure its the right one
            actual_item = self.context.avoidlistItemsList.findItems(item_name, Qt.MatchFixedString)[0]
            actual_item.setData(Qt.UserRole, item_data)
        
        #Now that a new file has been loaded, we need to update the current internal state
        self.updateUiStateInfo()
        #And finally set the title to the new file's name
        nameonly = str(filename)
        nameonly = nameonly.replace("\\", "/")
        nameonly = ntpath_basename(nameonly)
        title = "%s (%s)" % (nameonly, filename)
        self.updateUiTitle(title)
        
    def removeMinusSignPrefix(self, text):
        #Silly to have this as its own function but recursing has its benefits
        #wouldnt string.replace() work without needing recursion or looping?
        if text[0] == "-":
            text = text[1:]
            text = self.removeMinusSignPrefix(text)
        return text
    
    
    def saveAsDialog(self, recurse=False):
        #Since this is a save-as dialog, we just change the file location and save
        newfilename = self.saveAsAction()
        if len(newfilename) < 1:
            return False
        #Close the old file first
        self.context.SettingsManager.closeSettingsFile()
        #Then set the new file
        self.context.SettingsManager.openSettingsFile(newfilename)
        #Update the title of the window to reflect the new file name
        nameonly = str(newfilename)
        nameonly = nameonly.replace("\\", "/")
        nameonly = ntpath_basename(nameonly)
        title = "%s (%s)" % (nameonly, newfilename)
        self.updateUiTitle(title)
        #Finally we pass onto saveUiToFile to finish things off
        if recurse == False: self.saveUiToFile()
        else: return True
    
    def saveUiToFile(self):
        #Takes the current state of the UI in an OrderedDict and sends it to the saveSettings() function.
        #Our return dictionary
        save_data = OD()
        #Our return dictionary will be in the form:
        #save_data[subgroupName][optionName] = data
        
        #If there isnt a file currently loaded to save to, we turn this into a save-as dialog
        if self.context.SettingsManager.isLoaded == False:
            if not self.saveAsDialog(recurse=True):
                return False
        
        #Similar to updateUi(), we are going to loop through the uiElements dict and use its access methods to save the Ui state.
        #Now we loop through each element and eval it into life. Then we send each element through a type checking function that will access its data depending on its type.
        for element, data_list in self.context.elementsToOptions.iteritems():
            #Lets separate out some info from data_list first
            #These two options map our data to ini option sections and names
            subgroupName = data_list[0]
            optionName = data_list[1]
            #Do what we need to get the dictionary ready for use
            if subgroupName not in save_data.keys(): save_data[subgroupName] = OD()
            #Here we make up a string with our element, eval it into life, then give it to the type checker
            access_string = "self.context." + str(element)
            live_access_string = eval(access_string)
            #And now we send it to the type checker and set our save_data to its output
            if len(data_list) == 3:
                read_data = self.typeMatcher(live_access_string, "SLC_READ", data_list[2])
            else:
                read_data = self.typeMatcher(live_access_string, "READ")()
            save_data[subgroupName][optionName] = read_data
        
        #Now we get the data associated with each watchlist item and save it in our save_data dict
        #This part will get the number of items in the QListWidget and then loop through each QListWidgetItem
        #It will get the QListWidgetItem's text() as the option group name and the data() contains an OrderedDict with our data
        
        #We are going to shorten the variable name a little to make it easier on the eyes.
        watchlist = self.context.WLGwatchlistItemsList
        
        #We're going to grab the data associated with each item in the watchlist and save it to our save_data
        for cur_index in xrange(0, watchlist.count()):
            #Get our watchlist item
            cur_WL_item = watchlist.item(cur_index)
            #If we get a 0 it means this index has no item, so we go onto the next iteration.
            #We should really just break here since returning no item usually means end of list, but I cant be sure.
            if cur_WL_item == 0:
                continue
            
            #Get the watch title
            cur_WL_title = str(cur_WL_item.text())
            
            #Return our data and use toPyObject() to turn it from a QVariant to an OrderedDict.
            cur_WL_data = cur_WL_item.data(Qt.UserRole).toPyObject()
            
            #Before we can save the data we have to go through it and convert raw element names into human-readable option names.
            fixed_WL_data = self.fixElementsToOptionsSave(cur_WL_data, self.context.watchListElements)
            
            #Should have a nice OrderedDict full of our options with proper, human-readable names.
            save_data[cur_WL_title] = fixed_WL_data
        
        #Ok now we do the same for the avoidlist, except we prepend the title with a minus.
        avoidlist = self.context.avoidlistItemsList
        for cur_index in xrange(0, avoidlist.count()):
            #Get the avoidlist item
            cur_AL_item = avoidlist.item(cur_index)
            if cur_AL_item == 0:
                continue
            
            #Set the title, a minus denotes it is an avoidlist item. REMEMBER TO REMOVE ON LOAD!
            cur_AL_title = str(cur_AL_item.text())
            cur_AL_title = "-" + cur_AL_title
            
            #Get the data
            cur_AL_data = cur_AL_item.data(Qt.UserRole).toPyObject()
            
            #Change the keys from the element name to the option name for saving
            fixed_AL_data = self.fixElementsToOptionsSave(cur_AL_data, self.context.avoidListElements)
            
            #save the data
            save_data[cur_AL_title] = fixed_AL_data
        
        #We should now have a nice dictionary filled with the current state of our app. Lets send it to our save function and let it handle the rest
        self.context.SettingsManager.saveSettings(save_data)
        
        #We lastly need to update the internal GUI state since things could have changed since the last load/save operation
        self.updateUiStateInfo()
    
    
    def fixElementsToOptionsSave(self, cur_L_data, listElements):
        fixed_L_data = OD()
        cur_L_data_fixed = OD()
        #First we have to loop through cur_L_data and convert all the keys to proper strings
        for key, value in cur_L_data.iteritems():
            cur_L_data_fixed[str(key)] = str(value)
        
        
        for element, data_list in listElements.iteritems():
            if "TITLE" in data_list[1]:
                continue
            #data_list[1] is our option name
            if len(data_list) == 3:
                #special case for size-limit selectors
                #Remember, we have to undo this on load
                
                suffix = self.convertIndex(str(cur_L_data_fixed[data_list[2]]))
                nice_size_limit = str(cur_L_data_fixed[element]) + str(suffix)
                fixed_L_data[data_list[1]] = nice_size_limit
            else:
                try:
                    fixed_L_data[data_list[1]] = str(cur_L_data_fixed[element])
                except:
                    print "Missing option in watch entry data, ignoring %s..." % element
                    
        return fixed_L_data
    
    def fixElementsToOptionsLoad(self, loaded_data, listElements, nametextbox):
        fixed_loaded_data = OD()
        for element, data_list in listElements.iteritems():
            if "TITLE" in data_list[1]:
                fixed_loaded_data[nametextbox[0]] = nametextbox[1]
                continue
            
            option_name = data_list[1]
            try:
                data = loaded_data[option_name]
            except:
                #missing option, fill in with blank data
                continue
                
            if len(data_list) == 3:
                #special case for size-limit selectors
                #Split the data into two different items
                try:
                    prefix, suffix = re.match("([0-9]{1,9})(?:\s+)?([A-Za-z]{2})?", data).groups()
                    suffix = self.convertIndex(suffix)
                except:
                    #This option was probably not set by the user so we ignore it too by setting the prefix and suffix to default
                    prefix = ""
                    suffix = 0
                    
                suffix_element_name = data_list[2]
                #Set the data for both the prefix and suffix
                fixed_loaded_data[element] = prefix
                fixed_loaded_data[suffix_element_name] = suffix
            else:    
                fixed_loaded_data[element] = loaded_data[option_name]
        return fixed_loaded_data
    
    def convertIndex(self, index):
        #Changing these types() to isinstance(), comparing to their base classes, would be safer/more reliable.
        suffix = "ERROR"
        
        #Gettin rid of teh errors
        try:
            index = int(index)
        except:
            pass
        
        if index is None:
            index = ""
        
        if isinstance(index, basestring):
            if index == "": suffix = 0
            if index == "KB": suffix = 1
            if index == "MB": suffix = 2
            if index == "GB": suffix = 3
        if isinstance(index, Number):
            if index == 0: suffix = ""
            if index == 1: suffix = "KB"
            if index == 2: suffix = "MB"
            if index == 3: suffix = "GB"
        return suffix
        
    def typeMatcher(self, access_object, operation, alt_obj = None, sc = False):
        #This function will match the type of the access_object provided to an entry in a dictionary and return the data requested in operation.
        #operation can be READ, WRITE or a special case called SLC_READ.
        if operation == "SLC_READ":
            #SLC_READ is used when we need both the size and suffix of our sizelimit entries in one piece of data.
            #We need to concatenate the data returned from two objects
                prefix = self.typeMatcher(access_object, "READ")()
                suffix_index = int(self.typeMatcher(eval("self.context." + str(alt_obj)), "READ")())
                suffix = self.convertIndex(suffix_index)
                if sc is True: return [prefix, suffix_index]
                else: return str(prefix) + suffix
                    
        #Convert operation into numbers to make matching to index easier. Read is default.
        op = 0
        if operation == "WRITE": op = 1
        
        for type_name in self.context.elementAccessMethods.keys():
            if type_name in str(type(access_object)):
                access_function = self.context.elementAccessMethods[type_name][op]
                if op == 1: dtype = self.context.elementAccessMethods[type_name][2]
                break
        #Now we have our access function, we use getattr to return the live function
        live_function = getattr(access_object, access_function)
        if op == 1:
            return (live_function, dtype)
        else:
            return live_function
    
    
    
    #Here are the 6 browse buttons. I would have to mess around with the QPushButton class, changing the way it emits, if I wanted to cut these down.
    #start_dir is a list because im lazy and didn't want to rewrite it the correct way. Nobody but me is going to be messing around this part of the code anyway.
    #The extra digit controls whether the start_dir should be returned if the user cancels the dialog instead of making a selection.
    
    #I could replace most of these with partial'd functions
    def browse_button_mainSavepath(self):
        caption = "Choose location to save .torrent files..."
        if len(self.context.ggSavepathTextbox.text()) > 1:
            start_dir = [self.context.ggSavepathTextbox.text(), 1]
        elif len(self.context.ggLogpathTextbox.text()) > 1:
            start_dir = [self.context.ggLogpathTextbox.text(), 0]
        elif len(self.context.SettingsManager.currentFile) > 1:
            start_dir = [self.context.SettingsManager.currentFile, 0]
        else:
            start_dir = [QDir.currentPath(), 0]
        
        self.browse_button_master(self.context.ggSavepathTextbox, QtGui.QFileDialog.AcceptSave, QtGui.QFileDialog.Directory, caption, start_dir=start_dir)
    
    def browse_button_mainLogpath(self):
        if len(self.context.ggLogpathTextbox.text()) > 1:
            start_dir = [self.context.ggLogpathTextbox.text(), 1]
        elif len(self.context.ggSavepathTextbox.text()) > 1:
            start_dir = [self.context.ggSavepathTextbox.text(), 0]
        elif len(self.context.SettingsManager.currentFile) > 1:
            start_dir = [self.context.SettingsManager.currentFile, 0]
        else:
            start_dir = [QDir.currentPath(), 0]
        
        caption = "Choose location to save logs..."
        self.browse_button_master(self.context.ggLogpathTextbox, QtGui.QFileDialog.AcceptSave, QtGui.QFileDialog.Directory, caption, start_dir=start_dir)
        
    
    def browse_button_cookieFile(self):
        start_dir = [self.context.globalCFBypassCookiefilePathTextbox.text(), 1]
        caption = "Location of cookie file..."
        filters = "Exported Cookies (*.txt);;All Files (*.*)"
        self.browse_button_master(self.context.globalCFBypassCookiefilePathTextbox, QtGui.QFileDialog.AcceptOpen, QtGui.QFileDialog.ExistingFile, caption, start_dir=start_dir, filters=filters)
        
        
    def browse_button_mainExtProgram(self):
        start_dir = [self.context.extCmdExeLocation.text(), 1]
        caption = "Choose A Program..."
        self.browse_button_master(self.context.extCmdExeLocation, QtGui.QFileDialog.AcceptOpen, QtGui.QFileDialog.ExistingFile, caption, start_dir=start_dir)
        
        
    def browse_button_WLsavepath(self):
        start_dir = [self.context.WLSGsavepathTextbox.text(), 1]
        caption = "Choose location to save .torrent files to..."
        self.browse_button_master(self.context.WLSGsavepathTextbox, QtGui.QFileDialog.AcceptSave, QtGui.QFileDialog.Directory, caption, start_dir=start_dir)
        #Update the data for the watch item manually
        self.saveAllWatchlistItems()
        
        
    def browse_button_WLextProgram(self):
        start_dir = [self.context.WLSGexternalCommandTextbox.text(), 1]
        caption = "Choose A Program..."
        self.browse_button_master(self.context.WLSGexternalCommandTextbox, QtGui.QFileDialog.AcceptOpen, QtGui.QFileDialog.ExistingFile, caption, start_dir=start_dir)
        #Update the data for the watch item manually
        self.saveAllWatchlistItems()
    
    def browse_button_loadFile(self):
        start_dir = [self.context.SettingsManager.currentFile, 0]
        caption = "Location of scc2.ini..."
        filters = "SCCwatcher Settings File (*.ini);;All Files (*.*)"
        filename = self.browse_button_master(None, QtGui.QFileDialog.AcceptOpen, QtGui.QFileDialog.ExistingFile, caption, alt_mode=True, start_dir=start_dir, filters=filters)
        return filename
    
    def saveAsAction(self):
        start_dir = [self.context.SettingsManager.currentFile, 0]
        caption = "Choose location to save settings file..."
        filters = "SCCwatcher Settings File (*.ini);;All Files (*.*)"
        filename = self.browse_button_master(None, QtGui.QFileDialog.AcceptSave, QtGui.QFileDialog.AnyFile, caption, alt_mode=True, save_mode=True, start_dir=start_dir, filters=filters)
        return filename
    
    
    def browse_button_master(self, access_object, main_mode, file_mode, dialog_caption, alt_mode=False, save_mode=False, start_dir=["", 0], filters="All Files (*.*)"):
        rtnstat = start_dir[1]
        start_dir = start_dir[0]
        
        fileDialog = QtGui.QFileDialog()
        fileDialog.AcceptMode = main_mode
        fileDialog.setFileMode(file_mode)
        fileDialog.setDirectory(start_dir)
        if save_mode == True:
            fd_access = fileDialog.getSaveFileName
        else:
            fd_access = fileDialog.getOpenFileName
        
        if file_mode == QtGui.QFileDialog.Directory:
            chosenFile = fileDialog.getExistingDirectory(caption=dialog_caption)
        elif file_mode == QtGui.QFileDialog.ExistingFile or file_mode == QtGui.QFileDialog.AnyFile:
            chosenFile = fd_access(caption=dialog_caption, filter=filters)
        
        if len(chosenFile) < 1:
            if rtnstat == 1:
                chosenFile = start_dir
        
        if alt_mode is True:
            #We are going to return the filename instead
            return chosenFile
        else:
            #Tell the undo/redo system to ignore this update
            access_object.ignoreBrowseButtonSet = True
            access_object.setText(_translate("sccw_SettingsUI", chosenFile, None))
    
    
    #These EDsection_ functions enable/disable the option sections that correspond to certain checkboxes.
    #checkboxes will have thier toggled(bool) slots tied into these functions.
    #It was only possible to directly connect one checkbox, the others needed these helper functions.
    def EDsection_ftpupload(self, state):
        #FTP upload section of Upload/Download tab
        #These functions are pretty simple, we just pass state, which is a bool, to the setEnabled functions of the objects we need to turn off/on.
        self.context.ftpHostnameTextbox.setEnabled(state)
        self.context.ftpPortTextbox.setEnabled(state)
        self.context.ftpUsernameTextbox.setEnabled(state)
        self.context.ftpPasswordTextbox.setEnabled(state)
        self.context.ftpRemoteFolderTextbox.setEnabled(state)
        self.context.ftpPasvModeCheck.setEnabled(state)
        self.context.ftpTLSModeCheck.setEnabled(state)
        
    def EDsection_utwebui(self, state):
        #uTorrent WebUI of the Ul/Dl tab
        #Because this is a tri-state checkbox we cant use toggled(bool). Instead of have to use stateChanged(int) and compare the int.
        #We also update the QLabel here with the appropriate text and color change to indicate the different modes of operation for the utorrent module
        
        #QLabel first
        if state == 0:
            color = "#ff0000"
            text = "Disabled"
        elif state == 1:
            color = "#00aa00"
            text = "Normal DL and WebUI UL"
        elif state == 2:
            color = "#ff8700"
            text = "WebUI Uploading Only"
            
        self.context.utwuiStateLabel.setText(_translate("sccw_SettingsUI", "<html><head/><body><p><span style=\" font-weight:600; color:%s;\">%s</span></p></body></html>" % (color, text), None))
        
        #I wonder if setEnabled can take a simple 0/1 int so we don't have to do this compare
        #We could just bool() it since 0 is false and anything else is true
        if state > 0:
            state = True
        else:
            state = False
            
        self.context.utwuiHostnameTextbox.setEnabled(state)
        self.context.utwuiPortTextbox.setEnabled(state)
        self.context.utwuiUsernameTextbox.setEnabled(state)
        self.context.utwuiPasswordTextbox.setEnabled(state)
        
    def EDsection_externalcmd(self, state):
        #External command section of the ul/dl tab
        self.context.extCmdExeLocation.setEnabled(state)
        self.context.extCmdBrowseButton.setEnabled(state)
        self.context.extCmdExeArguments.setEnabled(state)
        
    def EDsection_emailer(self, state):
        #Emailer section of the Emailer tab
        self.context.hostnameIPTextbox.setEnabled(state)
        self.context.portTextbox.setEnabled(state)
        self.context.usernameTextbox.setEnabled(state)
        self.context.passwordTextbox.setEnabled(state)
        self.context.emailUseTLSCheck.setEnabled(state)
        self.context.emailFromTextbox.setEnabled(state)
        self.context.emailToTextbox.setEnabled(state)
        self.context.emailSubjectTextbox.setEnabled(state)
        self.context.emailMessageTextbox.setEnabled(state)
    
    #Ok we only use this function once, by the checkForUpdates() function.
    #I feel like these should both be merged. There is little point besides clean code to separating them.
    def isNewerVersion(self, latest):
        #This function will return True if the supplied version is older or the same as the current version
        #long expression to match something like this: 2.0b1
        mreg = re.compile(r"(?P<major>[0-9]\.[0-9]{1,2})(:?(?P<sep>(?:[ab]|rc))(?P<minor>[0-9]{1,2}))?")
        
        cregex = mreg.match(self.context.SettingsManager.CURRENT_GUI_VERSION)
        rregex = mreg.match(latest)
        #cmajor is current major
        #lmajor is latest major
        curver = [cregex.group("major"), cregex.group("sep"), cregex.group("minor")]
        latestver = [rregex.group("major"), rregex.group("sep"), rregex.group("minor")]
        
        if self.context.SettingsManager.CURRENT_GUI_VERSION == latest:
            return False
        if float(curver[0]) < float(latestver[0]): 
            return True
        if float(curver[0]) > float(latestver[0]): 
            return False
        if latestver[1] is not None:
            if curver[1] is None:
                return False
        if curver[1] is not None:
            if latestver[1] is None:
                return True
        if curver[1] > latestver[1]:
            return False
        if curver[1] < latestver[1]:
            return True
        if int(curver[2]) < int(latestver[2]):
            return True
        return False

    def checkForUpdates(self):
        text_color = "#ff0000"
        comment = "Error!"
        c = urlopen(self.context.SettingsManager.GITHUB_VER_URL)
        version_txt = c.read()
        c.close()
        #Fix some minor stuffs
        version_txt = version_txt.replace("true", "True")
        version_txt = version_txt.replace("false", "False")
        version_txt = version_txt.replace("null", "None")
        try:
            version_dict = safe_eval(version_txt) #might still be a bad idea
        except:
            return
        latest_version = version_dict["tag_name"]
        
        if self.isNewerVersion(latest_version) is True:
            #latest_version is newer than ours 
            text_color = "#ff0000"
            comment = "Old"
        else:
            comment = "Latest"
            text_color = "#0055ff"
        
        #Set the latest version number in the GUI
        self.context.ugServVerActual.setText(_translate("sccw_SettingsUI", "<html><head/><body><p><span style=\" font-weight:600; color:#0055ff;\">%s</span></p></body></html>" % (latest_version), None))
        self.context.ugCliVerActual.setText(_translate("sccw_SettingsUI", "<html><head/><body><p><span style=\" font-weight:600; color:%s;\">%s (%s)</span></p></body></html>" % (text_color, self.context.SettingsManager.CURRENT_GUI_VERSION, comment), None))
        
    
    def fileDropAction(self, filename):
        self.loadUiState(dd_filename=filename)
    
    #Custom edit menu stuffs
    def updateEditMenuStatus(self):
        currentWidget = self.context.MainWindow.window().focusWidget()
        
        #Update selection options if necessary
        if currentWidget is not None:
            #Set all to disabled by default
            self.context.actionCut.setEnabled(False)
            self.context.actionCopy.setEnabled(False)
            self.context.actionPaste.setEnabled(False)
            self.context.actionDelete.setEnabled(False)
            self.context.actionSelectAll.setEnabled(False)
            
            if re.search("special_Q(Line|Text)Edit", str(currentWidget)) is not None:
                self.context.actionSelectAll.setEnabled(True)
                #Check for clipboard
                if len(QtGui.QApplication.clipboard().text()) > 0:
                    self.context.actionPaste.setEnabled(True)
                else:
                    self.context.actionPaste.setEnabled(False)
            
            if "special_QSpinBox" in str(currentWidget):
                self.context.actionSelectAll.setEnabled(True)
            
            if "special_QLineEdit" in str(currentWidget):
                #Check for selection
                self.context.actionCut.setEnabled(currentWidget.hasSelectedText())
                self.context.actionCopy.setEnabled(currentWidget.hasSelectedText())
                self.context.actionDelete.setEnabled(currentWidget.hasSelectedText())
                
            elif "special_QTextEdit" in str(currentWidget):
                cursor = QtGui.QTextCursor(currentWidget.textCursor())
                self.context.actionCut.setEnabled(cursor.hasSelection())
                self.context.actionCopy.setEnabled(cursor.hasSelection())
                self.context.actionDelete.setEnabled(cursor.hasSelection())
                
    def customContextMenu_hasSelection(self, currentWidget):
        if "special_QLineEdit" in str(currentWidget):
            if currentWidget.hasSelectedText() is True:
                return 1
        elif "special_QTextEdit" in str(currentWidget):
            cursor = QtGui.QTextCursor(currentWidget.textCursor())
            if cursor.hasSelection() is True:
                return 2
        return None
    
    def customContextMenu_Cut(self):
        currentWidget = self.context.MainWindow.window().focusWidget()
        has_selection = self.customContextMenu_hasSelection(currentWidget)
        if has_selection == 1 or has_selection == 2:
            currentWidget.cut()
    
    def customContextMenu_Copy(self):
        currentWidget = self.context.MainWindow.window().focusWidget()
        has_selection = self.customContextMenu_hasSelection(currentWidget)
        if has_selection == 1 or has_selection == 2:
            currentWidget.copy()
    
    def customContextMenu_Paste(self):
        currentWidget = self.context.MainWindow.window().focusWidget()
        if any(x in str(currentWidget) for x in ["special_QLineEdit", "special_QTextEdit", "special_QSpinBox"]):
            if len(QtGui.QApplication.clipboard().text()) > 0:
                currentWidget.paste()
    
    def customContextMenu_SelectAll(self):
        currentWidget = self.context.MainWindow.window().focusWidget()
        if any(x in str(currentWidget) for x in ["special_QLineEdit", "special_QTextEdit", "special_QSpinBox"]):
            currentWidget.selectAll()
            
    def customContextMenu_Delete(self):
        currentWidget = self.context.MainWindow.window().focusWidget()
        #Not sure which way I like better, this one or the one in customContextMenu_Paste. This one is longer but easier to read.
        has_selection = self.customContextMenu_hasSelection(currentWidget)
        if has_selection == 1:
            if currentWidget.hasSelectedText() is True:
                currentWidget.del_()
        elif has_selection == 2:
            cursor = QtGui.QTextCursor(currentWidget.textCursor())
            cursor.removeSelectedText()
    
    def quitApp(self):
        #Basically the same as new, except we then quit after that
        if self.newSettingsFile():
            #User wants to quit
            self.context.MainWindow._user_accept_close = True
            #Shut down client thread
            self.client_thread.quit_thread()
            self.client_thread.join()
            self.context.MainWindow.close()
