from time import sleep, time
from adafruit_motorkit import MotorKit
from adafruit_motor import servo
import paho.mqtt.client as mqtt

MOTOR_TIMEOUT = 0.2
MQTT_BROKER_ADDRESS = "localhost"
MQTT_CLIENT_NAME = "robud_motors_motors.py"
TOPIC_MOTOR_LEFT_THROTTLE = 'robud/motors/motor_left/throttle'
TOPIC_MOTOR_RIGHT_THROTTLE = 'robud/motors/motor_right/throttle'
TOPIC_HEAD_SERVO_ANGLE = 'robud/motors/head_servo/angle'
HEAD_SERVO_MAX_ANGLE = 180
HEAD_SERVO_MIN_ANGLE = 0

class RobudMotorWapper(object):
    def __init__(self,motor,motor_name) -> None:
        super().__init__()
        self.motor = motor
        self.timeout_start = 0
        self.name = motor_name
    
    def stopIfTimeout(self):
        if self.timeout_start != 0 and time() - self.timeout_start > MOTOR_TIMEOUT:
            print ("motor timeout:", self.name)
            self.motor.throttle = 0
            self.timeout_start = 0 

def on_message_motor_throttle(client, userdata, message):
    print(message.topic, message.payload)
    robud_motor = None
    if message.topic == TOPIC_MOTOR_LEFT_THROTTLE:
        robud_motor = userdata["motor_left"]
    elif message.topic == TOPIC_MOTOR_RIGHT_THROTTLE:
        robud_motor = userdata["motor_right"]
    else:
        raise ValueError('Invalid Topic: {}'.format(message.topic))
    try:
        #convert message payload to float
        throttle = float(message.payload)
        #make sure throttle is between -1 and 1
        if throttle < -1 or throttle > 1:
            raise ValueError
        #finally set throttle!
        robud_motor.motor.throttle = throttle
        robud_motor.timeout_start = time()
    except ValueError:
        raise ValueError('Invalid Throttle Value: {}'.format(message.payload))
        
def on_message_servo_angle(client, userdata, message):
    print(message.topic, message.payload)
    head_servo = userdata["head_servo"]
    try:
        #convert message payload to int
        angle = int(message.payload)
        if angle < HEAD_SERVO_MIN_ANGLE or angle > HEAD_SERVO_MAX_ANGLE:
            raise ValueError
        head_servo.angle = angle
    except ValueError:
        raise ValueError('Invalid Servo Angle: {}'.format(message.payload))


kit = MotorKit(pwm_frequency = 50) #need frequency of 50hz for servo
pca = kit._pca
head_servo = servo.Servo(pca.channels[15])
motor_right = RobudMotorWapper(kit.motor1, "motor_right")
motor_left = RobudMotorWapper(kit.motor2, "motor_left")
#add anything that needs to be handled by mqtt callbacks to 
#client_userdata, and pass that into the client
client_userdata = {
    "head_servo":head_servo,
    "motor_left":motor_left,
    "motor_right":motor_right
}
mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
mqtt_client.connect(MQTT_BROKER_ADDRESS)
mqtt_client.loop_start()
print('MQTT Client Connected')
mqtt_client.subscribe(TOPIC_MOTOR_LEFT_THROTTLE)
mqtt_client.message_callback_add(TOPIC_MOTOR_LEFT_THROTTLE,on_message_motor_throttle)
print('Subcribed to', TOPIC_MOTOR_LEFT_THROTTLE)
mqtt_client.subscribe(TOPIC_MOTOR_RIGHT_THROTTLE)
mqtt_client.message_callback_add(TOPIC_MOTOR_RIGHT_THROTTLE,on_message_motor_throttle)
print('Subcribed to', TOPIC_MOTOR_RIGHT_THROTTLE)
mqtt_client.subscribe(TOPIC_HEAD_SERVO_ANGLE)
mqtt_client.message_callback_add(TOPIC_HEAD_SERVO_ANGLE,on_message_servo_angle)
print('Subcribed to', TOPIC_HEAD_SERVO_ANGLE)
print('Waiting for messages...')

#main loop:
while True:
    #stop the motors if they haven't received a message for the length of the timeout
    motor_left.stopIfTimeout()
    motor_right.stopIfTimeout()
    sleep(0.01)
