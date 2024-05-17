from compas_timber.connections import LButtJoint
from compas_timber.fabrication import BTLx
from compas_timber.fabrication import BTLxJackCut
from compas_timber.fabrication import BTLxLap
from compas_timber.fabrication import BTLxDoubleCut


class LButtFactory(object):
    """
    Factory class for creating L-Butt joints.
    """

    def __init__(self):
        pass

    @classmethod
    def apply_processings(cls, joint, parts):
        """Apply processings to the joint and its associated parts.

        Parameters
        ----------
        joint : :class:`~compas_timber.connections.joint.Joint`
            The joint object.
        parts : dict
            A dictionary of the BTLxParts connected by this joint, with part keys as the dictionary keys.

        Returns
        -------
        None

        """

        main_part = parts[str(joint.main_beam.key)]
        cross_part = parts[str(joint.cross_beam.key)]
        main_cut_plane, ref_plane = joint.get_main_cutting_plane()
        cross_cut_plane = joint.get_cross_cutting_plane()
        cross_part.processings.append(BTLxJackCut.create_process(cross_part, cross_cut_plane, "L-Butt Joint{0}".format(joint.key)))

        if joint.mill_depth > 0:
            if joint.ends[str(cross_part.key)] == "start":
                joint.btlx_params_cross["machining_limits"] = {
                    "FaceLimitedStart": "no",
                    "FaceLimitedFront": "no",
                    "FaceLimitedBack": "no",
                }
            else:
                joint.btlx_params_cross["machining_limits"] = {
                    "FaceLimitedEnd": "no",
                    "FaceLimitedFront": "no",
                    "FaceLimitedBack": "no",
                }

            joint.btlx_params_cross["ReferencePlaneID"] = str(cross_part.reference_surface_from_beam_face(ref_plane))
            cross_part.processings.append(BTLxLap.create_process(joint.btlx_params_cross, "L-Butt Joint {0}".format(joint.key)))

        if joint.birdsmouth:
            ref_face = main_part.beam.faces[joint.main_face_index]
            joint.btlx_params_main["ReferencePlaneID"] = str(main_part.reference_surface_from_beam_face(ref_face))
            main_part.processings.append(BTLxDoubleCut.create_process(joint.btlx_params_main, "L-Butt Joint {0}".format(joint.key)))
        else:
            main_part.processings.append(BTLxJackCut.create_process(main_part, main_cut_plane, "L-Butt Joint {0}".format(joint.key)))


BTLx.register_joint(LButtJoint, LButtFactory)
