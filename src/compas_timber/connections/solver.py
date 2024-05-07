import itertools
import math

from compas.geometry import Point
from compas.geometry import add_vectors
from compas.geometry import angle_vectors
from compas.geometry import closest_point_on_line
from compas.geometry import cross_vectors
from compas.geometry import distance_point_point
from compas.geometry import dot_vectors
from compas.geometry import scale_vector
from compas.geometry import subtract_vectors
from compas.geometry import intersection_line_line
from compas.plugins import pluggable


@pluggable(category="solvers")
def find_neighboring_beams(beams, inflate_by=None):
    """Finds neighboring pairs of beams in the given list of beams, using R-tree search.

    The inputs to the R-tree algorithm are the axis-aligned bounding boxes of the beams (beam.aabb), enlarged by the `inflate_by` amount.
    The returned elements are sets containing pairs of Beam objects.

    Parameters
    ----------
    beams : list(:class:`~compas_timer.part.Beam`)
        The list of beams in which neighboring beams should be identified.
    inflate_by : optional, float
        A value in design units by which the regarded bounding boxes should be inflated.

    Returns
    -------
    list(set(:class:`~compas_timber.part.Beam`, :class:`~compas_timber.part.Beam`))

    Notes
    -----
    This is a `pluggable`. In order to use this function, a compatible `plugin` has to be available.
    For example, in Rhino, the function :func:`~compas_timber.rhino.find_neighboring_beams` will be used.

    """
    raise NotImplementedError


class JointTopology(object):
    """Enumeration of the possible joint topologies.

    Attributes
    ----------
    TOPO_UNKNOWN
    TOPO_I
    TOPO_L
    TOPO_T
    TOPO_X

    """

    TOPO_UNKNOWN = 0
    TOPO_I = 1
    TOPO_L = 2
    TOPO_T = 3
    TOPO_X = 4

    @classmethod
    def get_name(cls, value):
        """Returns the string representation of given topology value.

        For use in logging.

        Parameters
        ----------
        value : int
            One of [JointTopology.TOPO_L, JointTopology.TOPO_T, JointTopology.TOPO_X, JointTopology.TOPO_UNKNOWN]

        Returns
        -------
        str
            One of ["TOPO_L", "TOPO_T", "TOPO_X", "TOPO_UNKNOWN"]

        """
        try:
            return {v: k for k, v in JointTopology.__dict__.items() if k.startswith("TOPO_")}[value]
        except KeyError:
            return "TOPO_UNKNOWN"


