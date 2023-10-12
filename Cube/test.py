from cube import Cube
from solver_3x3 import Solver3x3


def average_moves_to_solve(run_times=100, shuffle_moves_number=100):
    s = 0
    for _ in range(run_times):
        cube = Cube(3)
        shuffle_moves = cube.generate_shuffle_moves(shuffle_moves_number)
        cube.execute_moves(shuffle_moves)

        solver = Solver3x3(cube)
        can_solve, moves = solver.solve()
        s += len(moves)
    return s / run_times


if __name__ == '__main__':
    print(average_moves_to_solve(1000, 1000))
