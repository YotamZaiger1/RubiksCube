from orientation import Orientation


class Move:
    def __init__(self, orientation: Orientation, index: int, is_forward: bool):
        self.orientation: Orientation = orientation
        self.index: int = index
        self.is_forward: bool = is_forward

    def reversed(self) -> 'Move':
        return Move(self.orientation, self.index, not self.is_forward)

    def __repr__(self):
        string = f"{self.orientation.name}{self.index}"
        if not self.is_forward:
            string += "b"
        return string
