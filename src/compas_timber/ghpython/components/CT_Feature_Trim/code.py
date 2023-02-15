from compas_rhino.conversions import plane_to_compas_frame
from ghpythonlib.componentbase import executingcomponent as component
from Grasshopper.Kernel.GH_RuntimeMessageLevel import Warning

from compas_timber.ghpython import FeatureDefinition
from compas_timber.parts import BeamTrimmingFeature


class TrimmingFeature(component):
    def RunScript(self, Beam, Planes):
        if not Beam:
            self.AddRuntimeMessage(Warning, "Input parameter Beam failed to collect data")
        if not Planes:
            self.AddRuntimeMessage(Warning, "Input parameter Pln failed to collect data")
        if not (Beam and Planes):
            return

        if not isinstance(Beam, list):
            Beam = [Beam]
        if not isinstance(Planes, list):
            Planes = [Planes]

        FeatureDefs = []
        for plane in Planes:
            feature = BeamTrimmingFeature(plane_to_compas_frame(plane))
            FeatureDefs.append(FeatureDefinition(feature, Beam))

        return FeatureDefs
