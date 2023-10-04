from cube import Cube
from gui import GUI


def main(*_):
    gui = GUI(Cube(3))
    gui.run()


if __name__ == '__main__':
    main()
