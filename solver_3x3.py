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

        self.ring_color_pairs: list[list[Color]] = []
        self.ring_colors: list[Color] = []
        for i in range(len(RING_FACE_IDS)):
            color_a = self.faces_colors[RING_FACE_IDS[i]]
            color_b = self.faces_colors[RING_FACE_IDS[(i + 1) % len(RING_FACE_IDS)]]
            self.ring_color_pairs.append([color_a, color_b])
            self.ring_colors.append(color_a)

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
        raise ValueError(f"The given face ids ({id_1}, {id_2}) does not fit any corner.")

    @staticmethod
    def get_down_corner_location(id_1: FaceID, id_2: FaceID) -> Location:
        """
        Returns the corner location in the D face which has parts in `id_1` and in `id_2` faces.
        The order between `id_1` and `id_2` does not matter.
        :param id_1: A ring face id.
        :param id_2: A ring face id.
        :return: The corner location in the D face which has parts in `id_1` and in `id_2` faces.
        """
        ids = [id_1, id_2]
        if FaceID.F in ids and FaceID.R in ids:
            return Location(FaceID.D, 2, 0)
        if FaceID.R in ids and FaceID.B in ids:
            return Location(FaceID.D, 0, 0)
        if FaceID.B in ids and FaceID.L in ids:
            return Location(FaceID.D, 0, 2)
        if FaceID.L in ids and FaceID.F in ids:
            return Location(FaceID.D, 2, 2)
        raise ValueError(f"The given face ids ({id_1}, {id_2}) does not fit any corner.")

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

                    found_colors: set[Color] = {self.cube.get_location_color(loc) for loc in other_locations}
                    found_colors.add(face[i][j])  # add current color

                    if found_colors == colors_set:  # sticker found
                        locations = other_locations + [location]  # add current location

                        # sort by the order of colors in 'colors'
                        def sort_by(loc):
                            return colors.index(self.cube.get_location_color(loc))

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

        d_cross_positions = self.solve_d_cross_positions()
        moves += d_cross_positions

        can_solve_d_corner_positions, d_corner_position_moves = self.solve_d_corner_positions()
        moves += d_corner_position_moves
        if not can_solve_d_corner_positions:
            return False, moves

        can_solve_d_corner_orientations, d_corners_orientation_moves = self.solve_d_corner_orientations()
        moves += d_corners_orientation_moves
        return can_solve_d_corner_orientations, moves

    def _from_third_ring_corner_to_u(self, up_location: Location, move_down_location: Location) -> list[Move]:
        """
        Calculates and applies the needed moves to move a sticker from the third ring corner (on the X2 move axis) to
        `FaceID.U` face.
        :param up_location: The goal up location.
        :param move_down_location: A location to specify which way to go down. Must be on of the other sides of
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

    def _from_third_ring_edge_to_place(self, up_location: Location, move_down_first_location: Location,
                                       move_down_second_location) -> list[Move]:

        """
        Calculates and applies the needed moves to move a sticker from the third ring edge (on the X2 move axis) to
        its place.

        :param up_location: The location of sticker on the U face which is above the goal location.
        :param move_down_first_location: A location to specify which way to go down first. Must be one of the other
            sides of `up_location`.
        :param move_down_second_location: A location to specify which way to go down secondly. Must be one of the other
            sides of `up_location`.
        :return: The moves that were applied during the process.
        """
        moves = self._from_third_ring_corner_to_u(up_location, move_down_first_location)
        rotation_move = moves[1]
        self._add_and_apply(moves, rotation_move)

        moves.extend(self._from_third_ring_corner_to_u(up_location, move_down_second_location))
        return moves

    def _d_cross_action(self, down_location: Location, move_up_first_location: Location,
                        third_corner_location) -> list[Move]:
        """
        Calculates the needed moves to change the D face cross. Does not apply the moves to the cube.

        :param down_location: The location of a corner sticker on the D face.
        :param move_up_first_location: A location to specify which way to go up first. Must be one of the other sides
            of `down_location`.
        :param third_corner_location: The third location of the corner.
        :return: The needed moves for the process.
        """
        move_1 = self.cube.get_needed_single_move(down_location, move_up_first_location.face_id)
        move_2 = self.cube.get_needed_single_move(down_location, third_corner_location.face_id)
        move_3 = self.cube.get_needed_single_move(move_up_first_location, third_corner_location.face_id)

        moves = [move_1, move_3, move_2.reversed(), move_3.reversed(), move_2, move_1.reversed()]

        return moves

    def _d_edges_replacement(self, down_location: Location, move_down_location: Location,
                             third_corner_location) -> list[Move]:
        """
        Calculates the needed moves to replace positions between 2 D edges. Does not apply the moves to the cube.

        :param down_location: The location of a corner sticker on the D face.
        :param move_down_location: A location to specify which way to go down first. Must be one of the other sides
            of `down_location`.
        :param third_corner_location: The third location of the corner.
        :return: The needed moves for the process.
        """
        move_1 = self.cube.get_needed_single_move(move_down_location, down_location.face_id)
        move_2 = self.cube.get_needed_single_move(third_corner_location, move_down_location.face_id)

        moves = [move_1, move_2, move_2, move_1.reversed(), move_2.reversed(), move_1, move_2.reversed(),
                 move_1.reversed()]

        return moves

    def _d_corner_replacement(self, down_location: Location, move_down_location: Location,
                              third_corner_location) -> list[Move]:
        """
        Calculates the needed moves to replace positions between 3 D corners. Does not apply the moves to the cube.

        :param down_location: The location of a corner sticker on the D face which doesn't change its location.
        :param move_down_location: A location to specify which way to go down. Must be one of the other sides of
            `down_location`.
        :param third_corner_location: The third location of the corner.
        :return: The needed moves for the process.
        """
        rotation_move = self.cube.get_needed_single_move(third_corner_location, move_down_location.face_id)

        down_move_1 = self.cube.get_needed_single_move(move_down_location, down_location.face_id)

        after_rotation_move_ring_location = self.cube.trace_a_moved_sticker(third_corner_location, rotation_move)
        down_move_2 = self.cube.get_needed_single_move(after_rotation_move_ring_location, down_location.face_id)

        moves = [rotation_move, down_move_1, rotation_move.reversed(), down_move_2, rotation_move,
                 down_move_1.reversed(), rotation_move.reversed(), down_move_2.reversed()]

        return moves

    def _change_d_corners_orientation(self, down_location: Location, move_down_location: Location,
                                      third_corner_location) -> list[Move]:
        """
        Calculates the needed moves to change the orientation of 2 D corners. Does not apply the moves to the cube.

        :param down_location: The location of a corner sticker on the D face.
        :param move_down_location: A location to specify which way to go down first. Must be one of the other sides
            of `down_location`.
        :param third_corner_location: The third location of the corner.
        :return: The needed moves for the process.
        """
        rotation_move = self.cube.get_needed_single_move(third_corner_location, move_down_location.face_id)

        after_rotation_move_ring_location_1 = self.cube.trace_a_moved_sticker(third_corner_location, rotation_move)
        after_rotation_move_ring_location_2 = self.cube.trace_a_moved_sticker(move_down_location, rotation_move)
        other_locations = self.cube.get_other_sticker_locations(after_rotation_move_ring_location_1)
        other_locations.remove(after_rotation_move_ring_location_2)
        second_down_location = other_locations[0]

        moves = (self._d_edges_replacement(down_location, move_down_location, third_corner_location) +
                 self._d_edges_replacement(second_down_location, after_rotation_move_ring_location_1,
                                           after_rotation_move_ring_location_2))

        return moves

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
                # up_color_location is now not updated

                self._add_and_apply(place_ring_color_moves, move)
                self._add_and_apply(place_ring_color_moves, move)

                self._add_and_apply(place_ring_color_moves, revered_move_2)
                if revered_move_1 is not None:
                    self._add_and_apply(place_ring_color_moves, revered_move_1)

            # here both white location and ring color location are updated
            rotation_moves, ring_color_location = self.cube.get_rotation_moves_till_found(FaceID.D,
                                                                                          ring_color_location,
                                                                                          ring_face_id)
            place_ring_color_moves.extend(rotation_moves)
            self.cube.execute_moves(rotation_moves)

            move = self.cube.get_move_to_rotate_face(ring_color_location.face_id, True)
            self._add_and_apply(place_ring_color_moves, move)
            self._add_and_apply(place_ring_color_moves, move)

            place_edges_moves.extend(place_ring_color_moves)

        return place_edges_moves

    def solve_u_color(self) -> list[Move]:
        moves = []
        up_color = self.faces_colors[FaceID.U]

        for corner_other_colors in self.ring_color_pairs:
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
                rotation_moves, first_loc = self.cube.get_rotation_moves_till_found(FaceID.D, first_loc,
                                                                                    self.color_faces[second_color])
                place_corner_moves.extend(rotation_moves)
                self.cube.execute_moves(rotation_moves)

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

            rotation_moves, second_loc = self.cube.get_rotation_moves_till_found(FaceID.D, second_loc,
                                                                                 self.color_faces[down_color])
            place_corner_moves.extend(rotation_moves)
            self.cube.execute_moves(rotation_moves)

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

    def solve_second_x_strip(self) -> list[Move]:
        moves = []

        for edge_colors in self.ring_color_pairs:
            place_edge_moves = []
            first_color, second_color = edge_colors
            first_goal_id, second_goal_id = self.color_faces[first_color], self.color_faces[second_color]

            first_loc, second_loc = self.find_sticker_locations(edge_colors)

            if first_loc.face_id is first_goal_id and second_loc.face_id is second_goal_id:
                continue

            if first_loc.face_id in RING_FACE_IDS and second_loc.face_id in RING_FACE_IDS:
                up_location = self.get_up_corner_location(first_loc.face_id, second_loc.face_id)
                up_other_locations = self.cube.get_other_sticker_locations(up_location)

                place_edge_moves.extend(
                    self._from_third_ring_edge_to_place(up_location, up_other_locations[0], up_other_locations[1]))
                first_loc, second_loc = self.find_sticker_locations(edge_colors)

            # sticker is now in the X2 strip
            up_location = self.get_up_corner_location(first_goal_id, second_goal_id)
            up_other_locations = self.cube.get_other_sticker_locations(up_location)

            # make the firs location and its parameters be the location in the ring side:
            if first_loc.face_id is FaceID.D:
                first_loc, second_loc = second_loc, first_loc
                first_goal_id, second_goal_id = second_goal_id, first_goal_id
            if up_other_locations[0].face_id is not first_goal_id:
                up_other_locations.reverse()
            # first_color and second_color are now not updated

            rotation_target_face_id = second_goal_id.opposite()
            rotation_moves, new_location = self.cube.get_rotation_moves_till_found(FaceID.D, first_loc,
                                                                                   rotation_target_face_id)
            place_edge_moves.extend(rotation_moves)
            self.cube.execute_moves(rotation_moves)

            place_edge_moves.extend(
                self._from_third_ring_edge_to_place(up_location, up_other_locations[0], up_other_locations[1]))

            moves.extend(place_edge_moves)

        return moves

    def solve_d_cross(self) -> tuple[bool, list[Move]]:
        moves = []
        down_color_locations = self._find_d_cross_locations()

        if len(down_color_locations) % 2 == 1:
            return False, moves

        if len(down_color_locations) == 0:
            d_cross_moves = self._d_cross_none()
            moves.extend(d_cross_moves)
            self.cube.execute_moves(d_cross_moves)

            down_color_locations = self._find_d_cross_locations()

        if len(down_color_locations) == 2:
            first_loc, second_loc = down_color_locations
            first_other_loc = self.cube.get_other_sticker_locations(first_loc)[0]
            second_other_loc = self.cube.get_other_sticker_locations(second_loc)[0]

            first_face_id, second_face_id = first_other_loc.face_id, second_other_loc.face_id
            if first_face_id is second_face_id.opposite():
                d_cross_moves = self._d_cross_line(first_face_id)
            else:
                d_cross_moves = self._d_cross_adjacent(first_face_id, second_face_id)
            moves.extend(d_cross_moves)
            self.cube.execute_moves(d_cross_moves)

        return True, moves

    def _find_d_cross_locations(self):
        down_color = self.faces_colors[FaceID.D]
        down_color_locations = []
        for row, col in [[0, 1], [1, 0], [1, 2], [2, 1]]:
            if self.cube.faces[FaceID.D][row][col] is down_color:
                down_color_locations.append(Location(FaceID.D, row, col))
        return down_color_locations

    def _d_cross_none(self) -> list[Move]:
        d_location = Location(FaceID.D, 0, 0)  # corner choice does not matter
        second_loc, third_loc = self.cube.get_other_sticker_locations(d_location)

        return self._d_cross_action(d_location, second_loc, third_loc)

    def _d_cross_line(self, d_color_face_id: FaceID) -> list[Move]:
        second_face_id = None
        for face_id in RING_FACE_IDS:
            if face_id is not d_color_face_id and face_id is not d_color_face_id.opposite():
                second_face_id = face_id
                break

        d_location = Solver3x3.get_down_corner_location(d_color_face_id, second_face_id)
        first_location, second_location = self.cube.get_other_sticker_locations(d_location)
        if first_location.face_id is not d_color_face_id:
            first_location, second_location = second_location, first_location

        moves = self._d_cross_action(d_location, first_location, second_location)
        return Move.get_inverted_moves(moves)

    def _d_cross_adjacent(self, d_color_face_id_1: FaceID, d_color_face_id_2: FaceID) -> list[Move]:
        d_location = Solver3x3.get_down_corner_location(d_color_face_id_1.opposite(), d_color_face_id_2.opposite())
        first_location, second_location = self.cube.get_other_sticker_locations(d_location)
        return self._d_cross_action(d_location, first_location, second_location)

    def solve_d_cross_positions(self) -> list[Move]:
        moves = []
        rotation_fitting_locations = self._d_cross_positions_find_edges()

        if len(rotation_fitting_locations) == 0:
            d_location = Location(FaceID.D, 0, 0)  # corner choice does not matter
            first_location, second_location = self.cube.get_other_sticker_locations(d_location)
            edge_replacement_moves = self._d_edges_replacement(d_location, first_location, second_location)
            moves.extend(edge_replacement_moves)
            self.cube.execute_moves(edge_replacement_moves)
            rotation_fitting_locations = self._d_cross_positions_find_edges()

        if len(rotation_fitting_locations) == 2:
            first_fitting_location, second_fitting_location = rotation_fitting_locations
            d_location = Solver3x3.get_down_corner_location(first_fitting_location.face_id.opposite(),
                                                            second_fitting_location.face_id.opposite())
            first_location, second_location = self.cube.get_other_sticker_locations(d_location)
            edge_replacement_moves = self._d_edges_replacement(d_location, first_location, second_location)
            moves.extend(edge_replacement_moves)
            self.cube.execute_moves(edge_replacement_moves)

        location = Location(FaceID.F, 2, 1)  # an edge location from D face
        found_color = self.cube.get_location_color(location)
        target_face_id = self.color_faces[found_color]
        rotation_moves, location = self.cube.get_rotation_moves_till_found(FaceID.D, location, target_face_id)
        moves.extend(rotation_moves)
        self.cube.execute_moves(rotation_moves)

        return moves

    def _d_cross_positions_find_edges(self) -> list[Location]:
        """
        Finds the locations of the ring-colored-D edges which are in the correct position relative to the other D edges.
        :return: A list contains the locations of the ring-colored-D edges which are in the correct position relative to
            the other D edges.
        """
        ring_locations = [Location(FaceID.F, 2, 1), Location(FaceID.R, 1, 2), Location(FaceID.B, 0, 1),
                          Location(FaceID.L, 1, 0)]
        found_ring_colors = [self.cube.get_location_color(location) for location in ring_locations]

        rotation_fitting_locations = []
        for i in range(len(self.ring_colors)):
            index_1 = found_ring_colors.index(self.ring_colors[i])
            index_2 = found_ring_colors.index(self.ring_colors[(i + 1) % len(self.ring_colors)])
            if (index_1 + 1) % len(self.ring_colors) == index_2:
                if len(rotation_fitting_locations):
                    return ring_locations

                rotation_fitting_locations.append(ring_locations[index_1])
                rotation_fitting_locations.append(ring_locations[index_2])

        return rotation_fitting_locations

    def solve_d_corner_positions(self) -> tuple[bool, list[Move]]:
        fitting_locations, unfitting_locations = self._d_corner_positions_find_locations()
        if len(fitting_locations) == 2:
            return False, []

        moves = []

        if len(fitting_locations) == 0:
            d_location = unfitting_locations[0]
            move_d_location, third_location = self.cube.get_other_sticker_locations(d_location)
            corner_replacement_moves = self._d_corner_replacement(d_location, move_d_location, third_location)

            moves.extend(corner_replacement_moves)
            self.cube.execute_moves(corner_replacement_moves)
            fitting_locations, unfitting_locations = self._d_corner_positions_find_locations()

        if len(fitting_locations) == 1:
            d_location = fitting_locations[0]
            move_d_location, third_location = self.cube.get_other_sticker_locations(d_location)

            demo_move = self.cube.get_needed_single_move(move_d_location, third_location.face_id)
            demo_location = self.cube.trace_a_moved_sticker(move_d_location, demo_move)
            other_demo_locations = self.cube.get_other_sticker_locations(demo_location)
            found_ring_colors = [self.cube.get_location_color(location) for location in other_demo_locations]
            found_ring_colors.append(self.cube.get_location_color(demo_location))
            found_ring_colors.remove(self.faces_colors[FaceID.D])

            if (self.faces_colors[move_d_location.face_id.opposite()] not in found_ring_colors or
                    self.faces_colors[third_location.face_id.opposite()] not in found_ring_colors):
                move_d_location, third_location = third_location, move_d_location

            corner_replacement_moves = self._d_corner_replacement(d_location, move_d_location, third_location)
            moves.extend(corner_replacement_moves)
            self.cube.execute_moves(corner_replacement_moves)

        return True, moves

    def _d_corner_positions_find_locations(self) -> tuple[list[Location], list[Location]]:
        """
        Finds the locations of the ring-colored-D corners which are in the correct place (but may not be in the correct
        orientation).
        :return: 2 lists, the first contains the D-locations of the fitting corners, the second contains the D-locations
            of the unfitting corners.
        """
        fitting_locations = []
        unfitting_locations = []
        for first_color, second_color in self.ring_color_pairs:
            desired_first_id, desired_second_id = self.color_faces[first_color], self.color_faces[second_color]

            corner_location = self.get_down_corner_location(desired_first_id, desired_second_id)
            other_corner_locations = self.cube.get_other_sticker_locations(corner_location)

            found_colors = [self.cube.get_location_color(location) for location in other_corner_locations]
            found_colors.append(self.cube.get_location_color(corner_location))

            if first_color in found_colors and second_color in found_colors:
                fitting_locations.append(corner_location)
            else:
                unfitting_locations.append(corner_location)

        return fitting_locations, unfitting_locations

    def solve_d_corner_orientations(self) -> tuple[bool, list[Move]]:
        ring_face_id_pairs = [[FaceID.R, FaceID.B], [FaceID.B, FaceID.L], [FaceID.F, FaceID.R], [FaceID.L, FaceID.F]]
        down_corner_locations = [self.get_down_corner_location(id1, id2) for id1, id2 in ring_face_id_pairs]

        x, y, z, w = [self._get_d_corner_orientation_value(location) for location in down_corner_locations]
        if (x + w) % 3 != (y + z) % 3:
            return False, []

        a, b, g, d = self._d_corner_orientation_find_best_abgd(x, z, w)
        moves = []
        moves.extend(
            self._d_corner_orientation_convert_v_to_sub_step_moves(a, 2,
                                                                   self.get_down_corner_location(FaceID.R, FaceID.F),
                                                                   FaceID.F))
        moves.extend(
            self._d_corner_orientation_convert_v_to_sub_step_moves(b, 2,
                                                                   self.get_down_corner_location(FaceID.L, FaceID.F),
                                                                   FaceID.F))
        moves.extend(
            self._d_corner_orientation_convert_v_to_sub_step_moves(g, 1,
                                                                   self.get_down_corner_location(FaceID.L, FaceID.B),
                                                                   FaceID.L))
        moves.extend(
            self._d_corner_orientation_convert_v_to_sub_step_moves(d, 1,
                                                                   self.get_down_corner_location(FaceID.R, FaceID.F),
                                                                   FaceID.R))
        self.cube.execute_moves(moves)
        return True, moves

    def _get_d_corner_orientation_value(self, corner_location: Location) -> int:
        """
        Returns the orientation value of a given corner. For details see:
        "documentation/last_step_of_3x3_solution_idea/last_step_of_3x3_solution_idea.pdf".
        :param corner_location: One of the locations of a corner of the D face.
        :return: The orientation value of a given corner.
        """
        d_color = self.faces_colors[FaceID.D]

        if self.cube.get_location_color(corner_location) is d_color:
            d_color_face_id = corner_location.face_id

        else:
            first_loc, second_loc = self.cube.get_other_sticker_locations(corner_location)
            if self.cube.get_location_color(first_loc) is d_color:
                d_color_face_id = first_loc.face_id
            elif self.cube.get_location_color(second_loc) is d_color:
                d_color_face_id = second_loc.face_id
            else:
                raise ValueError(f"The given corner doesn't have any down-colored ({d_color.name}) location.")

        if d_color_face_id is FaceID.D:
            return 0
        if d_color_face_id is FaceID.F or d_color_face_id is FaceID.B:
            return 1
        if d_color_face_id is FaceID.R or d_color_face_id is d_color_face_id.L:
            return 2
        raise ValueError(f"The given corner is not in the {FaceID.D.name} face.")

    @staticmethod
    def _d_corner_orientation_find_best_abgd(x: int, z: int, w: int) -> tuple[int, int, int, int]:
        """
        When a solution exists, finds the one with the most occurrences of 0. For details see:
        "documentation/last_step_of_3x3_solution_idea/last_step_of_3x3_solution_idea.pdf".
        :param x: The x value.
        :param z: The z value.
        :param w: The w value.
        :return: The alpha, betta, gamma, delta values of the solution with the most occurrences of 0.
        """
        best_answer = []
        num_of_zeroes_in_best = -1

        for t in range(3):  # all options for t in Z3
            answer = [-t - z, -t - w, t + z - x, t]
            for i in range(len(answer)):
                answer[i] %= 3

            num_of_zeroes = answer.count(0)
            if num_of_zeroes > num_of_zeroes_in_best:
                best_answer = answer
                num_of_zeroes_in_best = num_of_zeroes

        return tuple(best_answer)

    def _d_corner_orientation_convert_v_to_sub_step_moves(self, v: int, invert_on: int, d_location: Location,
                                                          move_down_face_id: FaceID) -> list[Move]:
        """
        Converts a result variable to the specified sub-step moves. Does not apply any move. For more details about the
        sub-steps see: "documentation/last_step_of_3x3_solution_idea/last_step_of_3x3_solution_idea.pdf".
        :param v: A result variable.
        :param invert_on: On which value of `v` we should invert the moves.
        :param d_location: The D face corner location of the sub-step.
        :param move_down_face_id: A location to specify which way to go down first in the sub-step if it would be run in
            regular order. `move_down_face_id` Must be one of the other sides of `d_location`.
        :return: A list containing the moves for the specified sub-step.
        """
        if v == 0:
            return []

        move_down_location, third_location = self.cube.get_other_sticker_locations(d_location)
        if move_down_location.face_id is not move_down_face_id:
            move_down_location, third_location = third_location, move_down_location

        change_orientation_moves = self._change_d_corners_orientation(d_location, move_down_location, third_location)

        if v == invert_on:
            change_orientation_moves = Move.get_inverted_moves(change_orientation_moves)

        return change_orientation_moves
