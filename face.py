from face_id import FaceID
from color import Color
from orientation import Orientation
from index_translator import IndexTranslator, TOP_DOWN, BOTTOM_UP, LEFT_RIGHT, RIGHT_LEFT


class Face:
    def __init__(self, size: int, face_id: FaceID, stickers: list[list[Color]]):
        self.size: int = size
        self.face_id: FaceID = face_id

        self.stickers = stickers

    def get_strip_index_translator(self, orientation: Orientation, index: int) -> IndexTranslator:
        """
        Returns an index translator to convert the i-th index of the specified strip to its actual index in
        `self.stickers`.

        See:
            documentation/xyz orientation.png

        :param orientation: Which strip orientation to return (specified in the documentation).
        :param index: The index of the strip in the face (specified in the documentation).
        :return: An index translator to convert the i-th index of the specified strip to its actual index in
            `self.stickers`.
        """
        if orientation is Orientation.X:
            if self.face_id is FaceID.F:
                index_translator = IndexTranslator(LEFT_RIGHT, index, self.size)
            elif self.face_id is FaceID.R:
                index_translator = IndexTranslator(BOTTOM_UP, index, self.size)
            elif self.face_id is FaceID.B:
                index_translator = IndexTranslator(RIGHT_LEFT, (-index - 1) % self.size, self.size)
            elif self.face_id is FaceID.L:
                index_translator = IndexTranslator(TOP_DOWN, (-index - 1) % self.size, self.size)
            else:
                raise ValueError(Face._error_message_illegal_face_id_for_orientation(self.face_id, orientation))

            return index_translator

        elif orientation is Orientation.Y:
            if self.face_id is FaceID.F or self.face_id is FaceID.U or self.face_id is FaceID.B:
                index_translator = IndexTranslator(BOTTOM_UP, index, self.size)
            elif self.face_id is FaceID.D:
                index_translator = IndexTranslator(TOP_DOWN, (-index - 1) % self.size, self.size)
            else:
                raise ValueError(Face._error_message_illegal_face_id_for_orientation(self.face_id, orientation))

            return index_translator

        elif orientation is Orientation.Z:
            if (self.face_id is FaceID.D or self.face_id is FaceID.R or
                    self.face_id is FaceID.U or self.face_id is FaceID.L):
                index_translator = IndexTranslator(RIGHT_LEFT, index, self.size)
            else:
                raise ValueError(Face._error_message_illegal_face_id_for_orientation(self.face_id, orientation))

            return index_translator

        else:
            raise ValueError(Orientation.not_recognized_orientation_error_msg(orientation))

    def get_strip(self, orientation: Orientation, index) -> list[Color]:
        strip = []
        index_translator = self.get_strip_index_translator(orientation, index)
        for i in range(self.size):
            row, col = index_translator.translate(i)
            strip.append(self.stickers[row][col])
        return strip

    def set_strip(self, orientation: Orientation, index, new_strip) -> None:
        index_translator = self.get_strip_index_translator(orientation, index)
        for i in range(self.size):
            row, col = index_translator.translate(i)
            self.stickers[row][col] = new_strip[i]

    def find_move_index_from_real_indices(self, move_orientation: Orientation, row: int, col: int) -> int:
        illegal_face_id_for_orientation = False
        index = -1

        if move_orientation is Orientation.X:
            if self.face_id is FaceID.F:
                index = row
            elif self.face_id is FaceID.R:
                index = col
            elif self.face_id is FaceID.B:
                index = self.size - 1 - row
            elif self.face_id is FaceID.L:
                index = self.size - 1 - col
            else:
                illegal_face_id_for_orientation = True

        elif move_orientation is Orientation.Y:
            if self.face_id is FaceID.F or self.face_id is FaceID.U or self.face_id is FaceID.B:
                index = col
            elif self.face_id is FaceID.D:
                index = self.size - 1 - col
            else:
                illegal_face_id_for_orientation = True

        elif move_orientation is Orientation.Z:
            if (self.face_id is FaceID.D or self.face_id is FaceID.R or
                    self.face_id is FaceID.U or self.face_id is FaceID.L):
                index = row
            else:
                illegal_face_id_for_orientation = True
        else:
            raise ValueError(Orientation.not_recognized_orientation_error_msg(move_orientation))

        if illegal_face_id_for_orientation:
            raise ValueError(Face._error_message_illegal_face_id_for_orientation(self.face_id, move_orientation))

        return index

    ####################################################################################################################

    def rotate_face(self, clockwise: bool):
        """
        90 degrees rotation of `self.stickers`.
        """
        stickers = self.stickers

        if clockwise:
            stickers = stickers[::-1]  # reverse rows
            stickers = [list(row) for row in zip(*stickers)]  # transpose
        else:
            stickers = [list(row) for row in zip(*stickers)]  # transpose
            stickers = stickers[::-1]  # reverse rows

        self.stickers = stickers

    @staticmethod
    def _error_message_illegal_face_id_for_orientation(face_id: FaceID, required_orientation: Orientation) -> str:
        return f"The face {face_id.name!r} does not support {required_orientation.name!r} orientation."

    def __getitem__(self, item: int) -> list[Color]:
        return self.stickers[item]

    def __eq__(self, other: 'Face'):
        return self.stickers == other.stickers
