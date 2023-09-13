from face import FaceID
from orientation import Orientation

X_ROTATION_FACES: list[FaceID] = [FaceID.F, FaceID.R, FaceID.B, FaceID.L]
Y_ROTATION_FACES: list[FaceID] = [FaceID.F, FaceID.U, FaceID.B, FaceID.D]
Z_ROTATION_FACES: list[FaceID] = [FaceID.R, FaceID.U, FaceID.L, FaceID.D]


class Move:
    def __init__(self, orientation: Orientation, index: int, is_forward: bool):
        self.orientation: Orientation = orientation
        self.index: int = index
        self.is_forward: bool = is_forward
