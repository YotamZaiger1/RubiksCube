from Cube.orientation import Orientation


class Move:
    def __init__(self, orientation: Orientation, index: int, is_forward: bool):
        self.orientation: Orientation = orientation
        self.index: int = index
        self.is_forward: bool = is_forward

    def reversed(self) -> 'Move':
        return Move(self.orientation, self.index, not self.is_forward)

    @staticmethod
    def get_inverted_moves(moves: list['Move']) -> list['Move']:
        """
        Calculates the sequence of moves which inverts the effect of a given moves list.
        :param moves: A list of moves to invert.
        :return: A list of moves that cancel the effect of `moves`.
        """
        return [moves[-i - 1].reversed() for i in range(len(moves))]

    def __eq__(self, other: 'Move') -> bool:
        return (self.orientation is other.orientation and self.index == other.index and
                self.is_forward == other.is_forward)

    def __repr__(self):
        string = f"{self.orientation.name}{self.index}"
        if not self.is_forward:
            string += "b"
        return string
