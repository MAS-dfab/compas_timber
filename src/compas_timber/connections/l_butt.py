from compas.geometry import Frame
from compas_timber.parts import CutFeature

from .joint import BeamJoinningError
from .joint import Joint
from .solver import JointTopology


class LButtJoint(Joint):
    """Represents an L-Butt type joint which joins two beam in their ends, trimming the main beam.

    This joint type is compatible with beams in L topology.

    Please use `LButtJoint.create()` to properly create an instance of this class and associate it with an assembly.

    Parameters
    ----------
    assembly : :class:`~compas_timber.assembly.TimberAssembly`
        The assembly associated with the beams to be joined.
    main_beam : :class:`~compas_timber.parts.Beam`
        The main beam to be joined.
    cross_beam : :class:`~compas_timber.parts.Beam`
        The cross beam to be joined.
    small_beam_butts : bool, default False
        If True, the beam with the smaller cross-section will be trimmed. Otherwise, the main beam will be trimmed.
    extend_cross : bool, default True
        If True, the cross beam will be extended to the opposite face of the main beam.

    Attributes
    ----------
    beams : list(:class:`~compas_timber.parts.Beam`)
        The beams joined by this joint.
    joint_type : str
        A string representation of this joint's type.

    """

    SUPPORTED_TOPOLOGY = JointTopology.TOPO_L

    def __init__(self, main_beam=None, cross_beam=None, small_beam_butts=False, extend_cross=True, **kwargs):
        super(LButtJoint, self).__init__(**kwargs)

        if small_beam_butts and main_beam and cross_beam:
            if main_beam.width * main_beam.height > cross_beam.width * cross_beam.height:
                main_beam, cross_beam = cross_beam, main_beam

        self.main_beam = main_beam
        self.cross_beam = cross_beam
        self.main_beam_key = main_beam.key if main_beam else None
        self.cross_beam_key = cross_beam.key if cross_beam else None
        self.extend_cross = extend_cross
        self.features = []

    @property
    def __data__(self):
        data_dict = {
            "main_beam_key": self.main_beam_key,
            "cross_beam_key": self.cross_beam_key,
            "extend_cross": self.extend_cross,
        }
        data_dict.update(super(LButtJoint, self).__data__)
        return data_dict

    @classmethod
    def __from_data__(cls, value):
        instance = cls(frame=Frame.__from_data__(value["frame"]), key=value["key"], gap=value["gap"])
        instance.main_beam_key = value["main_beam_key"]
        instance.cross_beam_key = value["cross_beam_key"]
        return instance

    @property
    def beams(self):
        return [self.main_beam, self.cross_beam]

    @property
    def joint_type(self):
        return "L-Butt"

    def get_main_cutting_plane(self):
        # TODO: rework this to look at all faces (including end faces) and return the index of the face with the smallest angle
        # TODO: check here if the found face is one of the end faces, if it is raise BeamJoiningError, we don't want to join in that situation
        assert self.main_beam and self.cross_beam

        face_angles = self.beam_side_incidence(self.main_beam, self.cross_beam, ignore_ends=False)
        face_index = min(face_angles, key=face_angles.get)  # type: ignore
        if face_index in [5, 6]:
            raise BeamJoinningError(beams=self.beams, joint=self, debug_info="Can't join to end faces")

        cfr = self.cross_beam.faces[face_index]
        cfr = Frame(cfr.point, cfr.xaxis, cfr.yaxis * -1.0)  # flip normal
        return cfr

    def get_cross_cutting_plane(self):
        assert self.main_beam and self.cross_beam

        face_angles = self.beam_side_incidence(self.cross_beam, self.main_beam)
        face_index = max(face_angles, key=face_angles.get)  # type: ignore
        cfr = self.main_beam.faces[face_index]
        return cfr

    def restore_beams_from_keys(self, assemly):
        """After de-serialization, resotres references to the main and cross beams saved in the assembly."""
        self.main_beam = assemly.find_by_key(self.main_beam_key)
        self.cross_beam = assemly.find_by_key(self.cross_beam_key)

    def add_features(self):
        """Adds the required extension and trimming features to both beams.

        This method is automatically called when joint is created by the call to `Joint.create()`.

        """
        assert self.main_beam and self.cross_beam  # should never happen

        if self.features:
            self.main_beam.remove_features(self.features)
        start_main, start_cross = None, None

        try:
            main_cutting_plane = self.get_main_cutting_plane()
            cross_cutting_plane = self.get_cross_cutting_plane()
            start_main, end_main = self.main_beam.extension_to_plane(main_cutting_plane)
            start_cross, end_cross = self.cross_beam.extension_to_plane(cross_cutting_plane)
        except AttributeError as ae:
            # I want here just the plane that caused the error
            geometries = [cross_cutting_plane] if start_main is not None else [main_cutting_plane]
            raise BeamJoinningError(
                beams=self.beams,
                joint=self,
                debug_info=str(ae),
                debug_geometries=geometries
            )
        except Exception as ex:
            raise BeamJoinningError(beams=self.beams, joint=self, debug_info=str(ex))

        extension_tolerance = 0.01  # TODO: this should be proportional to the unit used

        if self.extend_cross:
            self.cross_beam.add_blank_extension(
                start_cross + extension_tolerance, end_cross + extension_tolerance, self.key
            )
            f_cross = CutFeature(self.get_cross_cutting_plane())
            self.cross_beam.add_features(f_cross)
            self.features.append(f_cross)

        self.main_beam.add_blank_extension(start_main + extension_tolerance, end_main + extension_tolerance, self.key)

        f_main = CutFeature(main_cutting_plane)
        self.main_beam.add_features(f_main)
        self.features.append(f_main)

