import picar
import cv2
from track_detection import Track_Detection


class Autonomous_Car():

    def __init__(self):
        picar.setup()

        forward_speed = 80
        backward_speed = 70
        turning_angle = 40

        max_off_track_count = 40

        delay = 0.0005

        fw = picar.front_wheels.Front_Wheels(db='config')
        bw = picar.back_wheels.Back_Wheels(db='config')

        fw.ready()
        bw.ready()
        fw.turning_max = 45

        self.track_detection = Track_Detection()


if __name__ == "__main__":
    car = Autonomous_Car()
