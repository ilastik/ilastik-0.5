from PyQt4 import QtGui

from enthought.traits.api import HasTraits, Instance, on_trait_change
from enthought.traits.ui.api import View, Item

from enthought.mayavi.core.api import PipelineBase
from enthought.mayavi.core.ui.api import MayaviScene, SceneEditor, MlabSceneModel

################################################################################
# Some logic to select 'mesh' and the _data index when picking.
from enthought.tvtk.api import tvtk

################################################################################
# Some logic to pick on click but no move
#*******************************************************************************
# M v t P i c k e r                                                            *
#*******************************************************************************

class MvtPicker(object):
    mouse_mvt = False

    def __init__(self, picker, scene):
        self.picker = picker
        self.scene = scene
        self.lastX = 0
        self.lastY = 0
        self.mouse_mvt = True

    def on_button_press(self, obj, evt):
        """
        picking on double click
        """
        x, y = obj.GetEventPosition()
        if not self.mouse_mvt and x == self.lastX and y == self.lastY:
            self.picker.pick((x, y, 0), self.scene.renderer)
        self.lastX = x
        self.lastY = y
        self.mouse_mvt = False

    def on_mouse_move(self, obj, evt):
        self.mouse_mvt = True

    def on_button_release(self, obj, evt):
        pass
        






################################################################################
#The actual visualization
#*******************************************************************************
# M a y a 3 D S c e n e                                                        *
#*******************************************************************************

class Maya3DScene(HasTraits):

    scene = Instance(MlabSceneModel, ())

    plot = Instance(PipelineBase)


    def __init__(self, volumeEditor, overlayItemReference, raw):
        HasTraits.__init__(self)
        self.volumeEditor = volumeEditor
        self.overlayItemReference = overlayItemReference
        self.raw = raw
        #print self.item.shape, self.item.dtype


        

    # When the scene is activated, or when the parameters are changed, we
    # update the plot.
    @on_trait_change('scene.activated')
    def update_plot(self):
        if self.plot is None:
            stuff = self.overlayItemReference._data[0,:,:,:,self.overlayItemReference.channel]
            print stuff.__class__
            print stuff.shape, stuff.dtype
            self.dataField = self.scene.mlab.pipeline.scalar_field(stuff)
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
            
            self.plot = self.scene.mlab.pipeline.iso_surface(self.dataField, contours=[1,2]) #opacity=0.4
#            cm = numpy.zeros((256,4),'uint8')#self.plot.module_manager.scalar_lut_manager.lut.table.to_array()
#            
#            cm[:,3] = 255
#            
#            for index in range(0,255):
#                c = self.overlayItemReference.colorTable[index]
#                c = QtGui.QColor.fromRgba(c)
#                print index, " ", c.red(), " ", c.green()
#                cm[index,0] = c.red()
#                cm[index,1] = c.green()
#                cm[index,2] = c.blue()
#            
#            mlab.colorbar(title="LUT", orientation="vertical")
#
#            self.plot.module_manager.scalar_lut_manager.lut.number_of_colors = 256 
#            self.plot.module_manager.scalar_lut_manager.lut.table_range = (0,255)
#            self.plot.module_manager.scalar_lut_manager.lut.range = (0,255)
#            self.plot.module_manager.scalar_lut_manager.lut.value_range = (0,255)
#            self.plot.module_manager.scalar_lut_manager.lut.vector_mode  = 'magnitude'
#            self.plot.module_manager.scalar_lut_manager.lut.table = cm
#            
#            
#            print self.plot
#            
#            print self.plot.module_manager.scalar_lut_manager.lut
            
            
            #self.scene.mlab.pipeline.volume(self.scene.mlab.pipeline.scalar_field(self.item._data[0,:,:,:,0]), vmin=0.5, vmax=1.5)
            #self.scene.mlab.outline()
        else:
            self.plot.mlab_source.set(self.item._data[0,:,:,:,0])
            
        az, elev, dist, focal = self.scene.mlab.view()
        
        self.scene.mlab.view(-90, 175, dist, focal)  # <- top view
        
        self.scene.picker.pointpicker.add_observer('EndPickEvent', self.picker_callback)

        self.mvt_picker = MvtPicker(self.scene.picker.pointpicker, self.scene)
        
        self.scene.interactor.add_observer('LeftButtonPressEvent', 
                                        self.mvt_picker.on_button_press)
        self.scene.interactor.add_observer('MouseMoveEvent', 
                                        self.mvt_picker.on_mouse_move)
        self.scene.interactor.add_observer('LeftButtonReleaseEvent', 
                                        self.mvt_picker.on_button_release)

    def picker_callback(self,picker_obj, evt):
        print self.scene.mlab.view()
        picker_obj = tvtk.to_tvtk(picker_obj)
        position =  picker_obj.pick_position
        self.volumeEditor.changeSlice(int(position[0]-1),0)
        self.volumeEditor.changeSlice(int(position[1]-1),1)
        self.volumeEditor.changeSlice(int(position[2]-1),2)
        





    # The layout of the dialog created
    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                     height=480, width=640, show_label=False),
                resizable=True

                )


################################################################################
# The QWidget containing the visualization, this is pure PyQt4 code.
#*******************************************************************************
# M a y a v i Q W i d g e t                                                    *
#*******************************************************************************

class MayaviQWidget(QtGui.QWidget):
    def __init__(self, volumeEditor, overlayItemReference, raw):
        QtGui.QWidget.__init__(self)
        self.volumeEditor = volumeEditor
        self.overlayItemReference = overlayItemReference
        layout = QtGui.QVBoxLayout(self)
        layout.setMargin(0)
        layout.setSpacing(0)
        self.visualization = Maya3DScene(self.volumeEditor, self.overlayItemReference, raw)

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