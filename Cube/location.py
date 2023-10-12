from Cube.face_id import FaceID


class Location:
    def __init__(self, face_id: FaceID, row: int, col: int):
        self.face_id: FaceID = face_id
        self.row: int = row
        self.col: int = col

    def __eq__(self, location: 'Location') -> bool:
        return self.face_id is location.face_id and self.row == location.row and self.col == location.col

    def __repr__(self):
        return f"{self.face_id.name}({self.row}, {self.col})"
