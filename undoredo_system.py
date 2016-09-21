#Crappy Undo/Redo system
#Hey it works tho


from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

class special_QLineEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        self.previous_text = ""
        self.ignore_undoredo_action = False
        self.parent = parent
        self.ignoreBrowseButtonSet = False
        super(special_QLineEdit, self).__init__(parent)
        #Disable standard context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
               
    
    def setText(self, text):
        if self.ignoreBrowseButtonSet == True:
            self.ignoreBrowseButtonSet = False
        else:
            self.previous_text = text
            #emit our special signal
            self.emit(QtCore.SIGNAL("undoredoUpdateSignal"), text)
        super(special_QLineEdit, self).setText(text)
    
    ##Override the QLineEdit standard shortcuts and use global ones
    def event(self, event):
        if event.type() == QtCore.QEvent.ShortcutOverride:
            return False 
        return QtGui.QLineEdit.event(self, event)
    
    def customContextMenu(self, pos):
        self.window().ui.menu_Edit.popup(self.mapToGlobal(pos))

class undoredo_item_QLineEdit(object):
    def __init__(self, element):
        self.element = element
        self.prevtext = element.previous_text
        self.curtext = element.text()
        self.savedOn = False
        #Get current tab
        self.tab = element.window().ui.tabWidget.currentIndex()
        #set current listwidget if necessary
        self.current_listwidget = None
        self.current_listwidget_row = 0
        if self.tab == 2:
            self.current_listwidget = element.window().ui.WLGwatchlistItemsList
            self.current_listwidget_row = self.current_listwidget.currentRow()
        elif self.tab == 3:
            self.current_listwidget = element.window().ui.avoidlistItemsList
            self.current_listwidget_row = element.window().ui.avoidlistItemsList.currentRow()
    
    
    def execute(self, prev_item):
        #Initiate undo or redo op
        #Change tab, listwidget item if necessary, and set focus
        self.element.window().ui.tabWidget.setCurrentIndex(self.tab)
        if self.current_listwidget is not None:
            self.current_listwidget.setCurrentRow(self.current_listwidget_row)
        self.element.setFocus(QtCore.Qt.OtherFocusReason)
        #Create our inverse object
        inverse_obj = undoredo_item_QLineEdit(self.element)
        #Update obj with new prevtext
        self.element.setText(self.prevtext)
        #set new prevtext
        self.element.previous_text = prev_item.prevtext
        #Set focus with OtherFocusReason (7)
        self.element.setFocus(7)
        return inverse_obj




class special_QTextEdit(QtGui.QPlainTextEdit):
    def __init__(self, parent=None):
        self.ignore_undoredo_action = False
        self.parent = parent
        super(special_QTextEdit, self).__init__(parent)
        self.previous_text = self.toPlainText()
        #Disable standard context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    
    #Override the QTextEdit standard shortcuts and use global ones
    def event(self, event): 
        if event.type() == QtCore.QEvent.ShortcutOverride:
            return False 
        return QtGui.QPlainTextEdit.event(self, event)
    
    def customContextMenu(self, pos):
        self.window().ui.menu_Edit.popup(self.mapToGlobal(pos))
        
    def setPlainText(self, text, ignore=True):
        self.ignore_undoredo_action = ignore
        self.previous_text = text
        super(special_QTextEdit, self).setPlainText(text)

class undoredo_item_QTextEdit(object):
    def __init__(self, element):
        self.element = element
        self.prevtext = element.previous_text
        self.curtext = element.toPlainText()
        self.savedOn = False
        #Get current tab
        self.tab = element.window().ui.tabWidget.currentIndex()
        #set current listwidget if necessary
        self.current_listwidget = None
        self.current_listwidget_row = 0
        if self.tab == 2:
            self.current_listwidget = element.window().ui.WLGwatchlistItemsList
            self.current_listwidget_row = self.current_listwidget.currentRow()
        elif self.tab == 3:
            self.current_listwidget = element.window().ui.avoidlistItemsList
            self.current_listwidget_row = element.window().ui.avoidlistItemsList.currentRow()
        
    def execute(self, prev_item):
        #Initiate undo or redo op
        #Change tab, listwidget item if necessary, and set focus
        self.element.window().ui.tabWidget.setCurrentIndex(self.tab)
        if self.current_listwidget is not None:
            self.current_listwidget.setCurrentRow(self.current_listwidget_row)
        self.element.setFocus(QtCore.Qt.OtherFocusReason)
        #Create our inverse object
        inverse_obj = undoredo_item_QTextEdit(self.element)
        #Update obj with new prevtext
        self.element.setPlainText(self.prevtext)
        #set new prevtext
        self.element.previous_text = prev_item.prevtext
        #Set focus with OtherFocusReason (7)
        self.element.setFocus(7)
        #Set cursor position to the end
        cursor = QtGui.QTextCursor(self.element.textCursor())
        cursor.movePosition(QtGui.QTextCursor.End)
        self.element.setTextCursor(cursor)
        
        #return new stack item
        return inverse_obj





