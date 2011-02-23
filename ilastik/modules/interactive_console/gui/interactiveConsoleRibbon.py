import code

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase
from ilastik.gui.overlayWidget import OverlayWidget

from PyQt4 import QtGui, QtCore

try:
    from shellWidget import SciShell
                
#*******************************************************************************
# C o n s o l e T a b                                                          *
#*******************************************************************************

    class ConsoleTab(IlastikTabBase, QtGui.QWidget):
        name = 'Interactive Console'
        position = 1
        moduleName = "Interactive_Console" 
        
        def __init__(self, parent=None):
            IlastikTabBase.__init__(self, parent)
            QtGui.QWidget.__init__(self, parent)
            
            self.consoleWidget = None
            
            self._initContent()
            self._initConnects()
            
        def on_activation(self):
            if self.ilastik.project is None:
                return
            ovs = self.ilastik._activeImage.module[self.__class__.moduleName].getOverlayRefs()
            if len(ovs) == 0:
                raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
                if raw is not None:
                    ovs.append(raw.getRef())
            
            self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget
    
            overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
            self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
            
            self.ilastik.labelWidget.setLabelWidget(DummyLabelWidget())
            
            
            self.volumeEditorVisible = self.ilastik.volumeEditorDock.isVisible()
            self.ilastik.volumeEditorDock.setVisible(False)
            
            if self.consoleWidget is None:
                locals = {}
                locals["activeImage"] = self.ilastik._activeImage
                locals["dataMgr"] = self.ilastik.project.dataMgr
                self.interpreter = code.InteractiveInterpreter(locals)
                self.consoleWidget = SciShell(self.interpreter)
                
                dock = QtGui.QDockWidget("ilastik interactive console", self.ilastik)
                dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.TopDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
                dock.setWidget(self.consoleWidget)
                
                self.consoleDock = dock
        
               
                area = QtCore.Qt.BottomDockWidgetArea
                self.ilastik.addDockWidget(area, dock)
            self.consoleDock.setVisible(True)
            self.consoleDock.setFocus()
            self.consoleWidget.multipleRedirection(True)
            
        
        def on_deActivation(self):
            if self.consoleWidget is not None:
                self.consoleWidget.multipleRedirection(False)
                self.consoleWidget.releaseKeyboard()
                self.consoleDock.setVisible(False)
                self.ilastik.volumeEditorDock.setVisible(self.volumeEditorVisible)
            
        def _initContent(self):
            self.setLayout(QtGui.QHBoxLayout())
        
        def _initConnects(self):
            pass
except:
    print "Console Tab error"    
