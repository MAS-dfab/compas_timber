from compas_timber.connections import LHalfLapJoint
from compas_timber.fabrication import BTLx
from compas_timber.fabrication import BTLxLap
from compas_timber.fabrication import BTLxDrilling


class LHalfLapFactory(object):
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

        # for processing_main, processing_cross in zip(main_part.processings, cross_part.processings):
        #     if processing_main.header_attributes["Name"] == "L-HalfLap Joint_Cross" or processing_cross.header_attributes["Name"] == "L-HalfLap Joint_Main":
        #         main_part_copy = main_part
        #         cross_part_copy = cross_part

        #         main_part, cross_part = cross_part_copy, main_part_copy

        params_dict_main = joint.btlx_params_main
        params_dict_cross = joint.btlx_params_cross

        # for processing in cross_part.processings:
        #     if processing.header_attributes["Name"] == "L-HalfLap Joint":
        #         params_dict_cross["ReferencePlaneID"] = int(processing.header_attributes["ReferencePlaneID"])
        #         if int(processing.header_attributes["ReferencePlaneID"]) > 2:
        #             params_dict_main["ReferencePlaneID"] = int(processing.header_attributes["ReferencePlaneID"])-2
        #         else:
        #             params_dict_main["ReferencePlaneID"] = int(processing.header_attributes["ReferencePlaneID"])+2

        cross_part.processings.append(BTLxLap.create_process(params_dict_cross, joint_name="L-HalfLap Joint_Cross"))
        main_part.processings.append(BTLxLap.create_process(params_dict_main, joint_name="L-HalfLap Joint_Main"))

        if joint.drill_diameter > 0:
            main_part.processings.append(BTLxDrilling.create_process(joint.btlx_drilling_params_main, "L-HalfLap Drilling"))


BTLx.register_joint(LHalfLapJoint, LHalfLapFactory)