class special_QCheckBox(QtGui.QCheckBox):
    def __init__(self, parent=None):
        self.ignore_undoredo_action = False
        self.parent = parent
        super(special_QCheckBox, self).__init__(parent)
        self.previous_state = self.checkState()
        
    def setCheckState(self, state):
        self.previous_state = state
        super(special_QCheckBox, self).setCheckState(state)

class undoredo_item_QCheckBox(object):
    def __init__(self, element):
        self.element = element
        self.prevstate = element.previous_state
        self.curstate = element.checkState()
        self.savedOn = False
        #Get current tab
        self.tab = element.window().ui.tabWidget.currentIndex()
        #set current listwidget if necessary
        self.current_listwidget = None
        self.current_listwidget_row = 0
        if self.tab == 2:
            self.current_listwidget = element.window().ui.WLGwatchlistItemsList
            self.current_listwidget_row = self.current_listwidget.currentRow()
        elif self.tab == 3:
            self.current_listwidget = element.window().ui.avoidlistItemsList
            self.current_listwidget_row = element.window().ui.avoidlistItemsList.currentRow()
        
    def execute(self, prev_item):
        #Initiate undo or redo op
        #Change tab, listwidget item if necessary, and set focus
        self.element.window().ui.tabWidget.setCurrentIndex(self.tab)
        if self.current_listwidget is not None:
            self.current_listwidget.setCurrentRow(self.current_listwidget_row)
        self.element.setFocus(QtCore.Qt.OtherFocusReason)
        #Create our inverse object
        inverse_obj = undoredo_item_QCheckBox(self.element)
        #Update obj with new prevstate
        self.element.setCheckState(self.prevstate)
        #set new prevstate
        self.element.previous_state = prev_item.prevstate
        #update watchlist
        if self.tab == 2:
            self.element.window().ui.guiActions.saveAllWatchlistItems()
        elif self.tab == 3:
            self.element.window().ui.guiActions.saveAllAvoidlistItems()
        #Set focus with OtherFocusReason (7)
        self.element.setFocus(7)
        
        #return new stack item
        return inverse_obj





class special_QComboBox(QtGui.QComboBox):
    def __init__(self, parent=None):
        self.ignore_undoredo_action = False
        self.parent = parent
        super(special_QComboBox, self).__init__(parent)
        self.previous_state = self.currentIndex()
        
    def setCurrentIndex(self, index):
        self.previous_state = index
        super(special_QComboBox, self).setCurrentIndex(index)

class undoredo_item_QComboBox(object):
    def __init__(self, element):
        self.element = element
        self.prevstate = element.previous_state
        self.curstate = element.currentIndex()
        self.savedOn = False
        #Get current tab
        self.tab = element.window().ui.tabWidget.currentIndex()
        #set current listwidget if necessary
        self.current_listwidget = None
        self.current_listwidget_row = 0
        if self.tab == 2:
            self.current_listwidget = element.window().ui.WLGwatchlistItemsList
            self.current_listwidget_row = self.current_listwidget.currentRow()
        elif self.tab == 3:
            self.current_listwidget = element.window().ui.avoidlistItemsList
            self.current_listwidget_row = element.window().ui.avoidlistItemsList.currentRow()
        
    def execute(self, prev_item):
        #Initiate undo or redo op
        #Change tab, listwidget item if necessary, and set focus
        self.element.window().ui.tabWidget.setCurrentIndex(self.tab)
        if self.current_listwidget is not None:
            self.current_listwidget.setCurrentRow(self.current_listwidget_row)
        self.element.setFocus(QtCore.Qt.OtherFocusReason)
        #Create our inverse object
        inverse_obj = undoredo_item_QComboBox(self.element)
        #Update obj with new prevstate
        self.element.setCurrentIndex(self.prevstate)
        #set new prevstate
        self.element.previous_state = prev_item.prevstate
        
        
        #return new stack item
        return inverse_obj


