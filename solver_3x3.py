from color import Color
from cube import Cube
from face_id import FaceID
from location import Location
from move import Move
from solver import Solver


class Solver3x3(Solver):
    def __init__(self, cube_3x3: Cube):
        super().__init__(cube_3x3)
        if cube_3x3.size != 3:
            raise Exception(f"Given cube size is {cube_3x3.size} instead of 3.")

        self.faces_colors: dict[FaceID, Color] = dict()
        for face_id in FaceID:
            self.faces_colors[face_id] = self.cube.faces[face_id][1][1]

        self.color_faces: dict[Color: FaceID] = dict()
        for face_id in FaceID:
            self.color_faces[self.faces_colors[face_id]] = face_id

    def find_sticker_locations(self, colors: list[Color]) -> list[Location]:
        """
        Finds the locations of the sticker with the given colors.
        :param colors: List of colors of the sticker.
        :return: List of locations [face id, row, col] of the specified sticker. The i-th element of the returned value
        is the location of the i-th color in `colors`. If the sticker wasn't found, raises a `ValueError`.
        """
        colors_set = set(colors)

        for face_id in FaceID:
            face = self.cube.faces[face_id]

            for i in range(self.cube.size):
                for j in range(self.cube.size):
                    location = Location(face_id, i, j)
                    other_locations: list[Location] = (self.cube.get_other_sticker_locations(location))

                    found_colors: set[Color] = {self.cube.faces[loc.face_id][loc.row][loc.col]
                                                for loc in other_locations}
                    found_colors.add(face[i][j])  # add current color

                    if found_colors == colors_set:  # sticker found
                        locations = other_locations + [location]  # add current location

                        # sort by the order of colors in 'colors'
                        def sort_by(loc):
                            return colors.index(self.cube.faces[loc.face_id][loc.row][loc.col])

                        return sorted(locations, key=sort_by)

        raise ValueError("The specified sticker was not found.")

    def solve(self) -> bool:
        self.solve_cross()
        self.solve_u_color()
        self.solve_second_x_strip()

        can_solve_d_cross = self.solve_d_cross()
        if not can_solve_d_cross:
            return False
        can_solve_d_corner_positions = self.solve_d_corner_positions()
        if not can_solve_d_corner_positions:
            return False

        self.solve_d_corners()
        return True

    def solve_cross(self) -> list[Move]:
        place_white_center_moves = []

        white_center_location = self.find_sticker_locations([Color.Wh])[0]
        if white_center_location.face_id is FaceID.D:
            move = self.cube.get_needed_single_move(white_center_location, FaceID.F)
            self._add_and_apply(place_white_center_moves, move)
            self._add_and_apply(place_white_center_moves, move)

        elif white_center_location.face_id is not FaceID.U:
            move = self.cube.get_needed_single_move(white_center_location, FaceID.U)
            self._add_and_apply(place_white_center_moves, move)

        place_colored_centers_moves = []
        move = self.cube.get_needed_single_move(Location(FaceID.F, 1, 1), FaceID.R)  # middle sticker
        while self.cube.faces[FaceID.F][1][1] is not Color.Bl:  # middle sticker
            self._add_and_apply(place_colored_centers_moves, move)

        place_edges_moves = []
        ring_colors = [Color.Bl, Color.Or, Color.Gr, Color.Re]
        ring_colors_face_ids = [FaceID.F, FaceID.R, FaceID.B, FaceID.L]
        for i, ring_color in enumerate(ring_colors):
            place_ring_color_moves = []

            white_location, ring_color_location = self.find_sticker_locations([Color.Wh, ring_color])
            if white_location.face_id is FaceID.U and ring_color_location.face_id is ring_colors_face_ids[i]:
                continue

            if white_location.face_id is FaceID.U and ring_color_location.face_id is not ring_colors_face_ids[i]:
                move = self.cube.get_move_to_rotate_face(ring_color_location.face_id, True)

                white_location = self.cube.trace_a_moved_sticker(white_location, move)
                white_location = self.cube.trace_a_moved_sticker(white_location, move)
                ring_color_location = self.cube.get_other_sticker_locations(white_location)[0]

                self._add_and_apply(place_ring_color_moves, move)
                self._add_and_apply(place_ring_color_moves, move)

            elif white_location.face_id in ring_colors_face_ids:
                revered_move_1 = None
                if ring_color_location.face_id not in ring_colors_face_ids:
                    move = self.cube.get_move_to_rotate_face(white_location.face_id, True)
                    ring_color_location = self.cube.trace_a_moved_sticker(ring_color_location, move)
                    white_location = self.cube.get_other_sticker_locations(ring_color_location)[0]
                    self._add_and_apply(place_ring_color_moves, move)
                    revered_move_1 = move.reversed()

                move = self.cube.get_needed_single_move(white_location, FaceID.D)
                revered_move_2 = move.reversed()
                white_location = self.cube.trace_a_moved_sticker(white_location, move)
                ring_color_location = self.cube.get_other_sticker_locations(white_location)[0]
                self._add_and_apply(place_ring_color_moves, move)

                # move the white edge twice to ensure it won't be moved when applying the reversed moves
                move = self.cube.get_move_to_rotate_face(white_location.face_id, True)
                ring_color_location = self.cube.trace_a_moved_sticker(ring_color_location, move)
                ring_color_location = self.cube.trace_a_moved_sticker(ring_color_location, move)
                white_location = self.cube.get_other_sticker_locations(ring_color_location)[0]
                self._add_and_apply(place_ring_color_moves, move)
                self._add_and_apply(place_ring_color_moves, move)

                self._add_and_apply(place_ring_color_moves, revered_move_2)
                if revered_move_1 is not None:
                    self._add_and_apply(place_ring_color_moves, revered_move_1)

            # here both white location and ring color location are updated
            move = self.cube.get_move_to_rotate_face(white_location.face_id, True)
            while ring_color_location.face_id is not ring_colors_face_ids[i]:
                ring_color_location = self.cube.trace_a_moved_sticker(ring_color_location, move)
                self._add_and_apply(place_ring_color_moves, move)

            move = self.cube.get_move_to_rotate_face(ring_color_location.face_id, True)
            self._add_and_apply(place_ring_color_moves, move)
            self._add_and_apply(place_ring_color_moves, move)

            place_edges_moves.extend(place_ring_color_moves)

        return place_white_center_moves + place_colored_centers_moves + place_edges_moves

    def _add_and_apply(self, lst: list, move: Move):
        lst.append(move)
        self.cube.move(move)

    def solve_u_color(self):
        pass

    def solve_second_x_strip(self):
        pass

    def solve_d_cross(self) -> bool:
        return True

    def solve_d_corner_positions(self) -> bool:
        return True

    def solve_d_corners(self):
        pass
