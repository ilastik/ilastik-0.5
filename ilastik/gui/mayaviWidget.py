from PyQt4 import QtCore, QtGui
import vigra, numpy
import sip
import os
from overlaySelectionDlg import OverlaySelectionDialog


from ilastik.core.volume import DataAccessor, Volume, VolumeLabels, VolumeLabelDescription
from ilastik.core.overlayMgr import OverlayMgr,  OverlayItem, OverlaySlice
from ilastik.core.volume import DataAccessor, Volume, VolumeLabels, VolumeLabelDescription


from enthought.traits.api import HasTraits, Range, Instance, on_trait_change
from enthought.traits.ui.api import View, Item, Group

from enthought.mayavi import mlab
from enthought.mayavi.core.api import PipelineBase
from enthought.mayavi.core.ui.api import MayaviScene, SceneEditor, MlabSceneModel


################################################################################
#The actual visualization
class Maya3DScene(HasTraits):

    scene = Instance(MlabSceneModel, ())

    plot = Instance(PipelineBase)


    def __init__(self, item, raw):
        HasTraits.__init__(self)
        
        self.item = item
        self.raw = raw
        print self.item.shape, self.item.dtype
        

    # When the scene is activated, or when the parameters are changed, we
    # update the plot.
    @on_trait_change('scene.activated')
    def update_plot(self):
        if self.plot is None:
            self.dataField = self.scene.mlab.pipeline.scalar_field(self.item)
            self.rawField = self.scene.mlab.pipeline.scalar_field(self.raw)


#            self.xp = self.scene.mlab.pipeline.image_plane_widget(self.rawField,
#                            plane_orientation='x_axes',
#                            slice_index=10
#                            )
#            def move_slicex(obj, evt):
#                #print obj
#                print obj.GetCurrentCursorPosition()
#                print self.xp.ipw.slice_position
#
#            self.xp.ipw.add_observer('EndInteractionEvent', move_slicex)
#
#            self.yp = self.scene.mlab.pipeline.image_plane_widget(self.rawField,
#                            plane_orientation='y_axes',
#                            slice_index=10
#                        )
#            def move_slicey(obj, evt):
#                #print obj
#                print obj.GetCurrentCursorPosition()
#                print self.yp.ipw.slice_position
#
#            self.yp.ipw.add_observer('EndInteractionEvent', move_slicey)
#
#            self.zp = self.scene.mlab.pipeline.image_plane_widget(self.rawField,
#                            plane_orientation='z_axes',
#                            slice_index=10
#                        )
#            def move_slicez(obj, evt):
#                #print obj
#                print obj.GetCurrentCursorPosition()
#                print self.zp.ipw.slice_position
#
#            self.zp.ipw.add_observer('EndInteractionEvent', move_slicez)

            self.plot = self.scene.mlab.pipeline.iso_surface(self.dataField, opacity=0.4, contours=[2, 3, 4, 5, 6, 7])
            
            #self.scene.mlab.pipeline.volume(self.scene.mlab.pipeline.scalar_field(self.item.data[0,:,:,:,0]), vmin=0.5, vmax=1.5)
            #self.scene.mlab.outline()
        else:
            self.plot.mlab_source.set(self.item.data[0,:,:,:,0])


    # The layout of the dialog created
    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                     height=480, width=640, show_label=False),
                resizable=True

                )


################################################################################
# The QWidget containing the visualization, this is pure PyQt4 code.
class MayaviQWidget(QtGui.QWidget):
    def __init__(self, item, raw):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QVBoxLayout(self)
        layout.setMargin(0)
        layout.setSpacing(0)
        self.visualization = Maya3DScene(item, raw)

        # If you want to debug, beware that you need to remove the Qt
        # input hook.
        #QtCore.pyqtRemoveInputHook()
        #import pdb ; pdb.set_trace()
        #QtCore.pyqtRestoreInputHook()

        # The edit_traits call will generate the widget to embed.
        self.ui = self.visualization.edit_traits(parent=self,
                                                 kind='subpanel').control
        layout.addWidget(self.ui)
        self.ui.setParent(self)

    def closeEvent(self, ev):
        self.ui.setVisible(False)
        #mlab.close()