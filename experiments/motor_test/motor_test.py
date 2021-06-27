from time import sleep
from re import M
from adafruit_motorkit import MotorKit
from adafruit_motor import servo
kit = MotorKit(pwm_frequency = 50)
pca = kit._pca
MOTOR_SPEED = 0
MOTOR_TIMEOUT=0.1
last_msg = 0
head_servo = servo.Servo(pca.channels[15])
if __name__ == '__main__':
    head_servo.angle=90
    angle_change = 5
    angle = 90
    while True:
    #kit.motor1.throttle = MOTOR_SPEED
        if angle<=1:
            angle_change=1
        elif angle>=179:
            angle_change=-1
        angle += angle_change
        head_servo.angle = angle
        sleep(0.01)
        #pca.channels[15].duty_cycle=0x0000