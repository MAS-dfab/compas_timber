import os
import uuid
import xml.dom.minidom as MD
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import date
from datetime import datetime

import compas
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Vector
from compas.geometry import angle_vectors
from compas.geometry import Transformation

class BTLx(object):
    """Class representing a BTLx object.

    BTLx is a format used for representing timber fabrication data.

    Parameters
    ----------
    assembly : :class:`~compas_timber.assembly.Assembly`
        The assembly object.

    Attributes
    ----------
    history : dict
        The history of the BTLx file.
    btlx_string : str
        A pretty XML string for visualization.
    parts : dict
        A dictionary of the BTLxParts in the assembly.
    joints : list
        A list of the joints in the assembly.

    """

    POINT_PRECISION = 3
    ANGLE_PRECISION = 3
    REGISTERED_JOINTS = {}
    REGISTERED_FEATURES = {}
    FILE_ATTRIBUTES = OrderedDict(
        [
            ("xmlns", "https://www.design2machine.com"),
            ("Version", "2.0.0"),
            ("Language", "en"),
            ("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance"),
            (
                "xsi:schemaLocation",
                "https://www.design2machine.com https://www.design2machine.com/btlx/btlx_2_0_0.xsd",
            ),
        ]
    )

    def __init__(self, assembly, do_marker_drilling = False):
        self.assembly = assembly
        self.parts = {}
        self._test = []
        self.joints = assembly.joints
        self.existing_intervals = []
        self.do_marker_drilling = do_marker_drilling
        self.mocap_dict = {}
        self.process_assembly()

    @property
    def history(self):
        """Returns the file history of the BTLx file."""
        return {
            "CompanyName": "Gramazio Kohler Research",
            "ProgramName": "COMPAS_Timber",
            "ProgramVersion": "Compas: {}".format(compas.__version__),
            "ComputerName": "{}".format(os.getenv("computername")),
            "UserName": "{}".format(os.getenv("USERNAME")),
            "FileName": "",
            "Date": "{}".format(date.today()),
            "Time": "{}".format(datetime.now().strftime("%H:%M:%S")),
            "Comment": "",
        }

    def btlx_string(self):
        """Returns a pretty XML string for visualization in GH, Terminal, etc."""
        self.ET_element = ET.Element("BTLx", BTLx.FILE_ATTRIBUTES)
        self.ET_element.append(self.file_history)
        self.project_element = ET.SubElement(self.ET_element, "Project", Name="testProject")
        self.parts_element = ET.SubElement(self.project_element, "Parts")
        for part in self.parts.values():
            self.parts_element.append(part.et_element)
        return MD.parseString(ET.tostring(self.ET_element)).toprettyxml(indent="   ")

    def process_assembly(self):
        """Processes the assembly and generates BTLx parts."""
        for beam in self.assembly.beams:
            self.parts[str(beam.key)] = BTLxPart(beam)
        for joint in self.joints:
            factory_type = self.REGISTERED_JOINTS.get(str(type(joint)))
            factory_type.apply_processings(joint, self.parts)
        for part in self.parts.values():
            id_face = '1'
            if part.ID:
                factory_type = self.REGISTERED_FEATURES.get("TextID")
                factory_type.apply_processings(part)
                id_face = part.processings[-1].header_attributes["ReferencePlaneID"]
                self.mocap_dict[part.ID] = {}
            # if part.do_marker:
            #     factory_type = self.REGISTERED_FEATURES.get("MarkerFactory")
            #     factory_type.apply_processings(part)
            if self.do_marker_drilling:
                factory_type = self.REGISTERED_FEATURES.get("MarkerFactory")
                interval, frame_x_pos = factory_type.apply_processings(part, self.existing_intervals)
                if interval == None and frame_x_pos == None:
                    self.mocap_dict[part.ID] = "no marker"
                if interval == None and frame_x_pos == None:
                    self.mocap_dict[part.ID] = "no marker"
                if interval:
                    self.mocap_dict[part.ID]["spacing"] = int(round(interval))
                    self.existing_intervals.append(int(interval))
                if frame_x_pos and id_face:
                    if not interval:
                        interval = 0
                        self.mocap_dict[part.ID]["single_marker"] = True
                    y_axis = -Vector.Yaxis()
                    if id_face == '2':
                        y_axis = -Vector.Zaxis()
                    elif id_face == '3':
                        y_axis = Vector.Yaxis()
                    elif id_face == '4':
                        y_axis = Vector.Zaxis()

                    part.processings[-1].header_attributes["ReferencePlaneID"] = id_face
                    beam_point = Point(-(frame_x_pos + (interval/2.0)),0,0)
                    beam_frame = Frame(beam_point, Vector.Xaxis(), y_axis)

                    self.mocap_dict[part.ID]["beam_frame_relative_to_MoCap_Frame"] = beam_frame

        print(self.existing_intervals)






    @classmethod
    def register_joint(cls, joint_type, joint_factory):
        """Registers a joint type and its corresponding factory.

        Parameters
        ----------
        joint_type : type
            The type of the joint.
        joint_factory : : class:`~compas_timber.fabrication.joint_factories.joint_factory.JointFactory`
            The factory for creating the joint.

        Returns
        -------
        None

        """
        cls.REGISTERED_JOINTS[str(joint_type)] = joint_factory

    @classmethod
    def register_feature(cls, feature_type, feature_factory):
        """Registers a feature type and its corresponding factory.

        Parameters
        ----------
        feature_type : type
            The type of the feature.
        feature_factory : : class:`~compas_timber.fabrication.feature_factories.feature_factory.FeatureFactory`
            The factory for creating the feature.

        Returns
        -------
        None

        """
        cls.REGISTERED_FEATURES[str(feature_type)] = feature_factory

    @property
    def file_history(self):
        """Returns the file history element."""
        file_history = ET.Element("FileHistory")
        file_history.append(ET.Element("InitialExportProgram", self.history))
        return file_history

