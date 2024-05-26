from collections import OrderedDict
from compas_timber.fabrication import BTLx
from compas_timber.fabrication import BTLxProcess


class BTLxFrenchRidgeLap(object):
    """
    BTLxFrenchRidgeLap represents a fabrication process for creating a French Ridge Lap joint.

    Parameters
    ----------
    part : :class:`~compas_timber.fabrication.btlx_part.BTLxPart`
        The BTLxPart object representing the beam.
    joint : :class:`~compas_timber.connections.joint.Joint`
        The joint object.
    is_top : bool
        Flag indicating if the part is the top part or bottom part.

    Attributes
    ----------
    PROCESS_TYPE : str
        The type of the process, which is "FrenchRidgeLap".
    beam : :class:`~compas_timber.parts.beam.Beam`
        The beam object associated with the part.
    other_beam : :class:`~compas_timber.parts.beam.Beam`
        The other beam object associated with the joint.
    part : :class:`~compas_timber.fabrication.btlx_part.BTLxPart`
        The BTLxPart object this process is applied to.
    joint : :class:`~compas_timber.connections.joint.Joint`
        The joint object.
    orientation : str
        Indicates which end of the beam this join is applied to.
    drill_hole_diameter : float
        The diameter of the drill hole.
    ref_face_index : int
        The index of the reference face.
    ref_face : :class:`~compas.geometry.Frame`
        The reference surface frame object.
    header_attributes : dict
        The header attributes for the process.
    process_parameters : dict
        The process parameters that define the geometric parameters of the BTLx process.
    angle : float
        The angle of the joint in degrees.

    """

    PROCESS_TYPE = "FrenchRidgeLap"

    def __init__(self, param_dict, joint_name=None, **kwargs):
        self.apply_process = True
        self.reference_plane_id = param_dict["ReferencePlaneID"]
        self.orientation = param_dict["Orientation"]
        self.start_x = param_dict["StartX"]
        self.angle = param_dict["Angle"]
        self.ref_edge = param_dict["RefPosition"]
        self.drill_hole = param_dict["Drillhole"]
        self.drill_hole_diameter = param_dict["DrillholeDiam"]

        for key, value in param_dict.items():
            setattr(self, key, value)

        for key, value in kwargs.items():
            setattr(self, key, value)

        if joint_name:
            self.name = joint_name
        else:
            self.name = "french_ridge_lap"

    @property
    def header_attributes(self):
        """the following attributes are required for all processes, but the keys and values of header_attributes are process specific."""

        return {
            "Name": self.name,
            "Process": "yes",
            "Priority": "0",
            "ProcessID": "0",
            "ReferencePlaneID": str(self.reference_plane_id),
        }

    @property
    def process_params(self):
        """This property is required for all process types. It returns a dict with the geometric parameters to fabricate the joint."""

        if self.apply_process:
            """the following attributes are specific to FrenchRidgeLap"""
            od = OrderedDict(
                [
                    ("Orientation", str(self.orientation)),
                    ("StartX", "{:.{prec}f}".format(self.start_x, prec=BTLx.POINT_PRECISION)),
                    ("Angle", "{:.{prec}f}".format(self.angle, prec=BTLx.ANGLE_PRECISION)),
                    ("RefPosition", self.ref_edge),
                    ("Drillhole", self.drill_hole),
                    ("DrillholeDiam", "{:.{prec}f}".format(self.drill_hole_diameter, prec=BTLx.POINT_PRECISION)),
                ]
            )
            return od
        else:
            return None

    @classmethod
    def create_process(cls, param_dict, joint_name=None, **kwargs):
        """Creates a french-ridge lap process from a dictionary of parameters."""
        frenh_ridge_lap = BTLxFrenchRidgeLap(param_dict, joint_name, **kwargs)
        return BTLxProcess(BTLxFrenchRidgeLap.PROCESS_TYPE, frenh_ridge_lap.header_attributes, frenh_ridge_lap.process_params)