class ConnectionSolver(object):
    """Provides tools for detecting beam intersections and joint topologies."""

    TOLERANCE = 1e-6

    @classmethod
    def find_intersecting_pairs(cls, beams, rtree=False, max_distance=None):
        """Finds pairs of intersecting beams in the given list of beams and stores the intersection parameters for each specific beam.

        Parameters
        ----------
        beams : list(:class:`~compas_timber.parts.Beam`)
            A list of beam objects.
        rtree : bool
            When set to True R-tree will be used to search for neighboring beams.
        max_distance : float, optional
            When `rtree` is True, an additional distance apart with which
            non-touching beams are still considered intersecting.

        Returns
        -------
        list(set(:class:`~compas_timber.parts.Beam`, :class:`~compas_timber.parts.Beam`))
            List containing sets or neightboring pairs beams.

        """

        neighboring_pairs = find_neighboring_beams(beams, inflate_by=max_distance) if rtree else itertools.combinations(beams, 2)
        return neighboring_pairs

    @classmethod
    def find_intersection_parameters(cls, beams, tol=None):
        generic_pair_indeces = itertools.combinations(range(len(beams)), 2)
        for pair in generic_pair_indeces:
            pair_centerlines = [beams[p].centerline for p in pair]
            intersection_points = intersection_line_line(*pair_centerlines, tol=10.0)
            if None in intersection_points:
                continue
            if all(abs(p1 - p2) < cls.TOLERANCE for p1, p2 in zip(intersection_points[0], intersection_points[1])):
                intersection_point = Point(*intersection_points[0])
                intersection_params = [cls._parameter_on_line(intersection_point, beams[p].centerline) for p in pair]
                for i, p in enumerate(pair):
                    # Check if the parameter is within [0, 1], if not, adjust it
                    intersection_params[i]= max(0, min(1,(intersection_params[i]))) #//TODO: this is just a temporal solution
                    beams[p].intersections.append(intersection_params[i])

    def find_topology(self, beam_a, beam_b, tol=TOLERANCE, max_distance=None):
        """If `beam_a` and `beam_b` intersect within the given `max_distance`, return the topology type of the intersection.

        If the topology is role-sensitive, the method outputs the beams in a consistent specific order
        (e.g. main beam first, cross beam second), otherwise, the beams are outputted in the same
        order as they were inputted.

        Parameters
        ----------
        beam_a : :class:`~compas_timber.parts.Beam`
            First beam from intersecting pair.
        beam_b : :class:`~compas_timber.parts.Beam`
            Second beam from intersecting pair.
        tol : float
            General tolerance to use for mathematical computations.
        max_distance : float, optional
            Maximum distance, in desigen units, at which two beams are considered intersecting.

        Returns
        -------
        tuple(:class:`~compas_timber.connections.JointTopology`, :class:`~compas_timber.parts.Beam`, :class:`~compas_timber.parts.Beam`)

        """

        tol = self.TOLERANCE  # TODO: change to a unit-sensitive value
        angtol = 1e-3

        a1, a2 = beam_a.centerline
        b1, b2 = beam_b.centerline
        va = subtract_vectors(a2, a1)
        vb = subtract_vectors(b2, b1)

        # check if centerlines parallel
        ang = angle_vectors(va, vb)
        if ang < angtol or ang > math.pi - angtol:
            parallel = True
        else:
            parallel = False

        if parallel:
            pa = a1
            pb = closest_point_on_line(a1, [b1, b2])
            if self._exceed_max_distance(pa, pb, max_distance, tol):
                return JointTopology.TOPO_UNKNOWN, None, None

            # check if any ends meet
            comb = [[0, 0], [0, 1], [1, 0], [1, 1]]
            meet = [not self._exceed_max_distance([a1, a2][ia], [b1, b2][ib], max_distance, tol) for ia, ib in comb]
            if sum(meet) != 1:
                return JointTopology.TOPO_UNKNOWN, None, None

            # check if overlap: find meeting ends -> compare vectors outgoing from these points
            meeting_ends_idx = [c for c, m in zip(comb, meet) if m is True][0]
            ia, ib = meeting_ends_idx
            pa1 = [a1, a2][ia]
            pa2 = [a1, a2][not ia]
            pb1 = [b1, b2][ib]
            pb2 = [b1, b2][not ib]
            vA = subtract_vectors(pa2, pa1)
            vB = subtract_vectors(pb2, pb1)
            ang = angle_vectors(vA, vB)
            if ang < tol:
                # vectors pointing in the same direction -> beams are overlapping
                return JointTopology.TOPO_UNKNOWN, None, None
            else:
                return JointTopology.TOPO_I, beam_a, beam_b

        # if not parallel:
        vn = cross_vectors(va, vb)
        vna = cross_vectors(va, vn)
        vnb = cross_vectors(vb, vn)

        ta = self._calc_t([a1, a2], [b1, vnb])
        pa = Point(*add_vectors(a1, scale_vector(va, ta)))
        tb = self._calc_t([b1, b2], [a1, vna])
        pb = Point(*add_vectors(b1, scale_vector(vb, tb)))

        # for max_distance calculations, limit intersection point to line segment
        if ta < 0:
            pa = a1
        if ta > 1:
            pa = a2
        if tb < 0:
            pb = b1
        if tb > 1:
            pb = b2

        if self._exceed_max_distance(pa, pb, max_distance, tol):
            return JointTopology.TOPO_UNKNOWN, None, None

        # topologies:
        xa = self._is_near_end(ta, beam_a.centerline.length, max_distance or 0, tol)
        xb = self._is_near_end(tb, beam_b.centerline.length, max_distance or 0, tol)

        # L-joint (both meeting at ends)
        if xa and xb:
            return JointTopology.TOPO_L, beam_a, beam_b

        # T-joint (one meeting with the end along the other)
        if xa:
            # A:main, B:cross
            return JointTopology.TOPO_T, beam_a, beam_b
        if xb:
            # B:main, A:cross
            return JointTopology.TOPO_T, beam_b, beam_a

        # X-joint (both meeting somewhere along the line)
        return JointTopology.TOPO_X, beam_a, beam_b

    @staticmethod
    def _parameter_on_line(point, line):
        # Vector from the start of the line segment to the given point
        point_vector = [(point.x - line.start.x), (point.y - line.start.y), (point.z - line.start.z)]
        # Calculate the parameter (t) using dot product
        t = dot_vectors(point_vector, line.vector) / dot_vectors(line.vector, line.vector)
        return t

    @staticmethod
    def _calc_t(line, plane):
        a, b = line
        o, n = plane
        ab = subtract_vectors(b, a)
        dotv = dot_vectors(n, ab)  # lines parallel to plane (dotv=0) filtered out already
        oa = subtract_vectors(a, o)
        t = -dot_vectors(n, oa) / dotv
        return t

    @staticmethod
    def _exceed_max_distance(pa, pb, max_distance, tol):
        d = distance_point_point(pa, pb)
        if max_distance is not None and d > max_distance:
            return True
        if max_distance is None and d > tol:
            return True
        return False

    @staticmethod
    def _is_near_end(t, length, max_distance, tol):
        return abs(t) * length < max_distance + tol or abs(1.0 - t) * length < max_distance + tol
