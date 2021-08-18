# import the necessary packages
import time
from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import cv2


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


def get_lines(edges):
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 10, np.array([]),
                            minLineLength=10, maxLineGap=5)
    # print(lines[0])

    # for line in lines:
    #     x1, y1, x2, y2 = line[0]
    #     cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

    return lines


def combined_lines(lines, image):
    pass


camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
camera.rotation = 180
rawCapture = PiRGBArray(camera, size=(640, 480))

time.sleep(0.5)


for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

    image = frame.array
    mask, edges = get_edges(image)

    #lines = get_lines(edges)

    output = cv2.bitwise_and(image, image, mask=edges)

    output = get_contours(mask, output)

    lines = get_lines(edges)

    combined_lines(lines, image)

    cv2.imshow("image", image)
    cv2.imshow("output", output)

    key = cv2.waitKey(1) & 0xFF

    rawCapture.truncate(0)

    if key == ord("q"):
        break
