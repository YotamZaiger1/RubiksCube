from color import Color
from cube import Cube
from face_id import FaceID, RING_FACE_IDS
from location import Location
from move import Move
from solver import Solver


class Solver3x3(Solver):
    def __init__(self, cube_3x3: Cube):
        super().__init__(cube_3x3)
        if cube_3x3.size != 3:
            raise Exception(f"Given cube size is {cube_3x3.size} instead of 3.")

        self.faces_colors: dict[FaceID: Color] = dict()
        for face_id in FaceID:
            self.faces_colors[face_id] = self.cube.faces[face_id][1][1]

        self.color_faces: dict[Color: FaceID] = dict()
        for face_id in FaceID:
            self.color_faces[self.faces_colors[face_id]] = face_id

        self.ring_corner_colors = []
        for i in range(len(RING_FACE_IDS)):
            color_a = self.faces_colors[RING_FACE_IDS[i]]
            color_b = self.faces_colors[RING_FACE_IDS[(i + 1) % len(RING_FACE_IDS)]]
            self.ring_corner_colors.append([color_a, color_b])

    @staticmethod
    def get_up_corner_location(id_1: FaceID, id_2: FaceID) -> Location:
        """
        Returns the corner location in the U face which has parts in `id_1` and in `id_2` faces.
        The order between `id_1` and `id_2` does not matter.
        :param id_1: A ring face id.
        :param id_2: A ring face id.
        :return: The corner location in the U face which has parts in `id_1` and in `id_2` faces.
        """
        ids = [id_1, id_2]
        if FaceID.F in ids and FaceID.R in ids:
            return Location(FaceID.U, 2, 2)
        if FaceID.R in ids and FaceID.B in ids:
            return Location(FaceID.U, 0, 2)
        if FaceID.B in ids and FaceID.L in ids:
            return Location(FaceID.U, 0, 0)
        if FaceID.L in ids and FaceID.F in ids:
            return Location(FaceID.U, 2, 0)
        raise ValueError("The given face ids does not fit any corner.")

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

    def _add_and_apply(self, lst: list, move: Move):
        lst.append(move)
        self.cube.move(move)

    def solve(self) -> tuple[bool, list[Move]]:
        cross_moves = self.solve_cross()
        u_color_moves = self.solve_u_color()
        second_strip_moves = self.solve_second_x_strip()

        can_solve_d_cross, d_cross_moves = self.solve_d_cross()
        moves = cross_moves + u_color_moves + second_strip_moves + d_cross_moves

        if not can_solve_d_cross:
            return False, moves

        can_solve_d_corner_positions, d_corner_position_moves = self.solve_d_corner_positions()
        moves += d_corner_position_moves
        if not can_solve_d_corner_positions:
            return False, moves

        d_corners_moves = self.solve_d_corners()
        moves += d_corners_moves
        return True, moves

    def solve_cross(self) -> list[Move]:
        up_color: Color = self.faces_colors[FaceID.U]

        place_edges_moves = []

        for ring_face_id in RING_FACE_IDS:
            ring_color = self.faces_colors[ring_face_id]
            place_ring_color_moves = []

            up_color_location, ring_color_location = self.find_sticker_locations([up_color, ring_color])
            if up_color_location.face_id is FaceID.U and ring_color_location.face_id is ring_face_id:
                continue

            if up_color_location.face_id is FaceID.U and ring_color_location.face_id is not ring_face_id:
                move = self.cube.get_move_to_rotate_face(ring_color_location.face_id, True)

                up_color_location = self.cube.trace_a_moved_sticker(up_color_location, move)
                up_color_location = self.cube.trace_a_moved_sticker(up_color_location, move)
                ring_color_location = self.cube.get_other_sticker_locations(up_color_location)[0]

                self._add_and_apply(place_ring_color_moves, move)
                self._add_and_apply(place_ring_color_moves, move)

            elif up_color_location.face_id in RING_FACE_IDS:
                revered_move_1 = None
                if ring_color_location.face_id not in RING_FACE_IDS:
                    move = self.cube.get_move_to_rotate_face(up_color_location.face_id, True)
                    ring_color_location = self.cube.trace_a_moved_sticker(ring_color_location, move)
                    up_color_location = self.cube.get_other_sticker_locations(ring_color_location)[0]
                    self._add_and_apply(place_ring_color_moves, move)
                    revered_move_1 = move.reversed()

                move = self.cube.get_needed_single_move(up_color_location, FaceID.D)
                revered_move_2 = move.reversed()
                up_color_location = self.cube.trace_a_moved_sticker(up_color_location, move)
                ring_color_location = self.cube.get_other_sticker_locations(up_color_location)[0]
                self._add_and_apply(place_ring_color_moves, move)

                # move the white edge twice to ensure it won't be moved when applying the reversed moves
                move = self.cube.get_move_to_rotate_face(up_color_location.face_id, True)
                ring_color_location = self.cube.trace_a_moved_sticker(ring_color_location, move)
                ring_color_location = self.cube.trace_a_moved_sticker(ring_color_location, move)
                up_color_location = self.cube.get_other_sticker_locations(ring_color_location)[0]
                self._add_and_apply(place_ring_color_moves, move)
                self._add_and_apply(place_ring_color_moves, move)

                self._add_and_apply(place_ring_color_moves, revered_move_2)
                if revered_move_1 is not None:
                    self._add_and_apply(place_ring_color_moves, revered_move_1)

            # here both white location and ring color location are updated
            move = self.cube.get_move_to_rotate_face(up_color_location.face_id, True)
            while ring_color_location.face_id is not ring_face_id:
                ring_color_location = self.cube.trace_a_moved_sticker(ring_color_location, move)
                self._add_and_apply(place_ring_color_moves, move)

            move = self.cube.get_move_to_rotate_face(ring_color_location.face_id, True)
            self._add_and_apply(place_ring_color_moves, move)
            self._add_and_apply(place_ring_color_moves, move)

            place_edges_moves.extend(place_ring_color_moves)

        return place_edges_moves

    def solve_u_color(self) -> list[Move]:
        moves = []
        up_color = self.faces_colors[FaceID.U]

        for corner_other_colors in self.ring_corner_colors:
            place_corner_moves = []

            first_color, second_color = corner_other_colors
            corner_colors: list[Color] = [up_color] + corner_other_colors
            up_color_location, first_loc, second_loc = self.find_sticker_locations(corner_colors)

            if up_color_location.face_id is FaceID.U:
                if first_loc.face_id is self.color_faces[first_color]:
                    continue  # corner in place
                # move the incorrectly placed corner to the X2 move strip
                place_corner_moves.extend(self._from_third_ring_corner_to_u(up_color_location, first_loc))

            elif first_loc.face_id is FaceID.U or second_loc.face_id is FaceID.U:
                up_location = first_loc if first_loc.face_id is FaceID.U else second_loc
                place_corner_moves.extend(self._from_third_ring_corner_to_u(up_location, up_color_location))
                # now the up_color location is in the X2 move strip

            elif up_color_location.face_id is FaceID.D:
                # put the up_color_location under its gaol location
                move = self.cube.get_move_to_rotate_face(FaceID.D, True)
                while first_loc.face_id is not self.color_faces[second_color]:
                    first_loc = self.cube.trace_a_moved_sticker(first_loc, move)
                    self._add_and_apply(place_corner_moves, move)

                goal_location = Solver3x3.get_up_corner_location(self.color_faces[first_color],
                                                                 self.color_faces[second_color])
                # other location doesn't matter
                goal_other_location = self.cube.get_other_sticker_locations(goal_location)[0]

                place_corner_moves.extend(self._from_third_ring_corner_to_u(goal_location, goal_other_location))
                # now the up_color location is in the X2 move strip

            # put corner from X2 strip to U face:
            up_color_location, down_loc, second_loc = self.find_sticker_locations(corner_colors)
            down_color = first_color
            if down_loc.face_id is not FaceID.D:
                down_loc, second_loc = second_loc, down_loc
                down_color = second_color

            move = self.cube.get_move_to_rotate_face(FaceID.D, True)
            while second_loc.face_id is not self.color_faces[down_color]:
                second_loc = self.cube.trace_a_moved_sticker(second_loc, move)
                self._add_and_apply(place_corner_moves, move)

            goal_location = Solver3x3.get_up_corner_location(self.color_faces[first_color],
                                                             self.color_faces[second_color])
            goal_other_locations = self.cube.get_other_sticker_locations(goal_location)
            if goal_other_locations[0].face_id is self.color_faces[down_color]:
                move_down_location = goal_other_locations[0]
            else:
                move_down_location = goal_other_locations[1]

            place_corner_moves.extend(self._from_third_ring_corner_to_u(goal_location, move_down_location))

            moves.extend(place_corner_moves)

        return moves

    def _from_third_ring_corner_to_u(self, up_location: Location, move_down_location: Location) -> list[Move]:
        """
        Calculates and applies the needed moves to move a sticker from the third ring corner (on the X2 move axis) to
        `FaceID.U` face.
        :param up_location: The goal up location.
        :param move_down_location: The location to specify which way to go down. Must be on of the other sides of
            `up_location`.
        :return: The moves that were applied during the process.
        """
        moves: list[Move] = []

        move = self.cube.get_needed_single_move(move_down_location, FaceID.D)
        reversed_move = move.reversed()
        up_location = self.cube.trace_a_moved_sticker(up_location, move)
        move_down_location = self.cube.trace_a_moved_sticker(move_down_location, move)
        self._add_and_apply(moves, move)

        other_sticker_locations = self.cube.get_other_sticker_locations(up_location)
        if other_sticker_locations[0] == move_down_location:
            third_location: Location = other_sticker_locations[1]
        else:
            third_location: Location = other_sticker_locations[0]

        move = self.cube.get_needed_single_move(up_location, third_location.face_id)
        self._add_and_apply(moves, move)
        self._add_and_apply(moves, reversed_move)

        return moves

    def solve_second_x_strip(self) -> list[Move]:
        return []

    def solve_d_cross(self) -> tuple[bool, list[Move]]:
        return True, []

    def solve_d_corner_positions(self) -> tuple[bool, list[Move]]:
        return True, []

    def solve_d_corners(self) -> list[Move]:
        return []

# todo: generalize while loop search for correct spot in a strip. -> reduce moves to solve
