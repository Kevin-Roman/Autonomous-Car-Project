import time

import cv2
import numpy as np
from imutils.video.pivideostream import PiVideoStream



class Track_Detection():
    def __init__(self):
        self.current_angle = 90

    def drive_track(self, image):
        image, output, angle = detect_track(image, self.current_angle)
        # print(angle)

        # check for 135 and 45
        if angle > 135:
            self.current_angle = 135
        elif angle < 45:
            self.current_angle = 45
        else:
            self.current_angle = angle

        return image, output, angle


def detect_track(image, current_angle):
    _, edges = get_edges(image)
    # lines = get_lines_old(edges)
    output = cv2.bitwise_and(image, image, mask=edges)
    # output = get_contours(mask, output)
    image, lines = get_lines(image, edges)
    track_lines = combined_lines(lines, image)

    if len(track_lines) > 0:
        image = show_track_lines(track_lines, image)

    main_line, next_angle = steering_line(track_lines, image)
    image = show_track_lines([[main_line]], image)
    # print(current_angle, next_angle)
    next_angle = clean_angle(current_angle, next_angle)
    # print(next_angle, "\n")
    return image, output, next_angle


def get_edges(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_bound = np.array([90, 98, 112])
    upper_bound = np.array([110, 255, 255])

    mask = cv2.inRange(hsv, lower_bound, upper_bound)

    mask = get_bottom_half(mask)

    edges = cv2.Canny(mask, 200, 400)

    return mask, edges


def get_contours(mask, output):
    kernel = np.ones((5, 5), np.uint8)
    dilation = cv2.dilate(mask, kernel, iterations=2)

    contours = cv2.findContours(
        dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    contours = contours[0] if len(contours) == 2 else contours[1]

    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:2]:
        cv2.drawContours(output, [contour], -1, (36, 255, 12), 1)

    return output


def get_bottom_half(mask):
    height, width = mask.shape

    top = np.zeros((int(height/2), width), dtype=mask.dtype)
    bottom = np.full((int(height/2), width), 255, dtype=mask.dtype)

    filtered = np.concatenate((top, bottom))

    bottom_only = cv2.bitwise_and(mask, mask, mask=filtered)

    return bottom_only


# Obscolete
def get_lines_old(image, edges):
    lines = cv2.HoughLines(edges, 1, np.pi/180, 10)
    # print(lines[0])

    for line in lines[:4]:
        # print(line[0])
        rho, theta = line[0]
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        x1 = int(x0 + 1000*(-b))
        y1 = int(y0 + 1000*(a))
        x2 = int(x0 - 1000*(-b))
        y2 = int(y0 - 1000*(a))
        cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 2)

    return lines, image


def get_lines(image, edges):
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 10, np.array([]),
                            minLineLength=10, maxLineGap=5)
    # print(lines[0])

    for line in lines:
        x1, y1, x2, y2 = line[0]
        # print(x1, y1, x2, y2)
        cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

    return image, lines


def combined_lines(lines, image):
    left_lines = []
    right_lines = []

    _, width = image.shape[:2]

    for line in lines:
        for x1, y1, x2, y2 in line:
            if x1 != x2 and y1 != y2:
                # polynomial = list(Polynomial.fit(
                #     (x1, x2), (y1, y2), 1).convert())

                polynomial = np.polyfit((x1, x2), (y1, y2), 1)

                intercept = polynomial[1]
                gradient = polynomial[0]
                # print(intercept, gradient)

                if gradient < 0:
                    if x1 < (width / 2) and x2 < (width / 2):
                        left_lines.append((intercept, gradient))
                else:
                    if x1 > (width / 2) and x2 > (width / 2):
                        right_lines.append((intercept, gradient))

    track_lines = []

    if len(left_lines) > 0:
        left_polynomial = np.average(left_lines, axis=0)
        left_line = make_line(left_polynomial, image)
        track_lines.append(left_line)
   

    if len(right_lines) > 0:
        right_polynomial = np.average(right_lines, axis=0)
        right_line = make_line(right_polynomial, image)
        track_lines.append(right_line)
    # print(left_polynomial)

    # print(left_polynomial, right_polynomial)

    return track_lines


def make_line(line, image):
    height, _ = image.shape[:2]
    intercept, gradient = line
    y1 = height
    y2 = int(height / 2)
    x1 = int((y1-intercept) / gradient)
    x2 = int((y2-intercept) / gradient)
    # Reminder: Unnecessary to include y1 and y2, or use them and dont inlcude them in steering_line()
    return [(x1, y1, x2, y2)]


def steering_line(lines, image):
    height, width = image.shape[:2]

    if len(lines) == 1:
        x1 = lines[0][0][0]
        x2 = lines[0][0][2]
        x = int((x2 - x1)/2)

        x1 = int(width/2)
        x2 = int(x1 + x)
        y1 = height
        y2 = int(height / 2)

    else:
        x2_left = lines[0][0][2]
        x2_right = lines[1][0][2]

        x1 = int(width/2)
        x2 = int((x2_left + x2_right) / 2)
        y1 = height
        y2 = int(height / 2)

        # print(lines)
        bottom_center = int(width/2)
        x = x2 - bottom_center

    y = int(height / 2)
    # print(x, y)
    if x != 0:
        toa = np.arctan(y/x)
        theta_radian = (np.pi/2 - abs(toa)) * \
            np.sign(toa)

        theta_degree = int(theta_radian * (180/np.pi))
    else:
        theta_degree = 0

    angle = theta_degree + 90

    # print(theta_radian, theta_degree, angle)

    main_line = (x1, y1, x2, y2)

    return main_line, angle


def clean_angle(current_angle, next_angle):
    # print(current_angle, next_angle)
    if abs(next_angle - current_angle) >= 10:

        cleaned_angle = int(
            current_angle + np.sign(next_angle - current_angle) * 10)
        return cleaned_angle
    # print(current_angle, next_angle)

    return next_angle


def show_track_lines(lines, image):
    for line in lines:

        for x1, y1, x2, y2 in line:
            cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 5)

    return image


def test_image():
    image = cv2.imread('./image3.jpg')

    track_driver = Track_Detection()
    image, output = track_driver.drive_track(image)
    cv2.imshow("image", image)
    cv2.imshow("output", output)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


def live_video(track_driver):
    # camera = PiCamera()
    # camera.resolution = (640, 480)
    # camera.framerate = 32
    # camera.rotation = 180
    # rawCapture = PiRGBArray(camera, size=(640, 480))

    time.sleep(0.5)
    pre_defined_kwargs = {'vflip': True, 'hflip': True}
    stream = PiVideoStream(resolution=((640, 480)), **
                           pre_defined_kwargs).start()

    time.sleep(2)
    fps = 0
    then = time.time()
    while True:
        frame = stream.read()

        fps += 1
        if (time.time() - then) >= 1:
            print(fps)
            fps = 0
            then = time.time()

        image = frame

        # image, output, angle = track_driver.drive_track(image)

        # self.fw.turn(angle)

        cv2.imshow("image", image)
        # cv2.imshow("output", output)

        key = cv2.waitKey(1) & 0xFF

        # rawCapture.truncate(0)

        if key == ord("q"):
            stream.stop()
            cv2.destroyAllWindows()
            break


if __name__ == "__main__":
    track_driver = Track_Detection()

    live_video(track_driver)
