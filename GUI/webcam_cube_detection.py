import sys
from queue import Queue

import cv2
import numpy as np

from Cube.color import Color


class WebcamCubeSettings:
    def __init__(self, quit_keys: list[int] = None, window_name: str = "Rubik's Cube",
                 detection_grid_position: tuple[float, float, float] = (0.5, 0.5, 0.4),
                 detection_grid_drawing: tuple[tuple[int, int, int], int] = ((0, 0, 0), 2),
                 stickers_bgr_values: dict[Color: tuple[int, int, int]] = None):
        if quit_keys is None:
            quit_keys = [ord("q"), 27]  # 'q' or 'Esc'
        if stickers_bgr_values is None:
            stickers_bgr_values = {
                Color.Wh: (255, 255, 255),
                Color.Bl: (172, 72, 13),
                Color.Or: (37, 85, 255),
                Color.Gr: (76, 155, 25),
                Color.Re: (20, 18, 137),
                Color.Ye: (47, 213, 254)
            }

        self.quit_keys: list[int] = quit_keys
        self.window_name: str = window_name
        self.detection_grid_position: tuple[float, float, float] = detection_grid_position
        self.detection_grid_drawing: tuple[tuple[int, int, int], int] = detection_grid_drawing
        self.stickers_bgr_values: dict[Color: tuple[int, int, int]] = stickers_bgr_values


