from compas_timber.parts import BrepSubtraction
from collections import OrderedDict
from compas_timber.fabrication import BTLx
from compas_timber.fabrication import BTLxText
from datatable import first, last

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
        intersections = set(part.intersections)
        intersections.update({0, 1})  # Ensure 0 and 1 are included
        all_intersections = sorted(intersections)
        interval_spacing = 20
        min_length = 200
        intervals = OrderedDict()
        for i in range(len(all_intersections)-1):
            if all_intersections[i+1] - all_intersections[i] > min_length:
                intervals[int(round((all_intersections[i+1] - all_intersections[i])/2))] = all_intersections[i+1] - all_intersections[i]

        if len(intervals) == 0:
            raise Exception("No suitable intervals found for marker placement.")

        if len(intervals) == 1:
            if intervals.values()[0] > min_length*2:
                spacing = MarkerFactory.round_to_nearest(part.length - min_length*2, interval_spacing)
                return min_length, spacing + min_length
            else:
                return part.length/2


        if len(intervals) > 1:
            spacing = MarkerFactory.round_to_nearest(intervals.keys()[-1] - intervals.keys()[0], interval_spacing)

            if spacing in existing_intervals:
                found = False
                for i in range(len(intervals.keys())-1):                                                    #loop through all first positions
                    first_position = intervals.keys()[i]
                    for j in range(len(intervals.keys())-1, 1, -1):                                         #loop through all last positions
                        last_position = intervals.keys()[j]
                        try_bigger = True
                        try_smaller = True
                        while try_bigger or try_smaller:                                                    #while there is room to incement steps up or down
                            step = interval_spacing
                            if try_bigger:
                                if spacing + step not in existing_intervals:                                #check if the bigger spacing is already taken
                                    if first_position -  step > all_intersections[i] + min_length:          #check if moving the first position down is possible
                                        first_position -=  step
                                        found = True
                                        break
                                    elif last_position +  step < all_intersections[j+1] - min_length:       #check if moving the last position up is possible
                                        last_position +=  step
                                        found = True
                                        break
                                    else:
                                        try_bigger = False                                                  #if not possible, stop trying bigger
                            if try_smaller:
                                if spacing - step not in existing_intervals:                                #check if the smaller spacing is already taken
                                    if first_position +  step < all_intersections[i+1] - min_length:        #check if moving the first position up is possible
                                        first_position +=  step
                                        found = True
                                        break
                                    elif last_position -  step  > all_intersections[j] + min_length:        #check if moving the last position down is possible
                                        last_position -=  step
                                        found = True
                                        break
                                    else:                                                                   #if not possible, stop trying smaller
                                        try_smaller = False
                            step += interval_spacing
                        if found:
                            return first_position, last_position



    @staticmethod
    def drill_params(x_position, y_position, face_id = 1):
        """Returns the text engraving parameters for the BTLx part."""
        return {
            "ReferencePlaneID": face_id, #default face
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
        for position in positions:
            param_dicts.append(MarkerFactory.drill_params(position - 105.0/2.0, 50, ref_plane_id))
            param_dicts.append(MarkerFactory.drill_params(position + 105.0/2.0, 50, ref_plane_id))
            param_dicts.append(MarkerFactory.drill_params(position + 105.0/2.0, 50, ref_plane_id+1 if ref_plane_id <4 else 1))


        for dict in param_dicts:
            part.processings.append(BTLxText.create_process(dict, "Marker"))
        return abs(positions[0] - positions[1])

BTLx.register_feature("MarkerFactory", MarkerFactory)

