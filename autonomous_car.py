import time

import cv2
import picar
from imutils.video.pivideostream import PiVideoStream

from track_detection import Track_Detection


_DISPLAY_VIDEO = True
_DISPLAY_FPS = True
_RESOLUTION = (320, 240)
_FRAMERATE = 32


class Autonomous_Car():

    def __init__(self):
        picar.setup()

        self.track_driver = Track_Detection()
        self.fw = picar.front_wheels.Front_Wheels(db='config')
        self.bw = picar.back_wheels.Back_Wheels(db='config')

        self.fw.ready()
        self.bw.ready()

        self.fw.turn(90)
        self.bw.speed = 35

        self.fw.turning_max = 45

    def drive(self):

        pre_defined_kwargs = {'vflip': True, 'hflip': True}
        stream = PiVideoStream(resolution=(
            _RESOLUTION), framerate=_FRAMERATE,  **pre_defined_kwargs).start()

        time.sleep(0.5)

        self.bw.forward()

        fps = 0
        then = time.time()
        while True:
            image = stream.read()

            fps += 1
            if _DISPLAY_FPS and (time.time() - then) >= 1:
                print(fps)
                fps = 0
                then = time.time()

            image, output, angle = self.track_driver.drive_track(image)

            self.fw.turn(angle)

            if _DISPLAY_VIDEO:

                image = cv2.resize(image, (640, 480))
                output = cv2.resize(output, (640, 480))

                cv2.imshow("image", image)
                cv2.imshow("output", output)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                stream.stop()
                cv2.destroyAllWindows()
                raise KeyboardInterrupt

    def destroy(self):
        self.bw.stop()
        self.fw.turn(90)


if __name__ == "__main__":
    car = Autonomous_Car()
    try:
        try:
            while True:
                car.drive()
        except Exception as e:
            print(e)
            print('error')
            car.destroy()
    except KeyboardInterrupt:
        car.destroy()
