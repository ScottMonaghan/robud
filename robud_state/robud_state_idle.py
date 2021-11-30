from numpy.lib.function_base import angle
import paho.mqtt.client as mqtt
from time import sleep, monotonic
import pickle
from robud.robud_face.robud_face_common import *
import random
from robud.robud_logging.MQTTHandler import MQTTHandler
import argparse
import logging
import os
from datetime import datetime
import sys
import traceback
from robud.robud_head.robud_head_common import head_keyframe, TOPIC_HEAD_KEYFRAMES
from robud.ai.object_detection_common import TOPIC_OBJECT_DETECTION_DETECTIONS
from robud.motors.motors_common import TOPIC_HEAD_SERVO_ANGLE
from robud.robud_voice.robud_voice_common import TOPIC_ROBUD_VOICE_TEXT_INPUT
from robud.sensors.camera_common import CAMERA_HEIGHT, CAMERA_WIDTH
from robud.sensors.tof_common import TOPIC_SENSORS_TOF_RANGE
from robud.sensors.light_level_common import TOPIC_SENSORS_LIGHT_LEVEL

random.seed()

HEAD_SERVO_MAX_ANGLE = 170
HEAD_SERVO_MIN_ANGLE = 60
SCREENHEIGHT = 320
SCREENWIDTH = 640
MOTOR_SPEED_BASE = 0.45
MOTOR_SPEED_ACCELERATED = 0.65
MOTOR_SPEED_MIN = 0.2
HEAD_ANGLE_CHANGE = 2
HEAD_ANGLE_MAX = 180
HEAD_ANGLE_MIN = 60
MAX_VEERAGE = 10
MQTT_BROKER_ADDRESS = "robud.local"
MQTT_CLIENT_NAME = "robud_state_idle.py" + str(random.randint(0,999999999))
HEAD_SERVO_SPEED = 150 #degrees/sec
PERSON_DETECTION_TIMEOUT = 5 #seconds
PERSON_DETECTION_RANGE = 80 #centimeters or less
PERSON_DETECTION_HEIGHT = 0.67 # % of CAMERA_HEIGHT


TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.DEBUG

SLEEP_LIGHT_LEVEL = 85
WAKE_LIGHT_LEVEL = 105
MINIMUM_SLEEP = 30 #seconds
MINIMUM_WAKE = 30 #seconds

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/robud_state_idle_log_")
args = parser.parse_args()

#initialize logger
logger=logging.getLogger()
file_path = args.Output + datetime.now().strftime("%Y-%m-%d") + ".txt"
directory = os.path.dirname(file_path)
if not os.path.exists(directory):
    os.makedirs(directory)
log_file = open(file_path, "a")
myHandler = MQTTHandler(hostname=MQTT_BROKER_ADDRESS, topic=TOPIC_ROBUD_LOGGING_LOG_SIGNED, qos=2, log_file=log_file)
myHandler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(filename)s: %(message)s'))
logger.addHandler(myHandler)
logger.level = LOGGING_LEVEL

