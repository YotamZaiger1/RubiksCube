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

    def should_close_window(self, window_name) -> bool:
        pressed_key = cv2.waitKey(1) & 0xFF
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

    def select_relevant_contours(self, contours_by_layer):
        # combine overlap contours.
        # find 3d-orientation of the face (using close to quadrilateral contours only).
        # deduce face size if it had been placed parallel to the camera view plane.
        # discard contours with unfitting 3d-orientation.
        # sort remaining contours by position in the 2 axis of the face in 3d.

        # go over face-sized slices (don't forget to change size as you get further away from the camera) and select the
        # one contains most contours.

        # discard other contours.
        ################################################################################################################

        s = 0
        calculated_number = 0
        for layer in contours_by_layer:
            for contour in layer:
                rect = cv2.minAreaRect(contour)
                angle = rect[2]
                # if angle - s > 45:
                #     angle = angle - 90
                if angle > 45:
                    angle -= 90
                s += angle
            calculated_number += len(layer)

        if calculated_number == 0:
            return 0
        average_angle = s / calculated_number
        print(average_angle)
        return average_angle

        # if len(contours) == 0:
        #     return contours
        #
        # cx_values, cy_values, w_values, h_values = [], [], [], []  # center locations and sizes
        # for contour in contours:
        #     x, y, width, height = cv2.boundingRect(contour)
        #     cx_values.append(x + width / 2)
        #     cy_values.append(y + height / 2)
        #     w_values.append(width)
        #     h_values.append(height)
        #
        # average_side_length = (sum(w_values) + sum(h_values)) / (2 * len(contours))
        # average_cx = sum(cx_values) / len(contours)
        # average_cy = sum(cy_values) / len(contours)
        #
        # relevant_contours = []
        # for cx, cy, w, h in zip(cx_values, cy_values, w_values, h_values):
        #     dx = average_cx - cx
        #     dy = average_cy - cy
        #
        #     accepted_distance = self.cube_size * average_side_length / 2
        #     if abs(dx) > accepted_distance or abs(dy) > accepted_distance:
        #         continue
        # print(f"{average_side_length = }")
        #
        # return contours

    def estimate_sticker_location(self, rectangles: list, face_a_value, face_b_value, sticker_side_length):
        (pivot_x, pivot_y), (_, _), _ = np.random.choice(rectangles)

        # horizontal and vertical face lines (ax + by + c = 0)
        ah, bh, ch = -face_a_value, face_b_value, -(pivot_x * face_a_value + pivot_y * face_b_value)
        av, bv, cv = -face_b_value, face_a_value, -(pivot_x * face_b_value + pivot_y * face_a_value)

        dxs: list[int] = []
        dys: list[int] = []
        sticker_side_length_squared = sticker_side_length * sticker_side_length
        for rectangle in rectangles:
            (center_x, center_y), (_, _), _ = rectangle

            # distance from the horizontal and vertical face lines:
            rotated_x_squared = WebcamCube._dist_from_point_to_line_squared(center_x, center_y, ah, bh, ch)
            rotated_y_squared = WebcamCube._dist_from_point_to_line_squared(center_x, center_y, av, bv, cv)

            dxs.append((rotated_x_squared - pivot_x) // sticker_side_length_squared)
            dys.append((rotated_y_squared - pivot_y) // sticker_side_length_squared)

        sticker_locations = []

    @staticmethod
    def _dist_from_point_to_line_squared(x, y, a, b, c):
        numerator = a * x + b * y + c
        return numerator * numerator / (a * a + b * b)

    @staticmethod
    def _find_best_beginning(numbers, window_size):
        best_beginning = None
        best_beginning_occurrences = -1

        unique, counts = np.unique(numbers, return_counts=True)
        last_sum = 0
        last_j = 0
        for i, n in enumerate(unique):
            found = last_sum

            j = last_j
            while j < len(unique) and unique[j] - n < window_size:
                found += counts[j]
                j += 1

            if found > best_beginning_occurrences:
                best_beginning_occurrences = found
                best_beginning = n

            last_sum = found - counts[i]
            last_j = j

        return best_beginning

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

            sticker_contours_by_layer = WebcamCube.detect_sticker_contours(frame)
            angle = self.select_relevant_contours(sticker_contours_by_layer)
            x = int(1000 * np.cos(angle * np.pi / 180))
            y = int(1000 * np.sin(angle * np.pi / 180))
            cv2.line(frame, (-x, -y), (x, y), (0, 0, 255), 2)
            x = int(-1000 * np.sin(angle * np.pi / 180))
            y = int(1000 * np.cos(angle * np.pi / 180))
            cv2.line(frame, (frame.shape[0] - x, -y), (x + frame.shape[0], y), (0, 0, 255), 2)

            WebcamCube.draw_contours(frame, sticker_contours_by_layer, (255, 255, 0))
            # print(detected_stickers)

            cv2.imshow(self.settings.window_name, frame)

            if self.should_close_window(self.settings.window_name):
                break

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
        frame = WebcamCube.read_capture(capture)

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
#       remove print statements
