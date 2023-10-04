from face_id import FaceID


class Location:
    def __init__(self, face_id: FaceID, row: int, col: int):
        self.face_id: FaceID = face_id
        self.row: int = row
        self.col: int = col
