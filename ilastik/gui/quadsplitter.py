from PyQt4.QtCore import *
from PyQt4.QtGui import *

import sys

from ilastik.gui.iconMgr import ilastikIcons 

class DockableContainer(QWidget):
    isDocked = True
    replaceWidget = None
    mainLayout = None
    maximized = False
    
    def __init__(self, number, parent=None):
        QWidget.__init__(self, parent)
        
        #self.replaceWidget = QTextEdit(None)
        #self.replaceWidget.setDocument(QTextDocument("replace widget %d" % (number)))
        self.replaceWidget = QWidget(None)
        self.replaceWidget.setObjectName("replaceWidget_%d" % (number))
        
        self.dockButton = QPushButton(None)
        self.dockButton.setObjectName("%d" % (number))
        self.dockButton.setFlat(True)
        self.dockButton.setAutoFillBackground(True)
        self.dockButton.setIcon(QIcon(QPixmap(ilastikIcons.ArrowUpx10)))
        self.dockButton.setIconSize(QSize(10,10));
        self.dockButton.setFixedSize(10,10)
        self.dockButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        self.maximizeButton = QPushButton(None)
        self.maximizeButton.setObjectName("%d" % (number))
        self.maximizeButton.setFlat(True)
        self.maximizeButton.setAutoFillBackground(True)
        self.maximizeButton.setIcon(QIcon(QPixmap(ilastikIcons.Maximizex10)))
        self.maximizeButton.setIconSize(QSize(10,10));
        self.maximizeButton.setFixedSize(10,10)
        self.maximizeButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        h = QHBoxLayout(None)
        h.addStretch()
        h.addWidget(self.maximizeButton)
        h.addWidget(self.dockButton)
        
        self.mainLayout = QVBoxLayout(None)
        self.mainLayout.addItem(h)
        
        self.mainWidget = QTextEdit(None); self.mainWidget.setDocument(QTextDocument("MAIN widget %d" % (number)))
        self.mainLayout.addWidget(self.mainWidget)
        
        self.setLayout(self.mainLayout)
        
        self.connect(self.dockButton, SIGNAL('clicked()'), self.__onDockButtonClicked )
        self.connect(self.maximizeButton, SIGNAL('clicked()'), self.__onMaximizeButtonClicked )
    
    def __del__(self):
        print "destruct dockabled widget"
        if not self.isDocked:
            del self
    
    def __onMaximizeButtonClicked(self):
        self.maximized = not self.maximized
        self.dockButton.setEnabled(not self.maximized)
        self.emit(SIGNAL('maximize(bool)'), self.maximized)
    
    def __onDockButtonClicked(self):
        self.setDocked(not self.isDocked)
    
    def setDocked(self, docked):
        if docked:
            self.dockButton.setIcon(QIcon(QPixmap(ilastikIcons.ArrowUpx10)))
        else:
            self.dockButton.setIcon(QIcon(QPixmap(ilastikIcons.ArrowDownx10)))
        
        if not docked:
            self.emit(SIGNAL('undock()'))
            widgetSize = self.size()
            self.setParent(None, Qt.Window)
            self.setWindowFlags(Qt.WindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint))
            self.show()
        else:
            self.emit(SIGNAL('dock()'))
            
        self.isDocked = not self.isDocked
        
        

