TOP_DOWN, BOTTOM_UP, LEFT_RIGHT, RIGHT_LEFT = range(4)


class IndexTranslator:
    def __init__(self, translate_type: int, index: int, size: int):
        self.translate_type: int = translate_type
        self.index: int = index
        self.size: int = size

        if translate_type == TOP_DOWN:
            self.translate = self._top_down_strip_index_translator
            self.inverse = IndexTranslator._inverse_top_down_strip_index_translator
            self.opposite = self._bottom_up_strip_index_translator

        elif translate_type == BOTTOM_UP:
            self.translate = self._bottom_up_strip_index_translator
            self.inverse = self._inverse_bottom_up_strip_index_translator
            self.opposite = self._top_down_strip_index_translator

        elif translate_type == LEFT_RIGHT:
            self.translate = self._left_right_strip_index_translator
            self.inverse = IndexTranslator._inverse_left_right_strip_index_translator
            self.opposite = self._right_left_strip_index_translator

        elif translate_type == RIGHT_LEFT:
            self.translate = self._right_left_strip_index_translator
            self.inverse = self._inverse_right_left_strip_index_translator
            self.opposite = self._left_right_strip_index_translator

        else:
            raise ValueError(f"translation type {translate_type!r} is not allowed.")

    def _top_down_strip_index_translator(self, i: int):
        return i, self.index

    @staticmethod
    def _inverse_top_down_strip_index_translator(coordinate: tuple[int, int]):
        x, y = coordinate
        return x

    def _bottom_up_strip_index_translator(self, i: int):
        return (-i - 1) % self.size, self.index

    def _inverse_bottom_up_strip_index_translator(self, coordinate: tuple[int, int]):
        x, y = coordinate
        return (-x - 1) % self.size

    def _left_right_strip_index_translator(self, i: int):
        return self.index, i

    @staticmethod
    def _inverse_left_right_strip_index_translator(coordinate: tuple[int, int]):
        x, y = coordinate
        return y

    def _right_left_strip_index_translator(self, i: int):
        return self.index, (-i - 1) % self.size

    def _inverse_right_left_strip_index_translator(self, coordinate: tuple[int, int]):
        x, y = coordinate
        return (-y - 1) % self.size
