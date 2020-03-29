import bpy
from bpy.props import *
from .. number.c_utils import offsetFloats
from ... events import executionCodeChanged
from .. vector.c_utils import offset3DVectors
from ... base_types import AnimationNode, VectorizedSocket
from ... data_structures import VirtualVector3DList, VirtualDoubleList

class OffsetSplineNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_OffsetSplineNode"
    bl_label = "Offset Spline"
    errorHandlingType = "EXCEPTION"

    def checkedPropertiesChanged(self, context):
        self.updateSocketVisibility()
        executionCodeChanged()

    useLocation: BoolProperty(update = checkedPropertiesChanged)
    useRadius: BoolProperty(update = checkedPropertiesChanged)
    useTilt: BoolProperty(update = checkedPropertiesChanged)

    useVectorList: VectorizedSocket.newProperty()
    useRadiusList: VectorizedSocket.newProperty()
    useTiltList: VectorizedSocket.newProperty()

    def create(self):
        self.newInput("Spline", "Stroke", "spline", dataIsModified = True)
        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput(VectorizedSocket("Vector", "useVectorList",
            ("Location", "offsetLocations", dict(value = (0, 0, 1))),
            ("Locations", "offsetLocations")))
        self.newInput(VectorizedSocket("Float", "useRadiusList",
            ("Radius", "offsetRadius", dict(value = 1)),
            ("Radii", "offsetRadii")))
        self.newInput(VectorizedSocket("Float", "useTiltList",
            ("Tilt", "offsetTilt", dict(value = 1)),
            ("Tilts", "offsetTilts")))

        self.newOutput("Spline", "Stroke", "spline")

        self.updateSocketVisibility()

    def draw(self, layout):
        col = layout.column(align = True)

        row = col.row(align = True)
        row.prop(self, "useLocation", text = "Location", toggle = True)

        row = col.row(align = True)
        row.prop(self, "useRadius", text = "Radius", toggle = True)
        row.prop(self, "useTilt", text = "Tilt", toggle = True)

    def updateSocketVisibility(self):
        self.inputs[2].hide = not self.useLocation
        self.inputs[3].hide = not self.useRadius
        self.inputs[4].hide = not self.useTilt

    def execute(self, spline, falloff, offsetLocations, offsetRadii, offsetTilts):
        if not any((self.useLocation, self.useRadius, self.useTilt)):
            return spline

        falloffEvaluator = self.getFalloffEvaluator(falloff)
        influences = falloffEvaluator.evaluateList(spline.points)

        if self.useRadius:
            _offsetRadii = VirtualDoubleList.create(offsetRadii, 0)
            offsetFloats(spline.radii, _offsetRadii, influences)

        if self.useTilt:
            _offsetTilts = VirtualDoubleList.create(offsetTilts, 0)
            offsetFloats(spline.tilts, _offsetTilts, influences)

        if self.useLocation:
            _offsetLocations = VirtualVector3DList.create(offsetLocations, (0, 0, 0))
            offset3DVectors(spline.points, _offsetLocations, influences)
            if spline.type == "BEZIER":
                offset3DVectors(spline.leftHandles, _offsetLocations, influences)
                offset3DVectors(spline.rightHandles, _offsetLocations, influences)

        return spline

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")
