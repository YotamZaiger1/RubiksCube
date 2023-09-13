from enum import Enum, unique, auto


@unique
class Orientation(Enum):
    X = auto()
    Y = auto()
    Z = auto()

    @staticmethod
    def not_recognized_orientation_error_msg(orientation: 'Orientation') -> str:
        return f"The orientation {orientation.name!r} is not recognized."