class WebcamCube:
    def __init__(self, cube_size: int, preview_settings: WebcamCubeSettings = None):
        if preview_settings is None:
            preview_settings = WebcamCubeSettings()

        self.cube_size: int = cube_size
        self.settings: WebcamCubeSettings = preview_settings

    ####################################################################################################################
    @staticmethod
    def read_capture(capture, err_msg="Cant read capture."):
        is_ok, frame = capture.read()
        if not is_ok:
            Exception(err_msg)
        return frame

    def should_close_window(self, window_name, wait_key_delay=1) -> bool:
        pressed_key = cv2.waitKey(wait_key_delay) & 0xFF
        is_closed = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1
        return is_closed or pressed_key in self.settings.quit_keys

    ####################################################################################################################
    @staticmethod
    def _cartesian_dist(point_a, point_b):
        return sum((a - b) ** 2 for a, b in zip(point_a, point_b)) ** 0.5

    @staticmethod
    def classify_color(bgr, options: dict):
        return min(options.items(), key=lambda item: WebcamCube._cartesian_dist(item[1], bgr))[0]

    @staticmethod
    def _get_positions_and_sizes(frame, grid_size, center_x_percentage: float, center_y_percentage: float,
                                 face_side_length_percentage: float):
        height, width = frame.shape[:2]

        face_side_length = min(height, width) * face_side_length_percentage
        sticker_side_length = face_side_length / grid_size

        center_x = width * center_x_percentage
        center_y = height * center_y_percentage

        start_x = center_x - sticker_side_length * grid_size / 2
        start_y = center_y - sticker_side_length * grid_size / 2

        return start_x, start_y, center_x, center_y, sticker_side_length, face_side_length, width, height

    ####################################################################################################################
    @staticmethod
    def detect_sticker_contours(frame):
        # todo: change hard-codded numbers
        filtered_frames = WebcamCube.get_all_filtered_frames(frame)
        stickers_contours_by_layer: list[list] = [[] for _ in range(len(filtered_frames))]

        for i, filtered_frame in enumerate(filtered_frames):
            contours, hierarchy = cv2.findContours(filtered_frame, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)

            for contour in contours:
                area = cv2.contourArea(contour)

                if area > 700:
                    perimeter = cv2.arcLength(contour, True)

                    side_length = perimeter * 0.25  # squares are expected
                    area_diff = side_length * side_length - area
                    if area_diff < 150:
                        stickers_contours_by_layer[i].append(contour)

        return stickers_contours_by_layer

    @staticmethod
    def draw_contours(frame, contours_by_layer, color):
        for layer in contours_by_layer:
            cv2.drawContours(frame, layer, -1, color, 2)

    @staticmethod
    def morph_open_close(frame, kernel=None):
        if kernel is None:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))

        frame = cv2.morphologyEx(frame, cv2.MORPH_OPEN, kernel)
        frame = cv2.morphologyEx(frame, cv2.MORPH_CLOSE, kernel)
        return frame

    @staticmethod
    def hsv_threshold_filter(frame):
        image_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  # better performance using HSV values as BGR values
        gray_frame = cv2.cvtColor(image_hsv, cv2.COLOR_BGR2GRAY)

        gray_frame = WebcamCube.morph_open_close(gray_frame)

        gray_frame = cv2.adaptiveThreshold(gray_frame, 20, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 99,
                                           0)
        return gray_frame

    @staticmethod
    def sharpen_filter(frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.medianBlur(gray, 5)
        sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpen = cv2.filter2D(blur, -1, sharpen_kernel)

        morphed = WebcamCube.morph_open_close(sharpen)

        thresh = cv2.adaptiveThreshold(morphed, 20, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15,
                                       0)
        return thresh

    @staticmethod
    def gaussian_blur_filter(frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (9, 9), 0)
        thresh = cv2.adaptiveThreshold(blur, 255, 1, 1, 11, 2)

        return thresh

    @staticmethod
    def get_all_filtered_frames(frame):
        return [WebcamCube.hsv_threshold_filter(frame), WebcamCube.sharpen_filter(frame),
                WebcamCube.gaussian_blur_filter(frame)]

    ####################################################################################################################

    @staticmethod
    def get_rectangles(contours):
        rectangles = []
        for contour in contours:
            rectangles.append(cv2.minAreaRect(contour))
        return rectangles

    @staticmethod
    def get_center_points(rectangles):
        center_points = []
        for rectangle in rectangles:
            (center_x, center_y), (_, _), _ = rectangle
            center_points.append((center_x, center_y))
        return center_points

    @staticmethod
    def estimate_sticker_side_length(contours):
        total_side_lengths = 0
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            total_side_lengths += perimeter * 0.25
        return total_side_lengths / len(contours)

    @staticmethod
    def estimate_face_slope(rectangles) -> tuple[float, float]:
        total_angle = 0
        for rectangle in rectangles:
            angle = rectangle[2]
            # avoid different sides angle selection problem when the cube is being held near 0 degrees
            if angle > 45:
                angle -= 90
            total_angle += angle

        average_angle = total_angle / len(rectangles)
        # find a and b values of the slope (ax + by = 0)
        if average_angle != 90:
            a, b = -np.tan(np.radians(average_angle)), 1
        else:
            a, b = 1, 0

        return a, b

    @staticmethod
    def combine_overlap_rectangles(rectangles, combine_overlap_percentage: float) -> None:
        """
        Combines rectangles which overlap. The method is in-place.
        :param rectangles: List of rectangles to combine. The original list values may be changed.
        :param combine_overlap_percentage: A value between 0 and 1. Combine two rectangles iff there intersection covers
            at least `combine_overlap_percentage`*(`the area of the smaller rectangle`).
        """
        i = 0
        while i < len(rectangles):
            rect_1 = rectangles[i]
            (center_x1, center_y1), (width_1, height_1), angle_1 = rect_1
            area_1 = width_1 * height_1

            j = i + 1
            while j < len(rectangles):
                rect_2 = rectangles[j]
                intersection_type, intersection_points = cv2.rotatedRectangleIntersection(rect_1, rect_2)
                combined = False

                # check only when the intersection has area
                if intersection_type != cv2.INTERSECT_NONE and len(intersection_points) > 2:
                    order_points = cv2.convexHull(intersection_points, returnPoints=True)
                    intersection_area = cv2.contourArea(order_points)

                    (center_x2, center_y2), (width_2, height_2), angle_2 = rect_2
                    area_2 = width_2 * height_2
                    if intersection_area > combine_overlap_percentage * min(area_1, area_2):
                        rect_1_factor, rect_2_factor = area_1 / (area_1 + area_2), area_2 / (area_1 + area_2)

                        combined_center_x = center_x1 * rect_1_factor + center_x2 * rect_2_factor
                        combined_center_y = center_y1 * rect_1_factor + center_y2 * rect_2_factor
                        combined_width = width_1 * rect_1_factor + width_2 * rect_2_factor
                        combined_height = height_1 * rect_1_factor + height_2 * rect_2_factor
                        combined_angle = angle_1 if angle_1 > angle_2 else angle_2
                        combined_rect = ((combined_center_x, combined_center_y), (combined_width, combined_height),
                                         combined_angle)

                        rectangles[i] = combined_rect
                        rectangles.pop(j)
                        combined = True

                if not combined:
                    j += 1
            i += 1

        return None

    @staticmethod
    def translate_points_to_new_axes(points, pivot: tuple[float, float], horizontal_a, horizontal_b) -> (
            list)[list[float]]:
        """
        Translates the coordinates of a (x, y) points list into a new axes system whose origin is at `pivot` and its
        horizontal axes is parallel to the line `a * x + b * y = 0`.
        :param points: List of (x, y) coordinates to translate.
        :param pivot: The (x, y) values of the new axes system origin.
        :param horizontal_a: The `a` value of the horizontal axes. `a * x + b * y + c = 0`
        :param horizontal_b: The `b` value of the horizontal axes. `a * x + b * y + c = 0`
        :return: A new list contains the translated (x, y) coordinates.
        """
        pivot_x, pivot_y = pivot

        # horizontal and vertical axes lines (ax + by + c = 0) whose origin is (pivot_x, pivot_y)
        # notice the minor differences
        ah, bh, ch = horizontal_a, +horizontal_b, -pivot_y * horizontal_b - pivot_x * horizontal_a
        av, bv, cv = horizontal_b, -horizontal_a, +pivot_y * horizontal_a - pivot_x * horizontal_b

        positions = []
        for point in points:
            x, y = point

            # distance from the horizontal and vertical axes:
            rotated_x = WebcamCube.signed_dist_from_point_to_line(x, y, av, bv, cv)
            rotated_y = WebcamCube.signed_dist_from_point_to_line(x, y, ah, bh, ch)
            positions.append([rotated_x, rotated_y])

        return positions

    @staticmethod
    def signed_dist_from_point_to_line(x, y, a, b, c):
        """
        Calculates the signed distance between the point (`x`, `y`) and the line `a` * x + `b` * y + `c` = 0. The
        returned value is not always positive. Use `abs()` on the returned value to get normal unsigned distance.
        Notice: Inverting the sign of `a`, `b` and `c` will invert the sign of the returned value but won't affect its
        absolute value.
        :param x: The point x value.
        :param y: The point y value.
        :param a: The line a value.
        :param b: The line b value.
        :param c: The line c value.
        :return: The signed distance between the point (`x`, `y`) and the line `a` * x + `b` * y + `c` = 0.
        """
        return (a * x + b * y + c) / (a * a + b * b) ** 0.5

    @staticmethod
    def normalize_points(points, scale_by: float) -> list[list[float]]:
        """
        Moves a list of (x,y) points so that the smallest x and y values would be 0. Then scales the points x-y
        coordinates by `scale_by`.
        :param points: A list of (x, y) points to normalize.
        :param scale_by: A factor to scale the coordinates by.
        :return: A list contains the new moved and scaled (x, y) coordinates of `points`.
        """
        min_x, min_y = min(points, key=lambda p: p[0])[0], min(points, key=lambda p: p[1])[1]

        normalized = []
        for point in points:
            x, y = point
            normalized.append([(x - min_x) * scale_by, (y - min_y) * scale_by])
        return normalized

    def estimate_sticker_locations(self, normalized_positions) -> list[tuple[int, int]]:
        """
        Estimate in-face locations of a given points list. Uses a stable marriage solution as an approximation for the
        best sticker-location mapping.
        :param normalized_positions: A list of normalized (x, y) points. See: `WebcamCube.normalize_points()`.
            Each point represent the detected center of a sticker in a face.
        :return: A list whose i-th element is the estimated (col, row) of the i-th point in the face.
        """
        # build proposer and non-proposer preferences for the stable marriage algorithm:
        options = [(col, row) for col in range(self.cube_size) for row in range(self.cube_size)]

        distances_from_options = [[-1] * len(options) for _ in range(len(normalized_positions))]
        distances_from_points = [[-1] * len(normalized_positions) for _ in range(len(options))]

        for i, (x, y) in enumerate(normalized_positions):
            for j, (option_x, option_y) in enumerate(options):
                dist = (x - option_x) ** 2 + (y - option_y) ** 2
                distances_from_options[i][j] = dist
                distances_from_points[j][i] = dist

        proposer_preferences = []
        non_proposer_ranking = [[-1] * len(normalized_positions) for _ in range(len(options))]

        for i, distances in enumerate(distances_from_options):
            distances = [list(x) for x in enumerate(distances)]
            distances.sort(key=lambda v: v[1])
            proposer_preferences.append([v[0] for v in distances])

        for j, distances in enumerate(distances_from_points):
            distances = [list(x) for x in enumerate(distances)]
            distances.sort(key=lambda v: v[1])
            for rank, v in enumerate(distances):
                non_proposer_ranking[j][v[0]] = rank

        stable_match = WebcamCube.stable_marriage(proposer_preferences, non_proposer_ranking)
        locations = []
        for non_proposer_index in stable_match:
            locations.append(options[non_proposer_index])

        return locations

    @staticmethod
    def stable_marriage(proposers_preferences: list[list[int]], non_proposers_rankings: list[list[int]]) -> list[int]:
        """
        Finds a solution to the Stable Marriage Problem using the Gale-Shapley algorithm.
        :param proposers_preferences: A list with the proposer preference lists. The i-th element is a list contains the
            preferences of the i-th proposer. In a proposer preferences list, the i-th element is the index of i-th
            prioritized non-proposer.
        :param non_proposers_rankings: A list with the non-proposer ranking lists. The i-th element is a list contains
            the ranking of the i-th non-proposer. *Unlike in a proposer preferences list*, In a non-proposer ranking
            list, the i-th element is the rank of the i-th proposer for the non-proposer. The most desired proposer of
            the non-proposer gets rank 0, and the most undesired proposer gets the largest rank.

        Notice: There might be more non-proposers than proposers. The other way around is not supported.

        :return: The stable match that was found. The i-th element is the index of non-proposer matched with the
            i-th proposer.
        """
        n, m = len(proposers_preferences), len(non_proposers_rankings)
        if n > m:
            raise ValueError(f"More proposers ({n}) than non-proposers ({m})")

        unmatched_proposer_ids = Queue(n)
        for proposer_id in range(n):
            unmatched_proposer_ids.put(proposer_id)

        # The i-th element is the number of times that the i-th proposer has been turned down so far
        proposer_turned_down_counters = [0] * n

        # The i-th element is the index of current non-proposer match of the i-th proposer
        stable_match = [-1] * n

        # The i-th element is the index of current proposer match of the i-th non-proposer
        stable_match_inverted = [-1] * m

        while unmatched_proposer_ids.qsize() > 0:
            proposer_id = unmatched_proposer_ids.get()
            turned_down_times = proposer_turned_down_counters[proposer_id]
            propose_to_id = proposers_preferences[proposer_id][turned_down_times]

            is_non_proposer_available = stable_match_inverted[propose_to_id] == -1
            if is_non_proposer_available:
                stable_match[proposer_id] = propose_to_id
                stable_match_inverted[propose_to_id] = proposer_id

            else:
                non_proposer_pref = non_proposers_rankings[propose_to_id]
                proposer_place = non_proposer_pref[proposer_id]
                curr_match_proposer_id = stable_match_inverted[propose_to_id]
                curr_match_proposes_place = non_proposer_pref[curr_match_proposer_id]

                if proposer_place < curr_match_proposes_place:
                    proposer_turned_down_counters[curr_match_proposer_id] += 1
                    unmatched_proposer_ids.put(curr_match_proposer_id)

                    stable_match[proposer_id] = propose_to_id
                    stable_match_inverted[propose_to_id] = proposer_id

                else:
                    proposer_turned_down_counters[proposer_id] += 1
                    unmatched_proposer_ids.put(proposer_id)

        return stable_match

    ####################################################################################################################

    @staticmethod
    def draw_grid(frame, grid_size, center_x_percentage: float, center_y_percentage: float,
                  face_side_length_percentage: float, color: tuple[int, int, int], thickness: int):

        start_x, start_y, _, _, sticker_side_length, face_side_length, _, _ = (
            WebcamCube._get_positions_and_sizes(frame, grid_size, center_x_percentage, center_y_percentage,
                                                face_side_length_percentage))

        for i in range(grid_size + 1):
            latitude = start_y + i * sticker_side_length
            longitude = start_x + i * sticker_side_length

            horizontal_start = np.int_([start_x, latitude])
            horizontal_end = np.int_([start_x + face_side_length, latitude])
            vertical_start = np.int_([longitude, start_y])
            vertical_end = np.int_([longitude, start_y + face_side_length])

            cv2.line(frame, horizontal_start, horizontal_end, color, thickness)
            cv2.line(frame, vertical_start, vertical_end, color, thickness)

    def detect_face_from_video(self, capture):
        while True:
            frame = WebcamCube.read_capture(capture)
            height, width = frame.shape[:2]

            sticker_contours_by_layer = WebcamCube.detect_sticker_contours(frame)

            detected_face_colors = [[None for _ in range(self.cube_size)] for _ in range(self.cube_size)]

            contours = sticker_contours_by_layer[0]
            for layer in sticker_contours_by_layer:
                contours.extend(layer)
            if len(contours) > 0:
                rectangles = WebcamCube.get_rectangles(contours)
                sticker_side_length = WebcamCube.estimate_sticker_side_length(contours)
                face_a_value, face_b_value = WebcamCube.estimate_face_slope(rectangles)

                WebcamCube.combine_overlap_rectangles(rectangles, 0.5)
                for rect in rectangles:  # todo change
                    cv2.drawContours(frame, [np.int_(cv2.boxPoints(rect))], 0, (255, 255, 255), 2)

                points = WebcamCube.get_center_points(rectangles)
                # pivot does not matter because of the normalization
                points = WebcamCube.translate_points_to_new_axes(points, (0, 0), face_a_value, face_b_value)
                points = WebcamCube.normalize_points(points, 1 / sticker_side_length)

                if len(points) > self.cube_size ** 2:
                    print(
                        f"Too many stickers detected ({len(points)}), maximum for {self.cube_size}x{self.cube_size} "
                        f"cube is {self.cube_size ** 2}.", file=sys.stderr)
                    points = points[:self.cube_size ** 2]

                estimated_sticker_locations = self.estimate_sticker_locations(points)

                for i, (col, row) in enumerate(estimated_sticker_locations):
                    mask = np.zeros((height, width), np.uint8)
                    cv2.drawContours(mask, contours, i, (255, 255, 255), 1)
                    found_color = cv2.mean(frame, mask=mask)
                    color = WebcamCube.classify_color(found_color, self.settings.stickers_bgr_values)
                    if row < self.cube_size and col < self.cube_size:
                        detected_face_colors[row][col] = color
                        pass
                    else:
                        print(f"{row= }, {col= }")
                        pass

            detected_face_bgr_frame = np.zeros((height, width, 3), np.uint8)
            self.draw_face(detected_face_bgr_frame, detected_face_colors)
            cv2.imshow("Detected Face", detected_face_bgr_frame)

            cv2.imshow(self.settings.window_name, frame)

            if self.should_close_window(self.settings.window_name):
                break

    def draw_face(self, frame, colors):
        frame[:, :] = (20, 20, 20)  # background  todo: make an option in self.settings

        start_x, start_y, _, _, sticker_side_length, face_side_length, _, _ = (
            WebcamCube._get_positions_and_sizes(frame, self.cube_size, *self.settings.detection_grid_position))

        for i, row in enumerate(colors):
            for j, color in enumerate(row):
                if color is not None:
                    up, left = start_y + i * sticker_side_length, start_x + j * sticker_side_length
                    down, right = up + sticker_side_length, left + sticker_side_length
                    up, down, left, right = np.int_([up, down, left, right])
                    frame[up:down, left:right] = self.settings.stickers_bgr_values[color]

        WebcamCube.draw_grid(frame, self.cube_size, *self.settings.detection_grid_position,
                             *self.settings.detection_grid_drawing)

    def calibrate_colors(self, capture):
        # todo: replace with kmeans classification
        last_color = None
        while True:
            frame = WebcamCube.read_capture(capture)

            center_x_per, center_y_per, size_per = self.settings.detection_grid_position
            size_per *= 1.5 / self.cube_size
            WebcamCube.draw_grid(frame, 1, center_x_per, center_y_per, size_per, *self.settings.detection_grid_drawing)

            cv2.putText(frame, "Put a sticker in the square and press", (20, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 0, 0), 2)
            cv2.putText(frame, "[Etr] to print its bgr value.", (20, 80), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 0, 0), 2)

            pressed_key = cv2.waitKey(1) & 0xFF
            if pressed_key == 13:  # Etr
                start_x, start_y, _, _, _, face_side_length, _, _ = (
                    WebcamCube._get_positions_and_sizes(frame, 1, center_x_per, center_y_per, size_per))

                color = np.array(cv2.mean(frame[int(start_y):int(start_y + face_side_length),
                                          int(start_x):int(start_x + face_side_length)])).astype(float)[:3]
                print(f"Detected BGR color: ({color[0]}, {color[1]}, {color[2]})")
                last_color = color

            if last_color is not None:
                start_x, start_y, _, _, _, face_side_length, _, _ = (
                    WebcamCube._get_positions_and_sizes(frame, 1, 0.8, 0.5, size_per))

                frame[int(start_y):int(start_y + face_side_length), int(start_x):int(start_x + face_side_length)] = (
                    last_color)

            cv2.imshow(self.settings.window_name, frame)
            if self.should_close_window(self.settings.window_name):
                break

    def video_cube(self):
        capture = cv2.VideoCapture(0)
        # frame = WebcamCube.read_capture(capture)

        # while True:
        #     frame = read_capture(capture)
        #
        #     cv2.imshow(WIN_NAME, frame)
        #
        #     if should_close_window(WIN_NAME):
        #         break

        self.detect_face_from_video(capture)
        # self.calibrate_colors(capture)

        cv2.destroyAllWindows()


if __name__ == '__main__':
    webcamCubeSettings = WebcamCubeSettings()
    webcamCubeSettings.stickers_bgr_values = {
        Color.Wh: (152.25954861111111, 147.97829861111111, 142.76529947916666),
        Color.Bl: (109.84320746527777, 78.23795572916666, 74.52430555555556),
        Color.Or: (69.83637152777777, 119.13541666666666, 174.04600694444443),
        Color.Gr: (94.57855902777777, 126.7829861111111, 42.42784288194444),
        Color.Re: (58.295138888888886, 48.853732638888886, 127.45073784722221),
        Color.Ye: (96.79915364583333, 175.49652777777777, 146.28125),
    }
    webcamCube = WebcamCube(5, webcamCubeSettings)
    webcamCube.video_cube()

# todo: check for static method calls which still use self.
#       remove unnecessary print statements
#       delete unused methods
# find 3d-orientation of the face.
# deduce face size if it had been placed parallel to the camera view plane.
# combine overlap contours.
# discard contours with unfitting 3d-orientation.
# sort remaining contours by position in the 2 axis of the face in 3d.

# go over face-sized slices (don't forget to change size as you get further away from the camera) and select the
# one contains most contours.

# discard other contours.
