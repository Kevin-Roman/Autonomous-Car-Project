import time

import cv2
import picar

from track_detection import Track_Detection
from picamera import PiCamera
from picamera.array import PiRGBArray


class Autonomous_Car():

    def __init__(self):
        picar.setup()

        self.track_driver = Track_Detection()
        self.fw = picar.front_wheels.Front_Wheels(db='config')
        self.bw = picar.back_wheels.Back_Wheels(db='config')

        self.fw.ready()
        self.bw.ready()

        self.fw.turn(90)
        self.bw.speed = 30

        self.fw.turning_max = 45

        self.bw.forward()

    def straight(self):
        self.bw.speed = 20
        self.fw.turn(90)
        self.bw.forward()

    def drive(self):
        camera = PiCamera()
        camera.resolution = (320, 240)
        camera.framerate = 32
        camera.rotation = 180
        rawCapture = PiRGBArray(camera, size=(320, 240))

        time.sleep(0.5)
        new = False
        fps = 0
        then = time.time()
        for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            fps += 1
            if (time.time() - then) >= 1:
                print(fps)
                fps = 0
                then = time.time()

            image = frame.array
            _, _, angle = self.track_driver.drive_track(image)
            self.fw.turn(angle)

            # cv2.imshow("image", image)
            # cv2.imshow("output", output)

            key = cv2.waitKey(1) & 0xFF

            rawCapture.truncate(0)

            if key == ord("q"):
                break

    def destroy(self):
        self.bw.stop()
        self.fw.turn(90)


if __name__ == "__main__":
    car = Autonomous_Car()
    try:
        try:
            while True:
                car.drive()
                # straight_run()
        except Exception as e:
            print(e)
            print('error try again in 5')
            car.destroy()
            time.sleep(5)
    except KeyboardInterrupt:
        car.destroy()
