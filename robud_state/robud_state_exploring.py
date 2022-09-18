from typing import Dict
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
from robud.ai.object_detection_common import TOPIC_OBJECT_DETECTION_DETECTIONS, TOPIC_OBJECT_DETECTION_REQUEST
from robud.motors.motors_common import TOPIC_HEAD_SERVO_ANGLE
from robud.robud_voice.robud_voice_common import TOPIC_ROBUD_VOICE_TEXT_INPUT
from robud.sensors.camera_common import CAMERA_HEIGHT, CAMERA_WIDTH
from robud.sensors.tof_common import TOPIC_SENSORS_TOF_RANGE
from robud.sensors.light_level_common import TOPIC_SENSORS_LIGHT_LEVEL
from robud.ai.wakeword_detection.wakeword_detection_common import TOPIC_WAKEWORD_DETECTED
from robud.robud_state.robud_state_common import TOPIC_ROBUD_STATE, logger


#same random facial expressions as idle
#also move around and avoid obstacles 
def robud_state_exploring(mqtt_client:mqtt.Client, client_userdata:Dict):
    logger.info("Starting ROBUD_STATE_EXPLORING")
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
    #MQTT_BROKER_ADDRESS = "robud.local"
    #MQTT_CLIENT_NAME = "robud_state_exploring.py" + str(random.randint(0,999999999))
    HEAD_SERVO_SPEED = 150 #degrees/sec

    try:

        AVG_GAZE_CHANGE = 5.0 #in seconds
        AVG_EXPRESSION_CHANGE = 15.0 #in seconds

        rate = 100 #100hz rate for sending messages
        carry_on = True
        stopped=True
        object_detections = []
        client_userdata["object_detections"] = object_detections
        recognized_objects = {}
        tof_range = -1

        head_angle = None
        client_userdata["tof_range"] = tof_range
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
            userdata["object_detections"] = pickle.loads(message.payload)

        def on_message_tof_range(client, userdata, message):
            userdata["tof_range"] = int(message.payload)


        def on_message_head_angle(client, userdata, message):
            userdata["head_angle"] = int(message.payload)

        def on_message_wakeword_detected(client:mqtt.Client, userdata,message):
             client.publish(TOPIC_ROBUD_STATE, "ROBUD_STATE_WAKEWORD_DETECTED")

        # mqtt_client.connect(MQTT_BROKER_ADDRESS)
        # mqtt_client.loop_start()
        # logger.info('MQTT Client Connected')
        mqtt_client.subscribe(TOPIC_OBJECT_DETECTION_DETECTIONS)
        mqtt_client.message_callback_add(TOPIC_OBJECT_DETECTION_DETECTIONS,on_message_object_detections)
        logger.info('Subcribed to ' + TOPIC_OBJECT_DETECTION_DETECTIONS)
        mqtt_client.subscribe(TOPIC_SENSORS_TOF_RANGE)
        mqtt_client.message_callback_add(TOPIC_SENSORS_TOF_RANGE,on_message_tof_range)
        logger.info('Subcribed to ' + TOPIC_SENSORS_TOF_RANGE)
        mqtt_client.subscribe(TOPIC_HEAD_SERVO_ANGLE)
        mqtt_client.message_callback_add(TOPIC_HEAD_SERVO_ANGLE,on_message_head_angle)
        logger.info('Subcribed to ' + TOPIC_HEAD_SERVO_ANGLE)
        mqtt_client.subscribe(TOPIC_WAKEWORD_DETECTED)
        mqtt_client.message_callback_add(TOPIC_WAKEWORD_DETECTED,on_message_wakeword_detected)
        logger.info('Subcribed to ' + TOPIC_WAKEWORD_DETECTED)

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
        while client_userdata["published_state"] == "ROBUD_STATE_EXPLORING":
            loop_start = monotonic()
            duration = EXPRESSION_CHANGE_DURATION
            head_duration = None
            tof_range = client_userdata["tof_range"]
            head_angle = client_userdata["head_angle"]
            
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
            loop_time = monotonic() - loop_start
            if loop_time < 1/rate:
                sleep(1/rate - loop_time)
        #transition out of state & clean up
        logger.info("State change detected:" + client_userdata["published_state"])
        #unsubscribe from all 
        logger.info("Finishing up of ROBUD_STATE_EXPLORING")
        mqtt_client.unsubscribe(TOPIC_OBJECT_DETECTION_DETECTIONS)
        logger.info("Unsubscribed from " + TOPIC_OBJECT_DETECTION_DETECTIONS)
        mqtt_client.unsubscribe(TOPIC_SENSORS_TOF_RANGE)
        logger.info("Unsubscribed from " + TOPIC_OBJECT_DETECTION_DETECTIONS)
        mqtt_client.unsubscribe(TOPIC_HEAD_SERVO_ANGLE)
        logger.info("Unsubscribed from " + TOPIC_HEAD_SERVO_ANGLE)
        mqtt_client.unsubscribe(TOPIC_WAKEWORD_DETECTED)
        logger.info('Unsubscribed from' + TOPIC_WAKEWORD_DETECTED)
        logger.info("Exiting ROBUD_STATE_EXPLORING")
    except Exception as e:
        logger.critical(str(e) + "\n" + traceback.format_exc())              

if __name__ == "__main__":
    MQTT_BROKER_ADDRESS = "robud.local"
    MQTT_CLIENT_NAME = "robud_state_exploring.py" + str(random.randint(0,999999999))
    client_userdata = {}
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME, userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start()
    logger.info('MQTT Client Connected')
    def on_message_robud_state(client, userdata, message):
        userdata["published_state"] = message.payload.decode()
    client_userdata["published_state"] = "ROBUD_STATE_EXPLORING"
    mqtt_client.subscribe(TOPIC_ROBUD_STATE)
    mqtt_client.message_callback_add(TOPIC_ROBUD_STATE,on_message_robud_state)
    logger.info('Subcribed to ' + TOPIC_ROBUD_STATE)
    mqtt_client.publish(topic=TOPIC_ROBUD_STATE, payload = "ROBUD_STATE_EXPLORING", retain=True)
    robud_state_exploring(mqtt_client, client_userdata)

