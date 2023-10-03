from enum import Enum, unique, auto

LEFT, UP, RIGHT, DOWN = range(4)


@unique
class FaceID(Enum):
    U = auto()
    D = auto()
    R = auto()
    L = auto()
    F = auto()
    B = auto()

    def get_side_linked_face(self, direction: int):
        """
        Returns the face which is literally placed next to self in the specified direction.
        :param direction: LEFT = 0, UP = 1, RIGHT = 2, DOWN = 3
        :return: The face which is literally placed next to self in the specified direction.
        """
        side_linked_faces = {
            FaceID.F: [FaceID.L, FaceID.U, FaceID.R, FaceID.D],
            FaceID.U: [FaceID.L, FaceID.B, FaceID.R, FaceID.F],
            FaceID.B: [FaceID.L, FaceID.D, FaceID.R, FaceID.U],
            FaceID.L: [FaceID.D, FaceID.B, FaceID.U, FaceID.F],
            FaceID.R: [FaceID.U, FaceID.B, FaceID.D, FaceID.F],
            FaceID.D: [FaceID.R, FaceID.B, FaceID.L, FaceID.F]
        }
        return side_linked_faces[self][direction]

    def opposite(self):
        if self is FaceID.F:
            return FaceID.B
        if self is FaceID.B:
            return FaceID.F

        if self is FaceID.U:
            return FaceID.D
        if self is FaceID.D:
            return FaceID.U

        if self is FaceID.L:
            return FaceID.R
        if self is FaceID.R:
            return FaceID.L

        raise ValueError(f"Unknown FaceID {self!r}.")
