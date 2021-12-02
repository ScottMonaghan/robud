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
from robud.robud_state.robud_state_common import TOPIC_ROBUD_STATE, logger

def test_func():
    print("Test Func!")

def robud_state_idle():
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
    PERSON_DETECTION_WIDTH = 0.33 # % of CAMERA_WIDTH


    TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
    TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
    TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
    LOGGING_LEVEL = logging.DEBUG

    SLEEP_LIGHT_LEVEL = 85
    WAKE_LIGHT_LEVEL = 105
    MINIMUM_SLEEP = 30 #seconds
    MINIMUM_WAKE = 30 #seconds

    # #parse arguments
    # parser = argparse.ArgumentParser()
    # parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/robud_state_idle_log_")
    # args = parser.parse_args()

    # #initialize logger
    # logger=logging.getLogger()
    # file_path = args.Output + datetime.now().strftime("%Y-%m-%d") + ".txt"
    # directory = os.path.dirname(file_path)
    # if not os.path.exists(directory):
    #     os.makedirs(directory)
    # log_file = open(file_path, "a")
    # myHandler = MQTTHandler(hostname=MQTT_BROKER_ADDRESS, topic=TOPIC_ROBUD_LOGGING_LOG_SIGNED, qos=2, log_file=log_file)
    # myHandler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(filename)s: %(message)s'))
    # logger.addHandler(myHandler)
    # logger.level = LOGGING_LEVEL

    try:
    #TOPIC_HEAD_SERVO_ANGLE = 'robud/motors/head_servo/angle'

        AVG_GAZE_CHANGE = 5.0 #in seconds
        AVG_EXPRESSION_CHANGE = 15.0 #in seconds

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
        head_angle = None
        client_userdata["tof_range"] = tof_range
        client_userdata["light_level"] = light_level
        client_userdata["head_angle"] = head_angle
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

        def on_message_head_angle(client, userdata, message):
            userdata["head_angle"] = int(message.payload)

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
        mqtt_client.subscribe(TOPIC_HEAD_SERVO_ANGLE)
        mqtt_client.message_callback_add(TOPIC_HEAD_SERVO_ANGLE,on_message_head_angle)
        logger.info('Subcribed to ' + TOPIC_HEAD_SERVO_ANGLE)

        def on_message_robud_state(client, userdata, message):
            userdata["published_state"] = message.payload.decode()
        client_userdata["published_state"] = "ROBUD_STATE_IDLE"
        mqtt_client.subscribe(TOPIC_ROBUD_STATE)
        mqtt_client.message_callback_add(TOPIC_ROBUD_STATE,on_message_robud_state)
        logger.info('Subcribed to ' + TOPIC_ROBUD_STATE)
        mqtt_client.publish(topic=TOPIC_ROBUD_STATE, payload = "ROBUD_STATE_IDLE", retain=True)


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
        position_sleep = 100
        angle_center = 90
        selected_position = (position_center,position_center)
        change_expression:bool = False
        last_dog_detection = 0
        tof_range = -1
        sleeping = False
        wake_time = monotonic()
        sleep_time = 0
        while client_userdata["published_state"] == "ROBUD_STATE_IDLE":
            loop_start = monotonic()
            duration = EXPRESSION_CHANGE_DURATION
            head_duration = None
            tof_range = client_userdata["tof_range"]
            light_level = client_userdata["light_level"]
            head_angle = client_userdata["head_angle"]
            if head_angle == None:
                head_angle = 90

            if light_level <= SLEEP_LIGHT_LEVEL and sleeping == False and monotonic()-wake_time > MINIMUM_WAKE:
                    #fall asleep
                    sleeping = True
                    sleep_time = monotonic()
                    new_head_angle = HEAD_ANGLE_MIN
                    gaze_vertical = position_sleep
                    gaze_horizontal = position_center
                    selected_position = (gaze_horizontal,gaze_vertical)
                    left_expression = Expressions[ExpressionId.BLINKING]
                    right_expression = Expressions[ExpressionId.BLINKING]
                    duration=4
                    head_duration=4
                    change_expression = True
                    mqtt_client.publish(TOPIC_FACE_ENABLE_BLINK, int(False))
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
                    duration=4
                    head_duration=4
                    change_expression = True
                    mqtt_client.publish(TOPIC_FACE_ENABLE_BLINK, int(True))
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
                        and detection["Width"] > CAMERA_WIDTH*PERSON_DETECTION_WIDTH
                        and tof_range > 30
                        and tof_range <= PERSON_DETECTION_RANGE
                        ):
                        logging.info("PERSON DETECTED, changing to ROBUD_STATE_PERSON_INTERACTION")
                        mqtt_client.publish(topic=TOPIC_ROBUD_STATE, payload="ROBUD_STATE_PERSON_INTERACTION", retain=True)
                        client_userdata["published_state"] = "ROBUD_STATE_PERSON_INTERACTION"
                    elif detection["ClassLabel"] == "dog" and detection["Height"] > CAMERA_HEIGHT*0.25:
                        if monotonic()-last_dog_detection > PERSON_DETECTION_TIMEOUT:
                            #greet the doggie!
                            mqtt_client.publish(TOPIC_ROBUD_VOICE_TEXT_INPUT, "Hello little doggie. woof woof! Good doggie!")
                            logging.info("Greeted a dog! (Height: " + str(detection["Height"]) + ")")
                        last_person_detection = monotonic()
                
                if (
                    client_userdata["published_state"]=="ROBUD_STATE_IDLE"
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
            face_expression, change_expression, new_head_angle = move_eyes(
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

if __name__ == "__main__":
    robud_state_idle()

