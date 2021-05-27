from time import time
from re import M
from adafruit_motorkit import MotorKit
import rospy
from std_msgs.msg import String
kit = MotorKit()
MOTOR_SPEED = 0.6
MOTOR_TIMEOUT=0.1
last_msg = 0
#rate = 100

def callback(msg):
    global last_msg
    last_msg = time()
    pressed_key=msg.data[0]
    if pressed_key == 'i':
        kit.motor1.throttle = MOTOR_SPEED
        kit.motor2.throttle = MOTOR_SPEED
    if pressed_key == 'k':
        kit.motor1.throttle = -1 * MOTOR_SPEED
        kit.motor2.throttle = -1 * MOTOR_SPEED
    if pressed_key == 'l':
        kit.motor1.throttle = -1 * MOTOR_SPEED
        kit.motor2.throttle = MOTOR_SPEED
    if pressed_key == 'j':
        kit.motor1.throttle = MOTOR_SPEED
        kit.motor2.throttle = -1 * MOTOR_SPEED

def motor_test():
    rospy.init_node('motor_test')
    rospy.Subscriber('keys', String, callback)
    rate = rospy.Rate(100)
    while not rospy.is_shutdown():
        elapsed_time = time() - last_msg
        if elapsed_time > MOTOR_TIMEOUT:
            kit.motor1.throttle = 0
            kit.motor2.throttle = 0
        rate.sleep()


if __name__ == '__main__':
    motor_test()
# kit.motor1.throttle = 0.6
# kit.motor2.throttle = 0.6
# time.sleep(3)
# kit.motor1.throttle = 0
# kit.motor2.throttle = 0