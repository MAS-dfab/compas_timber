from compas_timber.connections import FrenchRidgeLapJoint
from compas_timber.fabrication import BTLx
from compas_timber.fabrication import BTLxFrenchRidgeLap


class FrenchRidgeFactory(object):
    """
    Factory class for creating French ridge joints.
    """

    def __init__(self):
        pass

    @classmethod
    def apply_processings(cls, joint, parts):
        """
        Apply processings to the joint and parts.

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

        main_part.processings.append(BTLxFrenchRidgeLap.create_process(joint.btlx_params_main, joint_name="FrenchRidgeLap"))
        cross_part.processings.append(BTLxFrenchRidgeLap.create_process(joint.btlx_params_cross, joint_name="FrenchRidgeLap"))


BTLx.register_joint(FrenchRidgeLapJoint, FrenchRidgeFactory)
