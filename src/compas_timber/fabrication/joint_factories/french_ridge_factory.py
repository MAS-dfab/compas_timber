from compas_timber.connections import FrenchRidgeLapJoint
from compas_timber.fabrication import BTLx
from compas_timber.fabrication import BTLxFrenchRidgeLap
from compas_timber.fabrication.btlx_processes.btlx_drilling import BTLxDrilling

from compas.geometry import cross_vectors, dot_vectors


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

        top_key = joint.beams[0].key
        top_part = parts[str(top_key)]

        bottom_key = joint.beams[1].key
        bottom_part = parts[str(bottom_key)]

        # define a process for choosing top part
        top_vect = top_part.beam.centerline.direction
        compare_vect = cross_vectors(top_vect, [0, 0, 1])
        if dot_vectors(top_vect, compare_vect) == 0:
            top_part, bottom_part = bottom_part, top_part


        top_part.processings.append(BTLxFrenchRidgeLap.create_process(top_part, joint, True, joint.drill_diameter))
        bottom_part.processings.append(BTLxFrenchRidgeLap.create_process(bottom_part, joint, False, 0.0))


BTLx.register_joint(FrenchRidgeLapJoint, FrenchRidgeFactory)
