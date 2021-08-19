import time
import cv2
import numpy as np
from numpy.polynomial import Polynomial
from picamera import PiCamera
from picamera.array import PiRGBArray


def detect_lane(image):
    mask, edges = get_edges(image)
    # lines = get_lines(edges)
    output = cv2.bitwise_and(image, image, mask=edges)
    output = get_contours(mask, output)
    image, lines = get_lines(image, edges)
    track_lines = combined_lines(lines, image)
    image = show_track_lines(track_lines, image)

    return image, output


def get_bottom_half(mask):
    height, width = mask.shape

    top = np.zeros((int(height/2), width), dtype=mask.dtype)
    bottom = np.full((int(height/2), width), 255, dtype=mask.dtype)

    filtered = np.concatenate((top, bottom))

    bottom_only = cv2.bitwise_and(mask, mask, mask=filtered)

    return bottom_only


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


def get_lines_obscolete(image, edges):
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 10)
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


def make_line(line, image):
    height, width = image.shape[:2]
    intercept, gradient = line
    y1 = height
    y2 = int(height / 2)
    x1 = int((y1-intercept) / gradient)
    x2 = int((y2-intercept) / gradient)

    return [(x1, y1, x2, y2)]


def combined_lines(lines, image):
    left_lines = []
    right_lines = []

    height, width = image.shape[:2]

    for line in lines:
        for x1, y1, x2, y2 in line:
            if x1 != x2 and y1 != y2:
                polynomial = list(Polynomial.fit(
                    (x1, x2), (y1, y2), 1).convert())

                intercept = polynomial[0]
                gradient = polynomial[1]
                # print(intercept, gradient)

                if gradient < 0:
                    if x1 < (width / 2) and x2 < (width / 2):
                        left_lines.append((intercept, gradient))
                else:
                    if x1 > (width / 2) and x2 > (width / 2):
                        right_lines.append((intercept, gradient))

    left_polynomial = np.average(left_lines, axis=0)
    right_polynomial = np.average(right_lines, axis=0)
    # print(left_polynomial)

    track_lines = [make_line(left_polynomial, image),
                   make_line(right_polynomial, image)]

    # print(left_polynomial, right_polynomial)

    return track_lines


def show_track_lines(lines, image):
    for line in lines:

        for x1, y1, x2, y2 in line:
            cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 5)

    return image


def test_image():
    image = cv2.imread('./image3.jpg')
    image, output = detect_lane(image)
    cv2.imshow("image", image)
    cv2.imshow("output", output)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


def live_video():
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 32
    camera.rotation = 180
    rawCapture = PiRGBArray(camera, size=(640, 480))

    time.sleep(0.5)

    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

        image = frame.array
        image, output = detect_lane(image)

        cv2.imshow("image", image)
        cv2.imshow("output", output)

        key = cv2.waitKey(1) & 0xFF

        rawCapture.truncate(0)

        if key == ord("q"):
            break


live_video()
