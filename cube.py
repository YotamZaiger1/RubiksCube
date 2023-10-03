from color import Color
from face import Face
from face_id import FaceID, LEFT, UP, RIGHT, DOWN
from move import Move
from orientation import Orientation

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

    def find_other_sticker_locations(self, sticker_face: FaceID, row: int, col: int) -> list[list[FaceID, int, int]]:
        """
        Finds the other locations (face_id, row, col) of a given edge sticker.
        :param sticker_face: The known face of the sticker.
        :param row: The row of the sticker in `sticker_face`.
        :param col: The column of the sticker in `sticker_face`.
        :return: A list contains the other locations (face_id, row, col) of the specified edge.
        """
        if self.size <= 2:
            ValueError(f"Cube of size {self.size} does not have edge stickers.")

        adjacent_face_ids: list[FaceID] = []

        if row == 0:
            adjacent_face_ids.append(sticker_face.get_side_linked_face(UP))
        if row == self.size - 1:
            adjacent_face_ids.append(sticker_face.get_side_linked_face(DOWN))
        if col == 0:
            adjacent_face_ids.append(sticker_face.get_side_linked_face(LEFT))
        if col == self.size - 1:
            adjacent_face_ids.append(sticker_face.get_side_linked_face(RIGHT))

        locations: list[list[FaceID, int, int]] = []

        for adjacent_face_id in adjacent_face_ids:
            move = self.get_needed_single_move(sticker_face, row, col, adjacent_face_id)
            from_index_translator = self.faces[sticker_face].get_strip_index_translator(move.orientation, move.index)
            i = from_index_translator.inverse((row, col))

            adjacent_face = self.faces[adjacent_face_id]
            to_index_translator = adjacent_face.get_strip_index_translator(move.orientation, move.index)
            to_row, to_col = to_index_translator.opposite(i)
            locations.append([adjacent_face_id, to_row, to_col])

        return locations

    def get_needed_single_move(self, from_face_id: FaceID, from_row: int, from_col: int, to_face_id: FaceID) -> Move:
        move_orientation, is_forward = Orientation.find_needed_single_move_orientation(from_face_id, to_face_id)

        index = self.faces[from_face_id].find_move_index_from_real_indices(move_orientation, from_row, from_col)
        return Move(move_orientation, index, is_forward)

    def __eq__(self, cube: 'Cube') -> bool:
        return self.faces == cube.faces