try:
   #TOPIC_HEAD_SERVO_ANGLE = 'robud/motors/head_servo/angle'

    AVG_GAZE_CHANGE = 5.0 #in seconds
    AVG_EXPRESSION_CHANGE = 15.0 #in seconds

    if __name__ == '__main__':
        rate = 100 #100hz rate for sending messages
        carry_on = True
        client_userdata = {}
        mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME, userdata=client_userdata)
        stopped=True
        object_detections = []
        client_userdata["object_detections"] = object_detections
        recognized_objects = {}
        tof_range = -1
        light_level = 255
        client_userdata["tof_range"] = tof_range
        client_userdata["light_level"] = light_level
        def move_eyes(
            face_expression, 
            left_expression:ExpressionCoordinates, 
            right_expression:ExpressionCoordinates, 
            selected_position:tuple,
            change_expression:bool,
            head_angle:int,
            new_head_angle:int,
            mqtt_client:mqtt.Client,
            duration:float = EXPRESSION_CHANGE_DURATION,
            head_duration:float = None):    
            if (
                change_expression
                or
                face_expression[CENTER_X_OFFSET] != selected_position[0]
                or 
                face_expression[CENTER_Y_OFFSET] != selected_position[1]
                ):
                face_expression[CENTER_X_OFFSET] = selected_position[0]
                face_expression[CENTER_Y_OFFSET] = selected_position[1]
                new_face_keyframe = face_keyframe(
                    left_expression=left_expression,
                    right_expression=right_expression,
                    position=selected_position,
                    duration=duration
                )

                if head_duration == None:
                    #figure out head duration based on HEAD_SERVO_SPEED
                    head_duration = abs(new_head_angle - head_angle) * (1/HEAD_SERVO_SPEED)
                
                new_head_keyframe = head_keyframe(
                    angle = new_head_angle,
                    duration=head_duration
                )

                #add the keyframes to lists
                face_keyframes = [new_face_keyframe]
                head_keyframes = [new_head_keyframe]


                #publish them!
                mqtt_client.publish(TOPIC_FACE_KEYFRAMES,pickle.dumps(face_keyframes),qos=2)
                mqtt_client.publish(TOPIC_HEAD_KEYFRAMES,pickle.dumps(head_keyframes),qos=2)
                change_expression = False
            return face_expression, change_expression, new_head_angle

        def on_message_object_detections(client, userdata, message):
            object_detections = userdata["object_detections"]
            object_detections.clear()
            object_detections.extend(pickle.loads(message.payload))

        def on_message_tof_range(client, userdata, message):
            userdata["tof_range"] = int(message.payload)

        def on_message_light_level(client, userdata, message):
            userdata["light_level"] = int(message.payload)

        mqtt_client.connect(MQTT_BROKER_ADDRESS)
        mqtt_client.loop_start()
        logger.info('MQTT Client Connected')
        mqtt_client.subscribe(TOPIC_OBJECT_DETECTION_DETECTIONS)
        mqtt_client.message_callback_add(TOPIC_OBJECT_DETECTION_DETECTIONS,on_message_object_detections)
        logger.info('Subcribed to ' + TOPIC_OBJECT_DETECTION_DETECTIONS)
        mqtt_client.subscribe(TOPIC_SENSORS_TOF_RANGE)
        mqtt_client.message_callback_add(TOPIC_SENSORS_TOF_RANGE,on_message_tof_range)
        logger.info('Subcribed to ' + TOPIC_SENSORS_TOF_RANGE)
        mqtt_client.subscribe(TOPIC_SENSORS_LIGHT_LEVEL)
        mqtt_client.message_callback_add(TOPIC_SENSORS_LIGHT_LEVEL,on_message_light_level)
        logger.info('Subcribed to ' + TOPIC_SENSORS_LIGHT_LEVEL)
        head_angle = 90
        #mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE, head_angle)
        
        #init face expression
        face_expression = np.zeros(shape=FACE_EXPRESSION_ARRAY_SIZE, dtype=np.int16)
        set_expression(face_expression, Expressions[ExpressionId.OPEN])
        selected_expression = Expressions[ExpressionId.OPEN]
        left_expression:ExpressionCoordinates = Expressions[ExpressionId.OPEN]
        right_expression:ExpressionCoordinates = Expressions[ExpressionId.OPEN]
        position_left = 50
        position_right = -50
        position_center = 0
        position_up = -50
        position_down = 50
        position_sleep = 200
        angle_up = 105
        angle_center = 90
        angle_down = 75
        selected_position = (position_center,position_center)
        change_expression:bool = False
        last_person_detection = 0
        last_dog_detection = 0
        tof_range = -1
        sleeping = False
        wake_time = monotonic()
        sleep_time = 0
        while carry_on:
            loop_start = monotonic()
            duration = EXPRESSION_CHANGE_DURATION
            head_duration = None
            tof_range = client_userdata["tof_range"]
            light_level = client_userdata["light_level"]
            if light_level <= SLEEP_LIGHT_LEVEL and sleeping == False and monotonic()-wake_time > MINIMUM_WAKE:
                    #fall asleep
                    sleeping = True
                    sleep_time = monotonic()
                    new_head_angle = HEAD_ANGLE_MIN
                    gaze_vertical = position_sleep
                    gaze_horizontal = position_center
                    selected_position = (gaze_horizontal,gaze_vertical)
                    left_expression = Expressions[ExpressionId.OVERJOYED]
                    right_expression = Expressions[ExpressionId.OVERJOYED]
                    duration=5
                    head_duration=5
                    change_expression = True
                    mqtt_client.publish(TOPIC_FACE_ENABLE_BLINK, False)
            elif light_level >= WAKE_LIGHT_LEVEL and sleeping == True and monotonic()-sleep_time > MINIMUM_SLEEP:
                    #wake up!
                    sleeping = False
                    wake_time = monotonic()
                    new_head_angle = 90
                    gaze_vertical = position_center
                    gaze_horizontal = position_center
                    selected_position = (gaze_horizontal,gaze_vertical)
                    left_expression = Expressions[ExpressionId.BORED]
                    right_expression = Expressions[ExpressionId.BORED]
                    duration=5
                    head_duration=5
                    change_expression = True
                    mqtt_client.publish(TOPIC_FACE_ENABLE_BLINK, True)
            elif sleeping == False:
                #only run if awake
                #check for recognized objects
                #reference:
                #  detection_out = {
                #         "ClassID":detection.ClassID,
                #         "Confidence":detection.Confidence,
                #         "Left":detection.Left,
                #         "Top":detection.Top,
                #         "Right":detection.Right,
                #         "Bottom":detection.Bottom,
                #         "Width":detection.Width,
                #         "Height":detection.Height,
                #         "Area":detection.Area,
                #         "Center":detection.Center
                #     }
                for detection in object_detections:
                
                    if (
                        detection["ClassLabel"] == "person" 
                        and detection["Height"] > CAMERA_HEIGHT*PERSON_DETECTION_HEIGHT
                        and tof_range > 30
                        and tof_range <= PERSON_DETECTION_RANGE
                        ):
                        if head_angle >=90:
                            if monotonic()-last_person_detection > PERSON_DETECTION_TIMEOUT:
                                #greet the person!
                                #randomize greeting
                                greetings = [
                                    "Hello."
                                    ,"Hi!"
                                    ,"Sup?"
                                    ,"Yo."
                                    ,"Howdy."
                                ]
                                mqtt_client.publish(TOPIC_ROBUD_VOICE_TEXT_INPUT, greetings[random.randint(0,len(greetings)-1)])
                                logging.info("Greeted a person! (Height: " + str(detection["Height"]) + ", Center: " +str(detection["Center"])+ ")")
                                new_head_angle = 130
                                gaze_vertical = position_up
                                gaze_horizontal = position_center
                                selected_position = (gaze_horizontal,gaze_vertical)
                                change_expression = True
                                left_expression = Expressions[ExpressionId.HAPPY]
                                right_expression = Expressions[ExpressionId.HAPPY]
                            last_person_detection = monotonic()
                        else:
                            new_head_angle = 130
                            gaze_vertical = position_up
                            gaze_horizontal = position_center
                            selected_position = (gaze_horizontal,gaze_vertical)
                            change_expression = True
                    elif detection["ClassLabel"] == "dog" and detection["Height"] > CAMERA_HEIGHT*0.25:
                        if monotonic()-last_dog_detection > PERSON_DETECTION_TIMEOUT:
                            #greet the doggie!
                            mqtt_client.publish(TOPIC_ROBUD_VOICE_TEXT_INPUT, "Hello little doggie. woof woof! Good doggie!")
                            logging.info("Greeted a dog! (Height: " + str(detection["Height"]) + ")")
                        last_person_detection = monotonic()
                
                if (
                    monotonic()-last_person_detection > PERSON_DETECTION_TIMEOUT 
                    and monotonic()-last_dog_detection > PERSON_DETECTION_TIMEOUT
                    and change_expression == False
                    ):
                    new_head_angle = head_angle
                    #randomize position
                    chance = random.random()
                    if chance <= (1/(rate*AVG_GAZE_CHANGE)):
                        #print('change gaze')
                        #choose random updown
                        gaze_vertical = position_center
                        new_head_angle = angle_center
                        chance = random.randint(1,3)
                        if chance == 1:
                            gaze_vertical = position_up
                            new_head_angle = random.randint(100,150)
                        elif chance == 2:
                            gaze_vertical = position_down
                            new_head_angle = random.randint(60,80)

                        gaze_horizontal = position_center
                        chance = random.randint(1,3)
                        if chance == 1:
                            gaze_horizontal = position_left
                        elif chance ==2:
                            gaze_horizontal = position_right

                        selected_position = (gaze_horizontal,gaze_vertical)

                    chance = random.random()
                    if chance <= (1/(rate*AVG_EXPRESSION_CHANGE)):
                        #print('change expression')
                        chance = random.randint(1,4)
                        left_expression = Expressions[ExpressionId.OPEN]
                        right_expression = Expressions[ExpressionId.OPEN]
                        if chance == 1:
                            left_expression = Expressions[ExpressionId.HAPPY]
                            right_expression = Expressions[ExpressionId.HAPPY]
                        if chance == 2:
                            left_expression = Expressions[ExpressionId.BORED]
                            right_expression = Expressions[ExpressionId.BORED]
                        if chance == 3:
                            chace = random.randint(1,2)
                            if chance == 1:
                                left_expression = Expressions[ExpressionId.SKEPTICAL_LEFT]
                                right_expression = Expressions[ExpressionId.SKEPTICAL_RIGHT]
                            else:
                                left_expression = Expressions[ExpressionId.SKEPTICAL_RIGHT]
                                right_expression = Expressions[ExpressionId.SKEPTICAL_LEFT]
                        change_expression = True
            face_expression, change_expression, head_angle = move_eyes(
                    face_expression = face_expression,
                    left_expression = left_expression,
                    right_expression = right_expression,
                    selected_position = selected_position,
                    change_expression = change_expression,
                    mqtt_client = mqtt_client,
                    head_angle = head_angle,
                    new_head_angle=new_head_angle,
                    duration=duration,
                    head_duration=head_duration
                    )
            #mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE, head_angle,retain=True)
            loop_time = monotonic() - loop_start
            if loop_time < 1/rate:
                sleep(1/rate - loop_time)
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())              
