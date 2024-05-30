import math

from compas.geometry import Frame
from compas.geometry import angle_vectors
from compas.geometry import cross_vectors
from compas.geometry import dot_vectors

from .joint import BeamJoinningError
from .joint import Joint
from .solver import JointTopology


class FrenchRidgeLapJoint(Joint):
    """Represents a French Ridge Lap type joint which joins two beam at their ends.

    This joint type is compatible with beams in L topology.

    Please use `LButtJoint.create()` to properly create an instance of this class and associate it with an assembly.

    Parameters
    ----------
    assembly : :class:`~compas_timber.assembly.TimberAssembly`
        The assembly associated with the beams to be joined.
    beam_a : :class:`~compas_timber.parts.Beam`
        The top beam to be joined.
    beam_b : :class:`~compas_timber.parts.Beam`
        The bottom beam to be joined.

    Attributes
    ----------
    beams : list(:class:`~compas_timber.parts.Beam`)
        The beams joined by this joint.
    joint_type : str
        A string representation of this joint's type.
    reference_face_indices : dict
        A dictionary containing the indices of the reference faces for both beams.

    """

    SUPPORTED_TOPOLOGY = JointTopology.TOPO_L

    def __init__(self, main_beam=None, cross_beam=None, drill_diameter=0.0, **kwargs):
        super(FrenchRidgeLapJoint, self).__init__(main_beam, cross_beam, drill_diameter, **kwargs)
        self.main_beam= main_beam
        self.cross_beam = cross_beam
        self.main_beam_key = main_beam.key if main_beam else None
        self.cross_beam_key = cross_beam.key if cross_beam else None

        self.drill_diameter = float(drill_diameter)

        self.reference_face_indices = {}


    @property
    def __data__(self):
        data_dict = {
            "main_beam_key": self.main_beam_key,
            "cross_beam_key": self.cross_beam_key,
            "drill_diameter": self.drill_diameter,
        }
        data_dict.update(super(FrenchRidgeLapJoint, self).__data__)
        return data_dict

    @classmethod
    def __from_data__(cls, value):
        instance = cls(**value)
        instance.main_beam_key = value["main_beam_key"]
        instance.cross_beam_key = value["cross_beam_key"]
        instance.drill_diameter = value["drill_diameter"]
        return instance

    @property
    def beams(self):
        return [self.main_beam, self.cross_beam]

    def restore_beams_from_keys(self, assemly):
        """After de-serialization, resotres references to the main and cross beams saved in the assembly."""
        self.main_beam = assemly.find_by_key(self.main_beam_key)
        self.cross_beam = assemly.find_by_key(self.cross_beam_key)

    def flip_lap(self):
        """Ensure the top_part is more parallel to the predefined default axis."""
        default_axis = ([1, 0, 0])
        top_vect = self.main_beam.centerline.direction
        bottom_vect = self.cross_beam.centerline.direction

        top_dot = abs(dot_vectors(top_vect, default_axis))
        bottom_dot = abs(dot_vectors(bottom_vect, default_axis))

        # Determine which part is more parallel to the default axis and flip if necessary
        if top_dot < bottom_dot:
            self.main_beam, self.cross_beam = self.cross_beam, self.main_beam
            self.main_beam_key, self.cross_beam_key = self.cross_beam_key, self.main_beam_key
        return top_dot < bottom_dot

    @property
    def cutting_plane_top(self):
        _, cfr = self.get_face_most_towards_beam(self.main_beam, self.cross_beam, ignore_ends=True)
        cfr = Frame(cfr.point, cfr.xaxis, cfr.yaxis * -1.0)  # flip normal
        return cfr

    @property
    def cutting_plane_bottom(self):
        _, cfr = self.get_face_most_towards_beam(self.cross_beam, self.main_beam, ignore_ends=True)
        return cfr

    def add_extensions(self):
        self.main_beam.add_blank_extension(*self.main_beam.extension_to_plane(self.cutting_plane_top), joint_key=self.key)
        self.cross_beam.add_blank_extension(*self.cross_beam.extension_to_plane(self.cutting_plane_bottom), joint_key=self.key)

    def add_features(self):
        self.check_geometry()
        self.features = []

    def check_geometry(self):
        """
        This method checks whether the parts are aligned as necessary to create French Ridge Lap and determines which face is used as reference face for machining.
        """
        if not (self.main_beam and self.cross_beam):
            raise (BeamJoinningError(beams=self.beams, joint=self, debug_info="beams not set"))

        if not (self.main_beam.width == self.cross_beam.width and self.main_beam.height == self.cross_beam.height):
            raise (BeamJoinningError(beams=self.beams, joint=self, debug_info="beams are not of same size"))

        self.flip_lap()
        normal = cross_vectors(self.main_beam.frame.xaxis, self.cross_beam.frame.xaxis)

        indices = []

        if angle_vectors(normal, self.main_beam.frame.yaxis) < 0.001:
            indices.append(3)
        elif angle_vectors(normal, self.main_beam.frame.zaxis) < 0.001:
            indices.append(4)
        elif angle_vectors(normal, -self.main_beam.frame.yaxis) < 0.001:
            indices.append(1)
        elif angle_vectors(normal, -self.main_beam.frame.zaxis) < 0.001:
            indices.append(2)
        else:
            raise (
                BeamJoinningError(
                    beams=self.beams,
                    joint=self,
                    debug_info="part not aligned with corner normal, no French Ridge Lap possible",
                )
            )

        if abs(angle_vectors(normal, self.cross_beam.frame.yaxis) - math.pi) < 0.001:
            indices.append(3)
        elif abs(angle_vectors(normal, self.cross_beam.frame.zaxis) - math.pi) < 0.001:
            indices.append(4)
        elif abs(angle_vectors(normal, -self.cross_beam.frame.yaxis) - math.pi) < 0.001:
            indices.append(1)
        elif abs(angle_vectors(normal, -self.cross_beam.frame.zaxis) - math.pi) < 0.001:
            indices.append(2)
        else:
            raise (
                BeamJoinningError(
                    beams=self.beams,
                    joint=self,
                    debug_info="part not aligned with corner normal, no French Ridge Lap possible",
                )
            )
        self.reference_face_indices = {str(self.main_beam.key): 4, str(self.cross_beam.key): 2}



