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
        self.parent = parent
        super(special_QLineEdit, self).__init__(parent)
        #Disable standard context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
               
    
    def setText(self, text):
        self.previous_text = text
        super(special_QLineEdit, self).setText(text)
    
    #Override the QLineEdit standard shortcuts and use global ones
    def event(self, event): 
        if event.type() == QtCore.QEvent.ShortcutOverride:
            return False 
        return QtGui.QLineEdit.event(self, event)
    
    def customContextMenu(self, pos):
        self.window().ui.menu_Edit.popup(self.mapToGlobal(pos))



class cmd_General_QLineEdit(object):
    def __init__(self, element, context):
        self.element = element
        self.context = context
        self.prevtext = element.previous_text
        self.curtext = element.text()
        self.savedOn = False
        
    def execute(self, prev_item):
        #Initiate undo or redo op
        #Create our inverse object
        inverse_obj = cmd_General_QLineEdit(self.element, self.context)
        #Update obj with new prevtext
        self.element.setText(self.prevtext)
        #set new prevtext
        self.element.previous_text = prev_item.prevtext
        #Set forcus with OtherFocusReason (7)
        self.element.setFocus(7)
        #preturn new stack item
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
                live_element = eval("self.context.%s" % element)
                #maybe instead of doing this here we can do a element.parent() and check its name in the new_undoredo_QLineEdit (or whatever other type func)
                if section == "watchlistDefaults":
                    pass
                if section == "avoidlistDefaults":
                    pass
                else:
                    #general options
                    if "special_QLineEdit" in str(type(live_element)):
                        #QtCore.QObject.connect(live_element, QtCore.SIGNAL(_fromUtf8("editingFinished()")), self.new_undoredo_QLineEdit)
                        QtCore.QObject.connect(live_element, QtCore.SIGNAL(_fromUtf8("textEdited(QString)")), self.new_undoredo_QLineEdit)
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
        #Disable undostack if we are out of undo items
        if len(self.undo_stack) == 0:
            self.context.actionUndo.setEnabled(False)
        #Enable redo stack
        self.context.actionRedo.setEnabled(True)
        
    
    def redo(self):
        #Same as above
        try:
            op_item = self.redo_stack.pop(-1)
        except:
            return
        new_stack_item = op_item.execute(op_item)
        self.undo_stack.append(new_stack_item)
        #Disable redostack if we are out of redo items
        if len(self.redo_stack) == 0:
            self.context.actionRedo.setEnabled(False)
        #Enable undo stack
        self.context.actionUndo.setEnabled(True)
        
    
    
    
    def new_undoredo_QLineEdit(self):
        element = self.MW.sender()
        if element.text() == element.previous_text:
            return
        stack_item = cmd_General_QLineEdit(element, self)
        self.undo_stack.append(stack_item)
        element.previous_text = element.text()
        #Enable undo menu item
        self.context.actionUndo.setEnabled(True)
        #Clear out redo history since we have now changed
        self.redo_stack = []
        self.context.actionRedo.setEnabled(False)