class BTLxPart(object):
    """Class representing a BTLx part. This acts as a wrapper for a Beam object.

    Parameters
    ----------
    beam : :class:`~compas_timber.assembly.Beam`
        The beam object.

    Attributes
    ----------
    attr : dict
        The attributes of the BTLx part.
    beam : :class:`~compas_timber.assembly.Beam`
        The beam object.
    key : str
        The key of the beam object.
    length : float
        The length of the beam.
    width : float
        The width of the beam.
    height : float
        The height of the beam.
    frame : :class:`~compas.geometry.Frame`
        The frame of the BTLxPart at the corner of the blank box that puts the blank geometry in positive coordinates.
    blank : :class:`~compas.geometry.Box`
        The blank of the beam.
    blank_frame : :class:`~compas.geometry.Frame`
        The frame of the blank.
    blank_length : float
        The blank length of the beam.
    intersections : dict
        A list of the intersection parameters on the beam
    processings : list
        A list of the processings applied to the beam.
    et_element : :class:`~xml.etree.ElementTree.Element`
        The ET element of the BTLx part.

    """

    def __init__(self, beam):
        self.beam = beam
        self.key = beam.key
        self.length = beam.blank_length
        self.width = beam.width
        self.height = beam.height
        self.frame = Frame(
            self.beam.long_edges[2].closest_point(self.beam.blank_frame.point),
            beam.frame.xaxis,
            beam.frame.yaxis,
        )  # I used long_edge[2] because it is in Y and Z negative. Using that as reference puts the beam entirely in positive coordinates.
        self.blank_length = beam.blank_length
        self.ID = (str(beam.attributes["ID"])+str(beam.key)) if beam.attributes["ID"] else str(beam.key)
        self.intersections = beam.attributes["intersections"]
        self._reference_surfaces = []
        self.processings = []
        self._et_element = None

    def reference_surface_from_beam_face(self, beam_face):
        """Finds the reference surface with normal that matches the normal of the beam face argument

        Parameters
        -----------
        beam_face : :class:`~compas.geometry.Frame`
            The frame of a beam face from beam.faces.

        Returns
        --------
        key : str
            The key(index 1-6) of the reference surface.

        """
        for i in range(1, 7):
            if angle_vectors(self.reference_surface_planes(i).normal, beam_face.normal, deg=True) < 1e-3:
                return i

    def reference_surface_planes(self, index):
        """Returns the reference surface planes for a given index per BTLx docs.

        Parameters
        ----------
        index : int
            The index of the reference surface.

        Returns
        -------
        dict
            The BTLx reference surface frame.

        """
        if len(self._reference_surfaces) != 6:
            self._reference_surfaces = {
                "1": Frame(self.frame.point, self.frame.xaxis, self.frame.zaxis),
                "2": Frame(
                    self.frame.point + self.frame.yaxis * self.width,
                    self.frame.xaxis,
                    -self.frame.yaxis,
                ),
                "3": Frame(
                    self.frame.point + self.frame.yaxis * self.width + self.frame.zaxis * self.height,
                    self.frame.xaxis,
                    -self.frame.zaxis,
                ),
                "4": Frame(
                    self.frame.point + self.frame.zaxis * self.height,
                    self.frame.xaxis,
                    self.frame.yaxis,
                ),
                "5": Frame(self.frame.point, self.frame.zaxis, self.frame.yaxis),
                "6": Frame(
                    self.frame.point + self.frame.xaxis * self.blank_length + self.frame.yaxis * self.width,
                    self.frame.zaxis,
                    -self.frame.yaxis,
                ),
            }
        return self._reference_surfaces[str(index)]

    @property
    def attr(self):
        return {
            "SingleMemberNumber": str(self.key),
            "AssemblyNumber": "",
            "OrderNumber": str(self.key),
            "Designation": "",
            "Annotation": "",
            "Storey": "",
            "Group": "",
            "Package": "",
            "Material": "",
            "TimberGrade": "",
            "QualityGrade": "",
            "Count": "1",
            "Length": "{:.{prec}f}".format(self.blank_length, prec=BTLx.POINT_PRECISION),
            "Height": "{:.{prec}f}".format(self.height, prec=BTLx.POINT_PRECISION),
            "Width": "{:.{prec}f}".format(self.width, prec=BTLx.POINT_PRECISION),
            "Weight": "0",
            "ProcessingQuality": "automatic",
            "StoreyType": "",
            "ElementNumber": "00",
            "Layer": "0",
            "ModuleNumber": "",
        }

    @property
    def test(self):
        items = []
        for item in self._test:
            items.append(item)
        for process in self.processings:
            for item in process.test:
                items.append(item)
        return items

    def et_point_vals(self, point):
        """Returns the ET point values for a given point.

        Parameters
        ----------
        point : :class:`~compas.geometry.Point`
            The point to be converted.

        Returns
        -------
        dict
            The ET point values formatted for the ET element.

        """
        return {
            "X": "{:.{prec}f}".format(point.x, prec=BTLx.POINT_PRECISION),
            "Y": "{:.{prec}f}".format(point.y, prec=BTLx.POINT_PRECISION),
            "Z": "{:.{prec}f}".format(point.z, prec=BTLx.POINT_PRECISION),
        }

    @property
    def et_element(self):
        if not self._et_element:
            self._et_element = ET.Element("Part", self.attr)
            self._shape_strings = None
            self._et_element.append(self.et_transformations)
            self._et_element.append(ET.Element("GrainDirection", X="1", Y="0", Z="0", Align="no"))
            self._et_element.append(ET.Element("ReferenceSide", Side="1", Align="no"))
            processings_et = ET.Element("Processings")
            for process in self.processings:
                processings_et.append(process.et_element)
            self._et_element.append(processings_et)
            self._et_element.append(self.et_shape)
        return self._et_element

    @property
    def et_transformations(self):
        transformations = ET.Element("Transformations")
        guid = "{" + str(uuid.uuid4()) + "}"
        transformation = ET.SubElement(transformations, "Transformation", GUID=guid)
        position = ET.SubElement(transformation, "Position")
        position.append(ET.Element("ReferencePoint", self.et_point_vals(self.frame.point)))
        position.append(ET.Element("XVector", self.et_point_vals(self.frame.xaxis)))
        position.append(ET.Element("YVector", self.et_point_vals(self.frame.yaxis)))
        return transformations

    @property
    def et_shape(self):
        shape = ET.Element("Shape")
        indexed_face_set = ET.SubElement(shape, "IndexedFaceSet", convex="true", coordIndex="")
        indexed_face_set.set("coordIndex", " ")
        indexed_face_set.append(ET.Element("Coordinate"))
        # indexed_face_set.set("coordIndex", self.shape_strings[0])
        # indexed_face_set.append(ET.Element("Coordinate", point=self.shape_strings[1]))
        return shape

    @property
    def shape_strings(self):
        if not self._shape_strings:
            brep_vertex_points = []
            brep_indices = []
            try:
                for face in self.beam.geometry.faces:
                    for loop in face.loops:
                        for vertex in loop.vertices:
                            if brep_vertex_points.contains(vertex.point):
                                brep_indices.append(brep_vertex_points.index(vertex.point))
                            else:
                                brep_vertex_points.append(vertex.point)
                                brep_indices.append(len(brep_vertex_points))

                brep_indices.append(-1)
                brep_indices.pop(-1)
            except NotImplementedError:
                print("brep.face.loop.vertices not implemented")
            brep_indices_string = " "
            for index in brep_indices:
                brep_indices_string += str(index) + " "

            brep_vertices_string = " "
            for point in brep_vertex_points:
                xform = Transformation.from_frame_to_frame(self.frame, Frame((0, 0, 0), (1, 0, 0), (0, 1, 0)))
                point.transform(xform)
                brep_vertices_string += "{:.{prec}f} {:.{prec}f} {:.{prec}f} ".format(
                    point.x, point.y, point.z, prec=BTLx.POINT_PRECISION
                )
            self._shape_strings = [brep_indices_string, brep_vertices_string]
        return self._shape_strings


