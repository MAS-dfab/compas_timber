import Rhino
from ghpythonlib.componentbase import executingcomponent as component
from Grasshopper.Kernel.GH_RuntimeMessageLevel import Warning

from compas_timber.fabrication import BTLx
from compas import json_dump


class WriteBTLx(component):
    def RunScript(self, assembly, do_marker_drilling, path, write):
        if not assembly:
            self.AddRuntimeMessage(Warning, "Input parameter Assembly failed to collect data")
            return
        if not do_marker_drilling:
            do_marker_drilling = False

        btlx = BTLx(assembly, do_marker_drilling)
        btlx.history["FileName"] = Rhino.RhinoDoc.ActiveDoc.Name

        if write:
            if not path:
                self.AddRuntimeMessage(Warning, "Input parameter Path failed to collect data")
                return
            if path[-5:] != ".btlx":
                path += ".btlx"
            with open(path, "w") as f:
                f.write(btlx.btlx_string())
            if do_marker_drilling:
                path = path[0:-5] + "_MoCap.json"
                json_dump(btlx.mocap_dict, path, pretty = True)
        return btlx.btlx_string()
