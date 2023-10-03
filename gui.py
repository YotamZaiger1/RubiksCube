import pygame as pg

from color import Color
from cube import Cube
from face_id import FaceID
from move import Move
from orientation import Orientation

BACKGROUND_COLOR = (5, 5, 5, 255)
NO_COLOR = (0, 0, 0, 0)


class GUI:
    def __init__(self, cube: Cube, sticker_size: int = 30, sticker_extra_size: int = 3, face_extra_size: int = 7,
                 screen_extra_size: int = 50):
        self.cube: Cube = cube

        self.sticker_size: int = sticker_size
        self.sticker_extra_size: int = sticker_extra_size
        self.full_sticker_size: int = sticker_size + sticker_extra_size

        self.face_size = cube.size * sticker_size + (cube.size + 1) * sticker_extra_size
        self.face_extra_size: int = face_extra_size
        self.full_face_size = self.face_size + face_extra_size

        self.screen_extra_size: int = screen_extra_size
        self.screen_size = (
            4 * self.full_face_size + face_extra_size + screen_extra_size * 2,
            3 * self.full_face_size + face_extra_size + screen_extra_size * 2)

    def run(self):
        pg.init()
        pg.display.set_caption(f"{self.cube.size}x{self.cube.size} Rubik's Cube")

        screen = pg.display.set_mode(self.screen_size)
        background = screen.convert_alpha()
        foreground = screen.convert_alpha()
        overlay = screen.convert_alpha()

        background.fill(BACKGROUND_COLOR)

        done = False
        while not done:
            overlay.fill(NO_COLOR)
            foreground.fill(NO_COLOR)

            self._draw_cube(foreground)

            mouse_pos = pg.mouse.get_pos()
            hovered_face_id, hovered_row, hovered_col = self._find_hovered_sticker(mouse_pos)
            selected_move = None
            if hovered_face_id is not None:
                selected_move = self._get_selected_move(hovered_face_id, hovered_row, hovered_col,
                                                        pg.key.get_mods() & pg.KMOD_SHIFT,
                                                        pg.key.get_mods() & pg.KMOD_CTRL)
                self._draw_sticker(overlay, hovered_face_id, hovered_row, hovered_col, (0, 0, 0, 100))

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    done = True

                if event.type == pg.MOUSEBUTTONDOWN:
                    if selected_move is not None:
                        self.cube.move(selected_move)

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        done = True

            GUI._update_screen(screen, background, foreground, overlay)

    def _draw_sticker(self, surface, face_id: FaceID, row: int, col: int, color_rgba):
        starting_x, starting_y = self._get_face_starting_pixel(face_id)

        pg.draw.rect(surface, color_rgba, (starting_x + self.sticker_extra_size + self.full_sticker_size * col,
                                           starting_y + self.sticker_extra_size + self.full_sticker_size * row,
                                           self.sticker_size, self.sticker_size))

    def _draw_cube(self, surface):
        faces = self.cube.faces

        for face_id in faces:
            for row in range(self.cube.size):
                for col in range(self.cube.size):
                    color = GUI._get_color(faces[face_id][row][col])
                    self._draw_sticker(surface, face_id, row, col, color)

    @staticmethod
    def _update_screen(screen, background, foreground, overlay):
        screen.blit(background, (0, 0))
        screen.blit(foreground, (0, 0))
        screen.blit(overlay, (0, 0))
        pg.display.flip()

    ####################################################################################################################

    def _get_face_starting_pixel(self, face_id):
        row = -1
        col = -1

        if face_id == FaceID.L:
            row = 1
            col = 0
        elif face_id == FaceID.U:
            row = 1
            col = 1
        elif face_id == FaceID.R:
            row = 1
            col = 2
        elif face_id == FaceID.D:
            row = 1
            col = 3

        elif face_id == FaceID.F:
            row = 2
            col = 1
        elif face_id == FaceID.B:
            row = 0
            col = 1

        x = self.screen_extra_size + self.face_extra_size + col * self.full_face_size
        y = self.screen_extra_size + self.face_extra_size + row * self.full_face_size
        return x, y

    @staticmethod
    def _get_color(color):
        if color is Color.Wh:
            return 251, 248, 253, 255
        if color is Color.Bl:
            return 0, 110, 235, 255
        if color is Color.Or:
            return 254, 127, 38, 255
        if color is Color.Gr:
            return 63, 165, 69, 255
        if color is Color.Re:
            return 212, 0, 27, 255
        return 253, 250, 23, 255  # yellow

    def _find_hovered_sticker(self, mouse_pos):
        x, y = mouse_pos
        beginning_size = self.screen_extra_size + self.face_extra_size
        x -= beginning_size
        y -= beginning_size

        face_col = x // self.full_face_size
        face_row = y // self.full_face_size

        face_pos = (face_row, face_col)
        if face_pos == (0, 1):
            face_id = FaceID.B
        elif face_pos == (1, 0):
            face_id = FaceID.L
        elif face_pos == (1, 1):
            face_id = FaceID.U
        elif face_pos == (1, 2):
            face_id = FaceID.R
        elif face_pos == (1, 3):
            face_id = FaceID.D
        elif face_pos == (2, 1):
            face_id = FaceID.F
        else:
            return None, None, None

        x -= face_col * self.full_face_size + self.sticker_extra_size
        y -= face_row * self.full_face_size + self.sticker_extra_size

        col, x_rem = divmod(x, self.full_sticker_size)
        row, y_rem = divmod(y, self.full_sticker_size)

        if col >= self.cube.size or row >= self.cube.size or x_rem >= self.sticker_size or y_rem >= self.sticker_size:
            return None, None, None

        return face_id, row, col

    ####################################################################################################################
    def _get_selected_move(self, face_id, row, col, is_shift_down, is_ctrl_down):
        is_forward = not is_ctrl_down

        if face_id is FaceID.F or face_id is FaceID.B:
            orientation = Orientation.Y if is_shift_down else Orientation.X
        elif face_id is FaceID.R or face_id is FaceID.L:
            orientation = Orientation.X if is_shift_down else Orientation.Z
        elif face_id is FaceID.U or face_id is FaceID.D:
            orientation = Orientation.Y if is_shift_down else Orientation.Z
        else:
            raise ValueError(f"Unknown FaceID {face_id!r}.")

        index = self.cube.faces[face_id].find_move_index_from_real_indices(orientation, row, col)

        return Move(orientation, index, is_forward)