import time

import cv2
import numpy as np
import picar
import tflite_runtime.interpreter as tflite
from imutils.video.pivideostream import PiVideoStream

from track_detection import Track_Detection

_RECORD = False
_DISPLAY_VIDEO = False
_DISPLAY_FPS = True
_RESOLUTION = (320, 240)
_FRAMERATE = 32
_SPEED = 35


class Autonomous_Car():

    def __init__(self):
        picar.setup()

        self.track_driver = Track_Detection()
        self.fw = picar.front_wheels.Front_Wheels(db='config')
        self.bw = picar.back_wheels.Back_Wheels(db='config')

        self.fw.ready()
        self.bw.ready()

        self.fw.turn(90)
        self.bw.speed = _SPEED

        self.fw.turning_max = 45

    def drive_cv2(self):
        if _RECORD:
            with open('video_number.txt') as file:
                _VIDEO_NUMBER = file.read()
                file.write(_VIDEO_NUMBER + 1)

        pre_defined_kwargs = {'vflip': True, 'hflip': True}
        stream = PiVideoStream(resolution=(
            _RESOLUTION), framerate=_FRAMERATE,  **pre_defined_kwargs).start()

        time.sleep(1)

        self.bw.forward()

        fps = 0
        then = time.time()
        counter = 0
        while True:
            original_image = stream.read()

            fps += 1
            if _DISPLAY_FPS and (time.time() - then) >= 1:
                print(fps)
                fps = 0
                then = time.time()

            image = original_image.copy()
            image, output, angle = self.track_driver.drive_track(
                image)

            self.fw.turn(angle)

            if _RECORD:
                cv2.imwrite(
                    f'./images/video_{_VIDEO_NUMBER}_{counter}_{angle}.jpg', original_image[int(original_image.shape[0]/2):, :, :])

            if _DISPLAY_VIDEO:

                image = cv2.resize(image, (640, 480))
                output = cv2.resize(output, (640, 480))

                cv2.imshow("image", image)
                cv2.imshow("output", output)

            counter += 1

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                stream.stop()
                cv2.destroyAllWindows()
                raise KeyboardInterrupt

    def drive_deep_learning(self):
        interpreter = tflite.Interpreter(
            model_path='./models/model_04_09_21.tflite')
        interpreter.allocate_tensors()
        #model = load_model('./models/model.h5')

        pre_defined_kwargs = {'vflip': True, 'hflip': True}
        stream = PiVideoStream(resolution=(
            _RESOLUTION), framerate=_FRAMERATE,  **pre_defined_kwargs).start()

        time.sleep(1)

        # self.bw.forward()

        fps = 0
        then = time.time()

        while True:
            original_image = stream.read()

            fps += 1
            if _DISPLAY_FPS and (time.time() - then) >= 1:
                print(f'fps: {fps}')
                fps = 0
                then = time.time()

            image = original_image.copy()
            input_index = interpreter.get_input_details()[0]["index"]
            output_index = interpreter.get_output_details()[0]["index"]

            input_data = np.asarray(
                [process_image(original_image)]).astype('float32')
            # print(input_data.shape)
            ##input_data = process_image(original_image).astype('float32')
            # print(input_data.shape)
            interpreter.set_tensor(input_index, input_data)
            interpreter.invoke()

            angle = int(interpreter.get_tensor(output_index))

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


def process_image(image):
    height = image.shape[0]
    image = image[int(height/2):, :, :]
    image = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    image = cv2.resize(image, (200, 66))
    #image = image/255
    return image


if __name__ == "__main__":
    car = Autonomous_Car()
    try:
        try:
            while True:
                car.drive_deep_learning()
        except Exception as e:
            print(e)
            print('error')
            car.destroy()
    except KeyboardInterrupt:
        car.destroy()
