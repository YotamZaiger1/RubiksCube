from enum import Enum, unique, auto

from Cube.face_id import FaceID

X_ROTATION_FACES: list[FaceID] = [FaceID.F, FaceID.R, FaceID.B, FaceID.L]
Y_ROTATION_FACES: list[FaceID] = [FaceID.F, FaceID.U, FaceID.B, FaceID.D]
Z_ROTATION_FACES: list[FaceID] = [FaceID.R, FaceID.U, FaceID.L, FaceID.D]


@unique
class Orientation(Enum):
    X = auto()
    Y = auto()
    Z = auto()

    @staticmethod
    def not_recognized_orientation_error_msg(orientation: 'Orientation') -> str:
        return f"The orientation {orientation.name!r} is not recognized."

    @staticmethod
    def get_orientation_rotation_faces_ids(orientation: 'Orientation') -> list[FaceID]:
        if orientation is Orientation.X:
            return X_ROTATION_FACES
        if orientation is Orientation.Y:
            return Y_ROTATION_FACES
        if orientation is Orientation.Z:
            return Z_ROTATION_FACES
        raise ValueError(Orientation.not_recognized_orientation_error_msg(orientation))

    @staticmethod
    def find_needed_single_move_orientation(from_face_id: FaceID, to_face_id: FaceID) -> tuple['Orientation', bool]:
        """
        Finds the needed move orientation and direction to go from `from_face_id` to `to_face_id`.
        :param from_face_id: Starting face id.
        :param to_face_id: Ending face id.
        :return: The needed move orientation and direction to go from `from_face_id` to `to_face_id`.
        :raise ValueError: If `from_face_id` and `to_face_id` are opposites faces.
        """
        if from_face_id.opposite() is to_face_id:
            raise ValueError("No single move between opposite faces.")

        for i, rotation in enumerate((X_ROTATION_FACES, Y_ROTATION_FACES, Z_ROTATION_FACES)):
            if from_face_id in rotation and to_face_id in rotation:
                from_index = rotation.index(from_face_id)
                to_index = rotation.index(to_face_id)

                difference = (to_index - from_index) % len(rotation)
                is_forward = difference == 1

                return [Orientation.X, Orientation.Y, Orientation.Z][i], is_forward
