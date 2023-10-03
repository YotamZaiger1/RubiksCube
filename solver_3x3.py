from color import Color
from cube import Cube
from face_id import FaceID


class Solver3x3:
    def __init__(self, cube_3x3: Cube):
        if cube_3x3.size != 3:
            raise Exception(f"Given cube size is {cube_3x3.size} instead of 3.")
        self.cube: Cube = cube_3x3

        self.faces_colors: dict[FaceID, Color] = dict()
        for face_id in FaceID:
            self.faces_colors[face_id] = self.cube.faces[face_id][1][1]

        self.color_faces: dict[Color: FaceID] = dict()
        for face_id in FaceID:
            self.color_faces[self.faces_colors[face_id]] = face_id

    def find_sticker(self, colors: list[Color]) -> list[list[FaceID, int, int]]:
        """
        Finds the locations of the sticker with the given colors.
        :param colors: List of colors of the sticker.
        :return: List of locations [face id, row, col] of the specified sticker. The i-th element of the returned value
        is the location of the i-th color in `colors`. If the sticker wasn't found, raises a `ValueError`.
        """
        colors_set = set(colors)

        for face_id in FaceID:
            face = self.cube.faces[face_id]

            for i in range(self.cube.size):
                for j in range(self.cube.size):
                    other_locations: list[list[FaceID, int, int]] = (
                        self.cube.find_other_sticker_locations(face_id, i, j))

                    found_colors: set[Color] = {self.cube.faces[found_face_id][x][y]
                                                for found_face_id, x, y in other_locations}
                    found_colors.add(face[i][j])  # add current color

                    if found_colors == colors_set:  # sticker found
                        locations = other_locations + [[face_id, i, j]]  # add current location

                        # sort by the order of colors in 'colors'
                        def sort_by(location):
                            f, row, col = location
                            return colors.index(self.cube.faces[f][row][col])

                        return sorted(locations, key=sort_by)
        raise ValueError("The specified sticker was not found.")

    def solve_3x3(self) -> bool:
        self.solve_cross()
        self.solve_u_color()
        self.solve_second_x_strip()

        can_solve_d_cross = self.solve_d_cross()
        if not can_solve_d_cross:
            return False
        can_solve_d_corner_positions = self.solve_d_corner_positions()
        if not can_solve_d_corner_positions:
            return False

        self.solve_d_corners()
        return True

    def solve_cross(self):
        pass

    def solve_u_color(self):
        pass

    def solve_second_x_strip(self):
        pass

    def solve_d_cross(self) -> bool:
        return True

    def solve_d_corner_positions(self) -> bool:
        return True

    def solve_d_corners(self):
        pass