class special_QSpinBox(QtGui.QSpinBox):
    def __init__(self, parent=None):
        self.ignore_undoredo_action = False
        self.parent = parent
        super(special_QSpinBox, self).__init__(parent)
        self.previous_value = self.value()
        self.firstSet = True
        #Disable standard context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    
    #Override the QTextEdit standard shortcuts and use global ones
    def event(self, event): 
        if event.type() == QtCore.QEvent.ShortcutOverride:
            return False 
        return QtGui.QSpinBox.event(self, event)
    
    def customContextMenu(self, pos):
        self.window().ui.menu_Edit.popup(self.mapToGlobal(pos))
        
    def setValue(self, newval):
        self.previous_value = newval
        super(special_QSpinBox, self).setValue(newval)

class undoredo_item_QSpinBox(object):
    def __init__(self, element, is_list_widget=None):
        self.element = element
        self.prevstate = element.previous_value
        self.curstate = element.value()
        self.savedOn = False
        #Get current tab
        self.tab = element.window().ui.tabWidget.currentIndex()
        
    def execute(self, prev_item):
        #Initiate undo or redo op
        #Change tab and set focus
        self.element.window().ui.tabWidget.setCurrentIndex(self.tab)
        self.element.setFocus(QtCore.Qt.OtherFocusReason)
        #Create our inverse object
        inverse_obj = undoredo_item_QSpinBox(self.element)
        #Update obj with new prevstate
        self.element.setValue(self.prevstate)
        #set new prevstate
        self.element.previous_value = prev_item.prevstate
        
        
        #return new stack item
        return inverse_obj





class special_QListWidget(QtGui.QListWidget):
    def __init__(self, parent=None):
        self.ignore_undoredo_action = False
        self.parent = parent
        super(special_QListWidget, self).__init__(parent)

class undoredo_item_QListWidget(object):
    def __init__(self, element, item, set_row, op=None):
        self.element = element
        self.savedOn = False
        self.item = item
        self.op = op
        #Get current tab
        self.tab = element.window().ui.tabWidget.currentIndex()
        #set current listwidget
        self.current_listwidget = element
        self.current_listwidget_row = set_row
        
        
    def execute(self, prev_item):
        #Initiate undo or redo op
        #Change tab
        self.element.window().ui.tabWidget.setCurrentIndex(self.tab)
        #Add or remove item from list
        if self.op == "add":
            iop = "rem"
            #Remove and save the removed item for our inverse_obj
            inverse_item = self.element.takeItem(self.current_listwidget_row)
            #Set focus to whatever item is below us if possible
            if self.element.count() == self.current_listwidget_row:
                self.element.setCurrentRow(self.current_listwidget_row-1)
            else:
                self.element.setCurrentRow(self.current_listwidget_row)
        elif self.op == "rem":
            iop = "add"
            inverse_item = self.item
            self.element.insertItem(self.current_listwidget_row, self.item)
            #Set focus to new item
            self.element.setCurrentItem(self.item)
            
        #Create our inverse object
        inverse_obj = undoredo_item_QListWidget(self.element, inverse_item, self.current_listwidget_row, op=iop)
        #return new stack item
        return inverse_obj