class BTLxProcess(object):
    """Generic class for BTLx processings.

    This should be instantiated and appended to BTLxPart.processings in a specific btlx_process class (eg BTLxJackCut)

    each specific btlx process class should have:
    PROCESS_TYPE a class attribute which matches the btlx process name
    self.header_attributes which matches as a dict,
    self.process_parameters which describe the geometric parameters of the process

    the joint factory calls instantiates a process or processes and appends it or them to the BTLxPart.processes list

    each process will have specific inputs which are derived from the Joint instance and related BTLxParts

    some joints will require combinations of multiple BTLx processes, and some processes will cover multiple joint types.

    the factory module should call the BTLx.register_joint(joint type, joint factory) function so that the BTLx class can call specific factory types.

    The factory will typically derive the needed parameters from the Joint instance and the joint_factory will apply them to the individual BTLxParts.


    Parameters
    ----------
    name : str
        The name of the processing.
    attr : dict
        The attributes of the processing.
    params : dict
        The parameters of the processing.


    Attributes
    ----------
    et_element : :class:`~xml.etree.ElementTree.Element`
        The ET element of the BTLx processing.

    """

    def __init__(self, process_type, header_attributes, process_parameters):
        self.process_type = process_type
        self.header_attributes = header_attributes
        self.process_parameters = process_parameters

    @property
    def et_element(self):
        element = ET.Element(self.process_type, self.header_attributes)
        for key, value in self.process_parameters.items():
            if isinstance(value, dict):
                child = ET.Element(key, value)
            else:
                child = ET.Element(key)
                child.text = value
            element.append(child)
        return element
