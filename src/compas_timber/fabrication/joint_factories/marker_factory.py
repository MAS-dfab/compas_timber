from compas_timber.parts import BrepSubtraction
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
        intersections = set(part.intersections)
        intersections.update({0, 1})  # Ensure 0 and 1 are included
        all_intersections = sorted([position*part.length for position in intersections])
        interval_spacing = 20
        min_length = 200
        intervals = OrderedDict()
        for i in range(len(all_intersections)-1):
            if all_intersections[i+1] - all_intersections[i] > min_length:
                intervals[(all_intersections[i+1] + all_intersections[i])/2] = all_intersections[i+1] - all_intersections[i]
        if len(intervals.keys()) == 0:
            raise Exception("No suitable intervals found for marker placement.")

        if len(intervals) == 1:
            if intervals.values()[0] > min_length*2:
                spacing = MarkerFactory.round_to_nearest(intervals.values()[0] - min_length*2, interval_spacing)
                first_position = float(intervals.keys()[0]) - (intervals.values()[0]/2) + (min_length)
                last_position = first_position + spacing
                if spacing not in existing_intervals:
                    return [first_position, last_position]
                while last_position > first_position + min_length:
                    last_position -= interval_spacing
                    if last_position - first_position not in existing_intervals:
                        return [first_position, last_position]
                return [part.length/2]
            elif intervals.values()[0] > min_length:
                return [part.length/2]


        if len(intervals) > 1:
            spacing = MarkerFactory.round_to_nearest(intervals.keys()[-1] - intervals.keys()[0], interval_spacing)
            print(part.key, intervals)
            if spacing not in existing_intervals:
                return [intervals.keys()[0], intervals.keys()[0] + spacing]
            else:
                found = False
                for i in range(len(intervals.keys())-1):                                                    #loop through all first positions
                    first_position = intervals.keys()[i]
                    for j in range(len(intervals.keys())-1, 0, -1):                                         #loop through all last positions
                        last_position = first_position + spacing
                        try_bigger = True
                        try_smaller = True
                        i = 0
                        while ((try_bigger or try_smaller) and i<2000):                                                  #while there is room to incement steps up or down
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
                            i+=1
                        if found:

                            return [first_position, last_position]

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
            if len(positions) == 1:
                print("Single Marker")
            for position in positions:
                param_dicts.append(MarkerFactory.drill_params(position - 105.0/2.0, 47, ref_plane_id))
                param_dicts.append(MarkerFactory.drill_params(position + 105.0/2.0, 47, ref_plane_id))

            for dict in param_dicts:
                part.processings.append(BTLxDrilling.create_process(dict, "Marker"))
            if len(positions) > 1:
                return abs(positions[0] - positions[1]), positions[0]
            return None, positions[0]
        return None, None

BTLx.register_feature("MarkerFactory", MarkerFactory)

