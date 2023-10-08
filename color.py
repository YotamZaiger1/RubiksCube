from enum import Enum, unique, auto


@unique
class Color(Enum):
    Wh = auto()
    Bl = auto()
    Or = auto()
    Gr = auto()
    Re = auto()
    Ye = auto()

    def __repr__(self):
        return self.name