class undoRedoSystem(object):
    def __init__(self, context):
        self.context = context
        self.MW = self.context.MainWindow
        self.undo_stack = []
        self.redo_stack = []
        
    def setupSlots(self):
        #Here we do a simple type comparison to determine which cmd_ object to use for our undo/redo system
        for section, element_list in self.context.SettingsManager.guiDefaults.iteritems():
            for element in element_list:
                #In the future, use self.context.findChild(QtCore.QObject, "myObjectName")
                #If you dont have context for the mainWindow context use element.window().ui
                live_element = eval("self.context.%s" % element)
                #Set up our connections
                if "special_QLineEdit" in str(type(live_element)):
                    QtCore.QObject.connect(live_element, QtCore.SIGNAL(_fromUtf8("textChanged(QString)")), self.new_undoredo_QLineEdit)
                    QtCore.QObject.connect(live_element, QtCore.SIGNAL(_fromUtf8("customContextMenuRequested(QPoint)")), live_element.customContextMenu)
                    
                elif "special_QTextEdit" in str(type(live_element)):
                        QtCore.QObject.connect(live_element, QtCore.SIGNAL(_fromUtf8("textChanged()")), self.new_undoredo_QTextEdit)
                        QtCore.QObject.connect(live_element, QtCore.SIGNAL(_fromUtf8("customContextMenuRequested(QPoint)")), live_element.customContextMenu)
                
                elif "special_QCheckBox" in str(type(live_element)):
                        QtCore.QObject.connect(live_element, QtCore.SIGNAL(_fromUtf8("stateChanged(int)")), self.new_undoredo_QCheckBox)
                        
                elif "special_QComboBox" in str(type(live_element)):
                        QtCore.QObject.connect(live_element, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), self.new_undoredo_QComboBox)
                
                elif "special_QSpinBox" in str(type(live_element)):
                        QtCore.QObject.connect(live_element, QtCore.SIGNAL(_fromUtf8("valueChanged(int)")), self.new_undoredo_QSpinBox)
                        QtCore.QObject.connect(live_element, QtCore.SIGNAL(_fromUtf8("customContextMenuRequested(QPoint)")), live_element.customContextMenu)
    
    def reset(self):
        self.undo_stack = []
        self.context.actionUndo.setEnabled(False)
        self.redo_stack = []
        self.context.actionRedo.setEnabled(False)
    
    def undo(self):
        #pop last stack item and execute it, then set the return obj
        try:
            op_item = self.undo_stack.pop(-1)
        except:
            return
        new_stack_item = op_item.execute(op_item)
        self.redo_stack.append(new_stack_item)
        #Disable undo action if we are out of undo items
        if len(self.undo_stack) == 0:
            self.context.actionUndo.setEnabled(False)
        #Enable redo action
        self.context.actionRedo.setEnabled(True)
        
    
    def redo(self):
        #Same as above
        try:
            op_item = self.redo_stack.pop(-1)
        except:
            return
        new_stack_item = op_item.execute(op_item)
        self.undo_stack.append(new_stack_item)
        #Disable redo action if we are out of redo items
        if len(self.redo_stack) == 0:
            self.context.actionRedo.setEnabled(False)
        #Enable undo action
        self.context.actionUndo.setEnabled(True)
    
    def add_undo_item(self, stack_item):
        self.undo_stack.append(stack_item)
        self.context.actionUndo.setEnabled(True)
        #Clear out redo history since we have now changed
        self.redo_stack = []
        self.context.actionRedo.setEnabled(False)

    def new_undoredo_QLineEdit(self):
        element = self.MW.sender()
        if element.ignore_undoredo_action == True:
            element.ignore_undoredo_action = False
            return
        if element.text() == element.previous_text:
            return
        stack_item = undoredo_item_QLineEdit(element)
        self.add_undo_item(stack_item)
        element.previous_text = element.text()
        
        
        
    def new_undoredo_QTextEdit(self):
        element = self.MW.sender()
        if element.ignore_undoredo_action == True:
            element.ignore_undoredo_action = False
            return
        if element.toPlainText() == element.previous_text:
            return
        stack_item = undoredo_item_QTextEdit(element)
        self.add_undo_item(stack_item)
        element.previous_text = element.toPlainText()
        
        
    def new_undoredo_QCheckBox(self):
        element = self.MW.sender()       
        if element.ignore_undoredo_action == True:
            element.ignore_undoredo_action = False
            return
        if element.checkState() == element.previous_state:
            return
        stack_item = undoredo_item_QCheckBox(element)
        self.add_undo_item(stack_item)
        element.previous_state = element.checkState()
        
        
    def new_undoredo_QComboBox(self):
        element = self.MW.sender()
        if element.ignore_undoredo_action == True:
            element.ignore_undoredo_action = False
            return
        if element.currentIndex() == element.previous_state:
            return
        stack_item = undoredo_item_QComboBox(element)
        self.add_undo_item(stack_item)
        element.previous_state = element.currentIndex()
        
    def new_undoredo_QSpinBox(self):
        element = self.MW.sender()
        if element.ignore_undoredo_action == True:
            element.ignore_undoredo_action = False
            if element.firstSet == True:
                element.firstSet = False
            else:
                return
        if element.value() == element.previous_value:
            return
        stack_item = undoredo_item_QSpinBox(element)
        self.add_undo_item(stack_item)
        element.previous_value = element.value()
        
    def new_undoredo_QListWidget(self, element, item, op=None):
        if element.ignore_undoredo_action == True:
            element.ignore_undoredo_action = False
            if element.firstSet == True:
                element.firstSet = False
            else:
                return
        stack_item = undoredo_item_QListWidget(element, item, element.currentRow(), op=op)
        self.add_undo_item(stack_item)




