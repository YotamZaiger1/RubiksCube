from color import Color
from face import FaceID, Face
from move import Move, X_ROTATION_FACES, Y_ROTATION_FACES, Z_ROTATION_FACES
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
        if move.orientation is Orientation.X:
            effected_faces = X_ROTATION_FACES
        elif move.orientation is Orientation.Y:
            effected_faces = Y_ROTATION_FACES
        elif move.orientation is Orientation.Z:
            effected_faces = Z_ROTATION_FACES
        else:
            raise NotImplemented(Orientation.not_recognized_orientation_error_msg(move.orientation))

        direction_factor = 1 if move.is_forward else -1

        last_strip = self.faces[effected_faces[0]].get_strip(move.orientation, move.index)

        for i in range(len(effected_faces)):
            new_face_id = effected_faces[((i + 1) * direction_factor) % len(effected_faces)]
            new_face = self.faces[new_face_id]

            curr_strip = new_face.get_strip(move.orientation, move.index)
            new_face.set_strip(move.orientation, move.index, last_strip)
            last_strip = curr_strip

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

    def __eq__(self, cube: 'Cube') -> bool:
        return self.faces == cube.faces
