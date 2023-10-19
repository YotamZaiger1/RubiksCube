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

    def detect_stickers(self, frame, center_x_percentage: float, center_y_percentage: float,
                        face_side_length_percentage: float):

        image_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  # better performance using HSV values as BGR values
        gray_frame = cv2.cvtColor(image_hsv, cv2.COLOR_BGR2GRAY)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        gray_frame = cv2.morphologyEx(gray_frame, cv2.MORPH_OPEN, kernel)
        gray_frame = cv2.morphologyEx(gray_frame, cv2.MORPH_CLOSE, kernel)

        gray_frame = cv2.adaptiveThreshold(gray_frame, 20, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 99,
                                           0)
        contours, hierarchy = cv2.findContours(gray_frame, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)

        colors = []
        relevant_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)

            if area > 700:
                perimeter = cv2.arcLength(contour, True)
                approximated_polygon = cv2.approxPolyDP(contour, perimeter * 0.01, True)
                # hull = cv2.convexHull(contour)

                side_length = perimeter / 4  # squares are expected
                area_diff = side_length ** 2 - area
                if area_diff < 150:
                    x, y, width, height = cv2.boundingRect(contour)

                    color = np.array(cv2.mean(frame[y:y + height, x:x + width])).astype(float)
                    relevant_contours.append(contour)
                    colors.append(WebcamCube.classify_color(color, self.settings.stickers_bgr_values))
                    cv2.drawContours(frame, [contour], 0, (255, 255, 0), 2)
                    cv2.drawContours(frame, [approximated_polygon], 0, (255, 255, 0), 2)

        # relevant_contours = self.select_relevant_contours(relevant_contours)

        return colors

    def select_relevant_contours(self, contours):
        cx_values, cy_values, w_values, h_values = [], [], [], []  # center locations and sizes
        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            cx_values.append(x + width / 2)
            cy_values.append(y + height / 2)
            w_values.append(width)
            h_values.append(height)

        average_side_length = (sum(w_values) + sum(h_values)) / (2 * len(contours))
        average_cx = sum(cx_values) / len(contours)
        average_cy = sum(cy_values) / len(contours)

        relevant_contours = []
        for cx, cy, w, h in zip(cx_values, cy_values, w_values, h_values):
            dx = average_cx - cx
            dy = average_cy - cy

            accepted_distance = self.cube_size * average_side_length
            if abs(dx) > accepted_distance or abs(dy) > accepted_distance:
                continue


        return contours

    @staticmethod
    def draw_grid(frame, grid_size, center_x_percentage: float, center_y_percentage: float,
                  face_side_length_percentage: float, color: tuple[int, int, int], thickness: int):

        start_x, start_y, _, _, sticker_side_length, face_side_length, _, _ = (
            WebcamCube._get_positions_and_sizes(frame, grid_size, center_x_percentage, center_y_percentage,
                                                face_side_length_percentage))

        for i in range(grid_size + 1):
            latitude = start_y + i * sticker_side_length
            longitude = start_x + i * sticker_side_length

            horizontal_start = WebcamCube.int_list([start_x, latitude])
            horizontal_end = WebcamCube.int_list([start_x + face_side_length, latitude])
            vertical_start = WebcamCube.int_list([longitude, start_y])
            vertical_end = WebcamCube.int_list([longitude, start_y + face_side_length])

            cv2.line(frame, horizontal_start, horizontal_end, color, thickness)
            cv2.line(frame, vertical_start, vertical_end, color, thickness)

    @staticmethod
    def int_list(lst: list) -> list[int]:
        return [int(x) for x in lst]

    def detect_face_from_video(self, capture):
        while True:
            frame = WebcamCube.read_capture(capture)

            detected_stickers = self.detect_stickers(frame, *self.settings.detection_grid_position)
            print(detected_stickers)

            # WebcamCube.draw_grid(frame, self.cube_size, *self.settings.detection_grid_position,
            #                      *self.settings.detection_grid_drawing)
            cv2.imshow(self.settings.window_name, frame)
            if self.should_close_window(self.settings.window_name):
                break

    def calibrate_colors(self, capture):
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
