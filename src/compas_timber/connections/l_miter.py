from compas.geometry import Frame
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Vector
from compas.geometry import cross_vectors

from compas_timber.parts import BeamExtensionFeature
from compas_timber.parts import BeamTrimmingFeature
from compas_timber.utils import intersection_line_line_3D

from .joint import Joint
from .solver import JointTopology


class LMiterJoint(Joint):
    """Represents an L-Miter type joint which joins two beam in their ends, trimming them with a plane
    at the bisector angle between the beams' centerlines.

    This joint type is compatible with beams in L topology.

    Please use `LMiterJoint.create()` to properly create an instance of this class and associate it with an assembly.

    Parameters
    ----------
    assembly : :class:`~compas_timber.assembly.TimberAssembly`
        The assembly associated with the beams to be joined.
    beam_a : :class:`~compas_timber.parts.Beam`
        First beam to be joined.
    beam_b : :class:`~compas_timber.parts.Beam`
        Second beam to be joined.

    Attributes
    ----------
    beams : list(:class:`~compas_timber.parts.Beam`)
        The beams joined by this joint.
    cutting_planes : tuple(:class:`~compas.geometry.Frame`, :class:`~compas.geometry.Frame`)
        A trimming plane for each of the beams. The normals of the planes point at opposite directions.
    joint_type : str
        A string representation of this joint's type.

    """

    SUPPORTED_TOPOLOGY = JointTopology.TOPO_L

    def __init__(self, beam_a=None, beam_b=None, cutoff=None, frame=None, key=None):
        super(LMiterJoint, self).__init__(frame, key)
        self.beam_a = beam_a
        self.beam_b = beam_b
        self.beam_a_key = beam_a.key if beam_a else None
        self.beam_b_key = beam_b.key if beam_b else None
        self.cutoff = cutoff  # for very acute angles, limit the extension of the tip/beak of the joint
        self.features = []

    @property
    def data(self):
        data_dict = {
            "beam_a": self.beam_a_key,
            "beam_b": self.beam_b_key,
            "cutoff": self.cutoff,
        }
        data_dict.update(Joint.data.fget(self))
        return data_dict

    @classmethod
    def from_data(cls, value):
        instance = cls(frame=Frame.from_data(value["frame"]), key=value["key"], cutoff=value["cutoff"])
        instance.beam_a_key = value["beam_a"]
        instance.beam_b_key = value["beam_b"]
        instance.cutoff = value["cutoff"]
        return instance

    @property
    def joint_type(self):
        return "L-Miter"

    @property
    def beams(self):
        return [self.beam_a, self.beam_b]

    @property
    def cutting_planes(self):
        vA = Vector(*self.beam_a.frame.xaxis)  # frame.axis gives a reference, not a copy
        vB = Vector(*self.beam_b.frame.xaxis)

        # intersection point (average) of both centrelines
        [pxA, tA], [pxB, tB] = intersection_line_line_3D(
            self.beam_a.centerline,
            self.beam_b.centerline,
            max_distance=float("inf"),
            limit_to_segments=False,
        )
        # TODO: add error-trap + solution for I-miter joints

        p = Point((pxA.x + pxB.x) * 0.5, (pxA.y + pxB.y) * 0.5, (pxA.z + pxB.z) * 0.5)

        # makes sure they point outward of a joint point
        tA, _ = self.beam_a.endpoint_closest_to_point(pxA)
        if tA == "end":
            vA *= -1.0
        tB, _ = self.beam_b.endpoint_closest_to_point(pxB)
        if tB == "end":
            vB *= -1.0

        # bisector
        v_bisector = vA + vB
        v_bisector.unitize()

        # get frame
        v_perp = Vector(*cross_vectors(v_bisector, vA))
        v_normal = Vector(*cross_vectors(v_bisector, v_perp))

        plnA = Plane(p, v_normal)
        plnB = Plane(p, v_normal * -1.0)

        plnA = Frame.from_plane(plnA)
        plnB = Frame.from_plane(plnB)
        return plnA, plnB

    def add_features(self):
        """Adds the required extension and trimming features to both beams.

        This method is automatically called when joint is created by the call to `Joint.create()`.

        """
        if self.features:
            self.beam_a.clear_features(self.features)
            self.beam_b.clear_features(self.features)
            self.features = []

        plane_a, plane_b = self.cutting_planes

        trim_a = BeamTrimmingFeature(plane_a)
        extension_a = BeamExtensionFeature(*self.beam_a.extension_to_plane(plane_a))
        self.beam_a.add_feature(extension_a)
        self.beam_a.add_feature(trim_a)

        trim_b = BeamTrimmingFeature(plane_b)
        extension_b = BeamExtensionFeature(*self.beam_b.extension_to_plane(plane_b))
        self.beam_b.add_feature(extension_b)
        self.beam_b.add_feature(trim_b)

        self.features.extend([trim_a, extension_a, trim_b, extension_b])

    def restore_beams_from_keys(self, assemly):
        """After de-serialization, resotres references to the main and cross beams saved in the assembly."""
        self.beam_a = assemly.find_by_key(self.beam_a_key)
        self.beam_b = assemly.find_by_key(self.beam_b_key)