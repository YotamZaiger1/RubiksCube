import random

from Cube.color import Color
from Cube.face import Face
from Cube.face_id import FaceID, LEFT, UP, RIGHT, DOWN
from Cube.location import Location
from Cube.move import Move
from Cube.orientation import Orientation

ORDERED_COLORS = {FaceID.U: Color.Wh, FaceID.F: Color.Bl, FaceID.R: Color.Or, FaceID.B: Color.Gr,
                  FaceID.L: Color.Re, FaceID.D: Color.Ye}


class Cube:
    def __init__(self, size: int, faces: dict[FaceID, Face] = None):
        self.size: int = size

        if faces is None:
            faces = dict()
            for face_id in FaceID:
                color = ORDERED_COLORS[face_id]
                stickers = [[color for _ in range(size)] for _ in range(size)]
                faces[face_id] = Face(size, face_id, stickers)

        self.faces: dict[FaceID, Face] = faces

    def generate_shuffle_moves(self, moves_number: int) -> list[Move]:
        moves: list[Move] = []
        for _ in range(moves_number):
            orientation = random.choice([Orientation.X, Orientation.Y, Orientation.Z])
            index = random.randint(0, self.size - 1)
            is_forward = random.choice([True, False])
            move = Move(orientation, index, is_forward)

            moves.append(move)
        return moves

    def move(self, move: Move) -> None:
        effected_faces = Orientation.get_orientation_rotation_faces_ids(move.orientation)

        direction_factor = 1 if move.is_forward else -1

        last_strip = self.faces[effected_faces[0]].get_strip(move.orientation, move.index)

        for i in range(len(effected_faces)):
            new_face_id = effected_faces[((i + 1) * direction_factor) % len(effected_faces)]
            new_face = self.faces[new_face_id]

            curr_strip = new_face.get_strip(move.orientation, move.index)
            new_face.set_strip(move.orientation, move.index, last_strip)
            last_strip = curr_strip

        # find inplace-rotated face
        if move.index == 0:
            if move.orientation is Orientation.X:
                self.faces[FaceID.U].rotate_face(not move.is_forward)
            elif move.orientation is Orientation.Y:
                self.faces[FaceID.L].rotate_face(not move.is_forward)
            elif move.orientation is Orientation.Z:
                self.faces[FaceID.B].rotate_face(move.is_forward)
        elif move.index == self.size - 1:
            if move.orientation is Orientation.X:
                self.faces[FaceID.D].rotate_face(move.is_forward)
            elif move.orientation is Orientation.Y:
                self.faces[FaceID.R].rotate_face(move.is_forward)
            elif move.orientation is Orientation.Z:
                self.faces[FaceID.F].rotate_face(not move.is_forward)

    def execute_moves(self, moves: list[Move]) -> None:
        for move in moves:
            self.move(move)

    def trace_a_moved_sticker(self, original_location: Location, move: Move) -> Location:
        """
        Returns where `original_location` will be after the move `move` would be applied (Not applies `move` on the
        Cube). `original_location` must be a location that moves to a new face after the move `move` would be applied.
        Otherwise, a `ValueError` would be raised.
        :param original_location: The location to trace.
        :param move: The move to trace the location with.
        :return: The location where `original_location` will be in after the move `move` would be applied.
        """
        effected_faces = Orientation.get_orientation_rotation_faces_ids(move.orientation)
        if original_location.face_id not in effected_faces or self.faces[
            original_location.face_id].find_move_index_from_real_indices(move.orientation,
                                                                         original_location.row,
                                                                         original_location.col) != move.index:
            raise ValueError("The given location does not move to another face.")

        direction = 1 if move.is_forward else -1
        new_face_id = effected_faces[
            (effected_faces.index(original_location.face_id) + direction) % len(effected_faces)]

        curr_index_translator = self.faces[original_location.face_id].get_strip_index_translator(
            move.orientation, move.index)
        new_index_translator = self.faces[new_face_id].get_strip_index_translator(move.orientation, move.index)

        i = curr_index_translator.inverse((original_location.row, original_location.col))
        new_row, new_col = new_index_translator.translate(i)

        return Location(new_face_id, new_row, new_col)

    def get_location_color(self, location: Location) -> Color:
        return self.faces[location.face_id][location.row][location.col]

    def get_other_sticker_locations(self, sticker_location: Location) -> list[Location]:
        """
        Finds the other locations (face_id, row, col) of a given edge sticker.
        :param sticker_location: The known sticker location.
        :return: A list contains the other locations of the specified edge.
        """
        if self.size <= 2:
            ValueError(f"Cube of size {self.size} does not have edge stickers.")

        sticker_face, row, col = sticker_location.face_id, sticker_location.row, sticker_location.col

        adjacent_face_ids: list[FaceID] = []

        if row == 0:
            adjacent_face_ids.append(sticker_face.get_side_linked_face(UP))
        if row == self.size - 1:
            adjacent_face_ids.append(sticker_face.get_side_linked_face(DOWN))
        if col == 0:
            adjacent_face_ids.append(sticker_face.get_side_linked_face(LEFT))
        if col == self.size - 1:
            adjacent_face_ids.append(sticker_face.get_side_linked_face(RIGHT))

        locations: list[Location] = []

        for adjacent_face_id in adjacent_face_ids:
            move = self.get_needed_single_move(sticker_location, adjacent_face_id)
            from_index_translator = self.faces[sticker_face].get_strip_index_translator(move.orientation, move.index)
            i = from_index_translator.inverse((row, col))

            adjacent_face = self.faces[adjacent_face_id]
            to_index_translator = adjacent_face.get_strip_index_translator(move.orientation, move.index)
            to_row, to_col = to_index_translator.opposite(i)
            locations.append(Location(adjacent_face_id, to_row, to_col))

        return locations

    def get_needed_single_move(self, from_location: Location, to_face_id: FaceID) -> Move:
        move_orientation, is_forward = Orientation.find_needed_single_move_orientation(from_location.face_id,
                                                                                       to_face_id)

        index = self.faces[from_location.face_id].find_move_index_from_real_indices(move_orientation, from_location.row,
                                                                                    from_location.col)
        return Move(move_orientation, index, is_forward)

    def get_move_to_rotate_face(self, face_id: FaceID, clockwise: bool):
        up_face_id = face_id.get_side_linked_face(UP)
        right_face_id = face_id.get_side_linked_face(RIGHT)
        left_face_id = face_id.get_side_linked_face(LEFT)

        sticker_other_locations = self.get_other_sticker_locations(Location(face_id, 0, 0))
        sticker_up_location = None
        for sticker_location in sticker_other_locations:
            if sticker_location.face_id is up_face_id:
                sticker_up_location = sticker_location
                break

        return self.get_needed_single_move(sticker_up_location, right_face_id if clockwise else left_face_id)

    def get_rotation_moves_till_found(self, face_id_to_rotate: FaceID, location_to_trace: Location,
                                      goal_face_id: FaceID) -> tuple[list[Move], Location]:
        """
        Calculate the fewest required moves to rotate `face_id_to_rotate` till `location_to_trace` will be in
        `goal_face_id`. Does not apply any move to `self.Cube`.
        :param face_id_to_rotate: The face that being rotated.
        :param location_to_trace: The location to trace.
        :param goal_face_id: The goal face id for `location_to_trace`
        :return: A list with the fewest required moves to rotate `face_id_to_rotate` till `location_to_trace` will be in
            `goal_face_id`. And the location of `location_to_trace` after the moves would be applied.
        """
        if location_to_trace.face_id is goal_face_id:
            return [], location_to_trace

        move = self.get_move_to_rotate_face(face_id_to_rotate, True)
        new_location = self.trace_a_moved_sticker(location_to_trace, move)
        if new_location.face_id is goal_face_id:
            return [move], new_location

        move = move.reversed()  # counterclockwise
        new_location = self.trace_a_moved_sticker(location_to_trace, move)
        if new_location.face_id is goal_face_id:
            return [move], new_location

        new_location = self.trace_a_moved_sticker(new_location, move)
        return [move, move], new_location

    def copy(self) -> 'Cube':
        faces: dict[FaceID: Face] = dict()

        for face_id in FaceID:
            face: Face = self.faces[face_id]
            faces[face_id] = face.copy()

        return Cube(self.size, faces)

    def __eq__(self, cube: 'Cube') -> bool:
        return self.faces == cube.faces
