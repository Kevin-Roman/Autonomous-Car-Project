import time

import cv2
import picar

from track_detection import Track_Detection
from imutils.video.pivideostream import PiVideoStream


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

    # def drive_async(self, angle):
    #     time.sleep(0.5255157470703125)
    #     self.fw.turn(angle)

    def drive(self):
        # camera = PiCamera()
        # camera.resolution = (320, 240)
        # camera.framerate = 32
        # camera.rotation = 180
        # rawCapture = PiRGBArray(camera, size=(320, 240))

        pre_defined_kwargs = {'vflip': True, 'hflip': True}
        stream = PiVideoStream(framerate=32, **pre_defined_kwargs).start()

        time.sleep(0.5)

        self.bw.forward()

        fps = 0
        then = time.time()
        proc = []
        previous = time.time()
        while True:
            if time.time() - previous >= 0:
                image = stream.read()

                fps += 1
                if (time.time() - then) >= 1:
                    print(fps)
                    fps = 0
                    then = time.time()

                image, output, angle = self.track_driver.drive_track(image)
                #start = time.time()
                #p = Process(target=self.drive_async, args=(angle,))
                # p.start()
                # proc.append(p)
                self.fw.turn(angle)
                #print(time.time() - start)
                # 0.5255157470703125

                #image = cv2.resize(image, (640, 480))
                #output = cv2.resize(output, (640, 480))

                #cv2.imshow("image", image)
                #cv2.imshow("output", output)

                previous = time.time()

                key = cv2.waitKey(1) & 0xFF

                # rawCapture.truncate(0)

                if key == ord("q"):
                    for p in proc:
                        p.join()
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
