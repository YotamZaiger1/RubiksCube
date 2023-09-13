from enum import Enum, unique, auto
from color import Color
from orientation import Orientation


@unique
class FaceID(Enum):
    U = auto()
    D = auto()
    R = auto()
    L = auto()
    F = auto()
    B = auto()


class Face:
    def __init__(self, size: int, face_id: FaceID, stickers: list[list[Color]]):
        self.size: int = size
        self.face_id: FaceID = face_id

        self.stickers = stickers

    def get_strip_index_generator(self, orientation: Orientation, index: int):
        """
        Returns an index generator which contains the real indices in `self.stickers` of the specified orientation strip
        on this face.

        See:
            documentation/xyz orientation.png

        Parameters:
                orientation (int): Which strip orientation to return (specified in the documentation).
                index (int): The index of the strip in the face (specified in the documentation).

        Returns:
            index generator: Generator of the real indices in `self.stickers` of the specified orientation strip on this
             face.
        """
        if orientation is Orientation.X:
            if self.face_id is FaceID.F:
                index_generator = self._left_right_strip_indices_generator(index)
            elif self.face_id is FaceID.R:
                index_generator = self._bottom_up_strip_indices_generator(index)
            elif self.face_id is FaceID.B:
                index_generator = self._right_left_strip_indices_generator(-index - 1)
            elif self.face_id is FaceID.L:
                index_generator = self._top_down_strip_indices_generator(-index - 1)
            else:
                raise Exception(Face._error_message_illegal_face_id_for_strip(self.face_id, orientation))

            return index_generator

        elif orientation is Orientation.Y:
            if self.face_id is FaceID.F or self.face_id is FaceID.U or self.face_id is FaceID.B:
                index_generator = self._bottom_up_strip_indices_generator(index)
            elif self.face_id is FaceID.D:
                index_generator = self._top_down_strip_indices_generator(-index - 1)
            else:
                raise Exception(Face._error_message_illegal_face_id_for_strip(self.face_id, orientation))

            return index_generator

        elif orientation is Orientation.Z:
            if (self.face_id is FaceID.D or self.face_id is FaceID.R or
                    self.face_id is FaceID.U or self.face_id is FaceID.L):
                index_generator = self._right_left_strip_indices_generator(index)
            else:
                raise Exception(Face._error_message_illegal_face_id_for_strip(self.face_id, orientation))

            return index_generator

        else:
            raise NotImplemented(Orientation.not_recognized_orientation_error_msg(orientation))

    def get_strip(self, orientation: Orientation, index) -> list[Color]:
        return [self.stickers[row][col] for row, col in self.get_strip_index_generator(orientation, index)]

    def set_strip(self, orientation: Orientation, index, new_strip) -> None:
        index_generator = self.get_strip_index_generator(orientation, index)
        for i, indices in enumerate(index_generator):
            row, col = indices
            self.stickers[row][col] = new_strip[i]

    def _top_down_strip_indices_generator(self, index: int):
        return ((i, index) for i in range(self.size))

    def _bottom_up_strip_indices_generator(self, index: int):
        return ((self.size - 1 - i, index) for i in range(self.size))

    def _left_right_strip_indices_generator(self, index: int):
        return ((index, i) for i in range(self.size))

    def _right_left_strip_indices_generator(self, index: int):
        return ((index, self.size - 1 - i) for i in range(self.size))

    def rotate_face(self, clockwise: bool):
        """90 degrees rotation"""
        stickers = self.stickers

        if clockwise:
            stickers = stickers[::-1]  # reverse rows
            stickers = [list(row) for row in zip(*stickers)]  # transpose
        else:
            stickers = [list(row) for row in zip(*stickers)]  # transpose
            stickers = stickers[::-1]  # reverse rows

        self.stickers = stickers

    @staticmethod
    def _error_message_illegal_face_id_for_strip(face_id: FaceID, required_orientation: Orientation) -> str:
        return f"The face {face_id.name!r} does not support {required_orientation.name!r} orientation stripes."

    def __getitem__(self, item: int) -> list[Color]:
        return self.stickers[item]

    def __eq__(self, other: 'Face'):
        return self.stickers == other.stickers
