from compas_timber.parts import BrepSubtraction
from compas.geometry import distance_point_point
from collections import OrderedDict
from compas_timber.fabrication import BTLx
from compas_timber.fabrication import BTLxDrilling

class MarkerFactory(object):
    """
    Factory class for creating Text engraving.
    """

    def __init__(self):
        pass

    @staticmethod
    def round_to_nearest(input, base):
        return int(base * round(input/base))

    @staticmethod
    def get_marker_positions(part, existing_intervals):
        """Finds the optimal parameter on the line for the text engraving process."""
        # print("intersections: for beam: {}", part.key)
        # for key, value in part.intersections.items():
        #     tag = key.split(".")[-1]
        #     print(tag, value)

        intersections = set(part.intersections)
        intersections.update({0, 1})  # Ensure 0 and 1 are included
        all_intersections = [position*part.beam.length for position in intersections]
        all_intersections.sort()
        interval_spacing = 20
        min_dist = 150
        intervals = OrderedDict()
        for i in range(len(all_intersections)-1):
            if all_intersections[i+1] - all_intersections[i] > min_dist*2:
                intervals[(all_intersections[i+1] + all_intersections[i])/2] = (all_intersections[i], all_intersections[i+1])
        if len(intervals.keys()) == 0:
            print("No suitable location found for marker placement on beam {}.".format(part.ID))


        if len(intervals) == 1:
            center, _range = intervals.items()[0]
            if _range[1] - _range[0] > min_dist*3:                                   #if space for 2 markers
                first_position = float(_range[0]) + min_dist
                last_position = float(_range[1]) - min_dist
                spacing = MarkerFactory.round_to_nearest(last_position - first_position, interval_spacing)
                last_position = first_position + spacing
                while last_position - first_position > min_dist:
                    if int(round(last_position - first_position)) not in existing_intervals:
                        return [first_position, last_position]
                    last_position -= interval_spacing
                return [center]
            else:
                return [center]


        if len(intervals) > 1:
                for first_range in intervals.values():                                                    #loop through all first positions
                    for last_range in intervals.values()[::-1]:
                        first_position = first_range[0] + min_dist                                     #loop through all last positions
                        last_position = last_range[1] - min_dist
                        spacing = MarkerFactory.round_to_nearest(last_position - first_position, interval_spacing)
                        last_position = first_position + spacing

                        if spacing not in existing_intervals:
                            return [first_position, last_position]

                        i = 0
                        do_first, do_last = True, True
                        while (do_first and do_last):
                            if last_position - first_position < min_dist:
                                break
                            if i%2 == 0 and do_first:
                                first_position += interval_spacing
                                if first_position + min_dist > first_range[1]:                          #while there is room to incement steps up or down
                                    do_first = False
                            elif do_last:
                                last_position -= interval_spacing
                                if last_position - min_dist < last_range[0]:                                    #while there is room to incement steps up or down
                                    do_last = False                                                                 #if not possible, stop trying bigger

                            if int(round(last_position - first_position)) not in existing_intervals:                                #check if the smaller spacing is already taken
                                return [first_position, last_position]
                            i += 1
                else:
                    return [intervals.keys()[0]]
        return None



    @staticmethod
    def drill_params(x_position, y_position, face_id = 1):
        """Returns the text engraving parameters for the BTLx part."""
        return {
            "ReferencePlaneID": str(face_id), #default face
            "StartX": x_position, #7=number of characters in the ID
            "StartY": y_position, #manually center it since text is not centered in easybeam
            "Angle": 0.0,
            "Inclination": 90.0, #default(bottom) in easybeam
            "DepthLimited": "yes", #default(left) in easybeam
            "Depth": 8.0,   #default(left) in easybeam
            "Diameter": 4.0,
        }




    @classmethod
    def apply_processings(cls, part, existing_intervals):
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



        if part.processings:
            ref_plane_id = part.processings[0].header_attributes.get("ReferencePlaneID", 1)
        else:
            ref_plane_id = "1"


        positions = MarkerFactory.get_marker_positions(part, existing_intervals)

        param_dicts = []
        if positions:
            offset = distance_point_point(part.beam.blank_frame.point, part.beam.frame.point)
            if len(positions) == 1:
                print("Single Marker on beam {}.".format(part.ID))
            for position in positions:
                position += offset
                param_dicts.append(MarkerFactory.drill_params(position - 105.0/2.0, 47, ref_plane_id))
                param_dicts.append(MarkerFactory.drill_params(position + 105.0/2.0, 47, ref_plane_id))

            for dict in param_dicts:
                part.processings.append(BTLxDrilling.create_process(dict, "Marker"))
            if len(positions) > 1:
                return int(round(abs(positions[0] - positions[1]))), positions[0]
            return None, positions[0]
        return None, None

BTLx.register_feature("MarkerFactory", MarkerFactory)