class QuadView(QWidget):
    dockButton        = 4*[None]
    dockableContainer = 4*[None]
    firstTime = True
    maximized = False
    
    def horizontalSplitterMoved(self):
        w, h = self.size().width()-self.splitHorizontal1.handleWidth(), self.size().height()-self.splitVertical.handleWidth()
        
        w1  = [self.dockableContainer[i].mainLayout.minimumSize().width() for i in [0,2] ]
        w2  = [self.dockableContainer[i].mainLayout.minimumSize().width() for i in [1,3] ]
        wLeft  = max(w1)
        wRight = max(w2)
        
        #print "moved"
        if self.sender().objectName() == "splitter1":
            s = self.splitHorizontal1.sizes()
            if s[0] < wLeft or s[1] < wRight:
                self.splitHorizontal1.setSizes(self.splitHorizontal2.sizes())
            else:
                self.splitHorizontal2.setSizes( self.splitHorizontal1.sizes() )

        if self.sender().objectName() == "splitter2":
            s = self.splitHorizontal2.sizes()
            if s[0] < wLeft or s[1] < wRight:
                self.splitHorizontal2.setSizes( self.splitHorizontal1.sizes() )
            else:
                self.splitHorizontal1.setSizes( self.splitHorizontal2.sizes() )
    
    def addWidget(self, i, widget):
        assert 0 <= i < 4, "range of i"
        
        #widget.setMinimumSize(QSize(0,0))

        w = self.dockableContainer[i]
        oldMainWidget = w.mainWidget
        w.mainWidget = widget
        oldMainWidget.setParent(None); del oldMainWidget
        w.mainLayout.addWidget(w.mainWidget)
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        #split up <-> down
        self.splitVertical    = QSplitter(Qt.Vertical, self)
        self.splitVertical.setChildrenCollapsible(False)
        #split left <-> right
        self.splitHorizontal1 = QSplitter(Qt.Horizontal, self.splitVertical)
        self.splitHorizontal1.setChildrenCollapsible(False)
        self.splitHorizontal1.setObjectName("splitter1")
        self.splitHorizontal2 = QSplitter(Qt.Horizontal, self.splitVertical)
        self.splitHorizontal2.setObjectName("splitter2")
        self.splitHorizontal2.setChildrenCollapsible(False)
        
        for i in range(4):
            if i<2:
                self.dockableContainer[i] = DockableContainer(i, self.splitHorizontal1)
            else:
                self.dockableContainer[i] = DockableContainer(i, self.splitHorizontal2)
            self.dockableContainer[i].setObjectName("%d" % (i))
            self.connect(self.dockableContainer[i], SIGNAL('dock()'), self.dockContainer )
            self.connect(self.dockableContainer[i], SIGNAL('undock()'), self.undockContainer )
            self.connect(self.dockableContainer[i], SIGNAL('maximize(bool)'), self.maximizeContainer )
        
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.splitVertical)
        self.setLayout(self.layout)
        
        self.connect( self.splitHorizontal1, SIGNAL( 'splitterMoved( int, int )'), self.horizontalSplitterMoved)
        self.connect( self.splitHorizontal2, SIGNAL( 'splitterMoved( int, int )'), self.horizontalSplitterMoved)

    def __del__(self):
        print "destruct QuadView"
        for i in range(4):
            if not self.dockableContainer[i]:
                print "deleting undocked widget", i
                del self.dockableContainer[i]
            else:
                print "widget %d is docked" % (i)

    def setMaximized(self, maximized, i):
        if maximized:
            self.splitVertical.setParent(None)
            self.layout.addWidget(self.dockableContainer[i])
        else:
            for i in range(4):
                self.dockableContainer[i].setParent(None)
            for i in range(4):
                if i<2:
                    self.dockableContainer[i].setParent(self.splitHorizontal1)
                else:
                    self.dockableContainer[i].setParent(self.splitHorizontal2)
            self.layout.addWidget(self.splitVertical)
            self.__resizeEqual()
        self.maximized = maximized
    
    def toggleMaximized(self, i):
        self.setMaximized(not self.maximized, i)
    
    def maximizeContainer(self, maximized):
        print "maximized =", maximized
        i = int(self.sender().objectName())
        self.setMaximized(maximized, i)
    
    def deleteUndocked(self):
        print "delete undocked"
        toDelete = []
        for i in range(4):
            if not self.dockableContainer[i].isDocked:
                print "deleting undocked widget", i
                toDelete.append( self.dockableContainer[i] )
            else:
                print "widget %d is docked" % (i)
        for x in toDelete: x.deleteLater()

    def resizeEvent(self, event):
        print "resizeEvent:",self.size()
        if self.firstTime:
            self.__resizeEqual()
            self.firstTime=False
    
    def __resizeEqual(self):
        w, h = self.size().width()-self.splitHorizontal1.handleWidth(), self.size().height()-self.splitVertical.handleWidth()
        
        w1  = [self.dockableContainer[i].mainLayout.minimumSize().width() for i in [0,2] ]
        w2  = [self.dockableContainer[i].mainLayout.minimumSize().width() for i in [1,3] ]
        #print w1, w2
        wLeft  = max(w1)
        wRight = max(w2)
        #print 'wLeft=',wLeft, 'wRight=',wRight
        if wLeft > wRight and wLeft > w/2:
            wRight = w - wLeft
        elif wRight >= wLeft and wRight > w/2:
            wLeft = w - wRight
        else:
            wLeft = w/2
            wRight = w/2
        #print 'wLeft=',wLeft, 'wRight=',wRight
        self.splitHorizontal1.setSizes([wLeft, wRight+10])
        self.splitHorizontal2.setSizes([wLeft, wRight+10])
        #print "width=",w
        self.splitVertical.setSizes([h/2, h/2])
    
    def undockContainer(self):
        i = int(self.sender().objectName())
        w = self.dockableContainer[i]
        print "undock", i
        
        index = i
        splitter = self.splitHorizontal1
        if i>=2:
            index = i-2
            splitter = self.splitHorizontal2
        assert 0 <= index < 2
    
        size = w.size()
        splitter.widget(index).setParent(None)
        w.replaceWidget.resize(size)
        splitter.insertWidget(index, w.replaceWidget)
        
        if i<2:
            self.splitHorizontal2.setSizes( self.splitHorizontal1.sizes() )
        else:
            self.splitHorizontal1.setSizes( self.splitHorizontal2.sizes() )
            
        
        
    def dockContainer(self):
        i = int(self.sender().objectName())
        w = self.dockableContainer[i]
        assert not w.isDocked
        print "dock", i

        index = i
        splitter = self.splitHorizontal1
        if i>=2:
            index = i-2
            splitter = self.splitHorizontal2
        assert 0 <= index < 2

        splitter.widget(index).setParent(None)
        if i<2:
            self.splitHorizontal1.insertWidget(index, w)
        else:
            self.splitHorizontal2.insertWidget(index, w)

if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    
    class Window(QMainWindow):
        def __init__(self):
            QMainWindow.__init__(self)
            #self.setAttribute(Qt.WA_DeleteOnClose)
            
            widget= QWidget()
            mainLayout = QVBoxLayout()
            self.q = QuadView(self)
            
            for i in range(4):
                edit = QTextEdit()
                edit.setDocument(QTextDocument("view %d" % (i)))
                edit.setMinimumSize(200+100*i,200+100*i)
                print "setting minimum size to", 200+100*i, 200+100*i
                self.q.addWidget(i, edit)
            
            mainLayout.addWidget(self.q)
            self.setCentralWidget(widget)
            widget.setLayout(mainLayout)
        
        def closeEvent(self, event):
            print "close event"
            self.q.deleteUndocked()
            self.deleteLater()

    window = Window()
    window.show()
    app.exec_()
