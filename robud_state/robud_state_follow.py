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
from robud.motors.motors_common import TOPIC_HEAD_SERVO_ANGLE, TOPIC_MOTOR_LEFT_THROTTLE, TOPIC_MOTOR_RIGHT_THROTTLE
from robud.robud_voice.robud_voice_common import TOPIC_ROBUD_VOICE_TEXT_INPUT
from robud.sensors.camera_common import CAMERA_HEIGHT, CAMERA_WIDTH
from robud.sensors.tof_common import TOPIC_SENSORS_TOF_RANGE
from robud.ai.wakeword_detection.wakeword_detection_common import TOPIC_WAKEWORD_DETECTED
from robud.robud_state.robud_state_common import TOPIC_ROBUD_STATE, logger

def robud_state_follow(mqtt_client:mqtt.Client, client_userdata:Dict):
    logger.info("Starting ROBUD_STATE_FOLLOW")
    random.seed()

    HEAD_SERVO_MAX_ANGLE = 170
    HEAD_SERVO_MIN_ANGLE = 60
    SCREENHEIGHT = 320
    SCREENWIDTH = 640
    TURN_SPEED = 0.8
    MOTOR_SPEED_BASE = 0.9
    MOTOR_SPEED_ACCELERATED = 0.6
    MOTOR_SPEED_MIN = 0.2
    HEAD_ANGLE_CHANGE = 2
    HEAD_ANGLE_MAX = 180
    HEAD_ANGLE_MIN = 10
    MAX_VEERAGE = 10
    STOP_DISTANCE = 80 #centimeters or less
    BACK_UP_DISTANCE = 40

    CENTER_RANGE_WIDTH = 120

    MQTT_BROKER_ADDRESS = "robud.local"
    MQTT_CLIENT_NAME = "robud_state_follow.py" + str(random.randint(0,999999999))
    HEAD_SERVO_SPEED = 150 #degrees/sec
    PERSON_DETECTION_TIMEOUT = 50 #milliseconds
    PERSON_DETECTION_RANGE = 5000 #millimeters or less
    PERSON_DETECTION_HEIGHT = 0.67 # % of CAMERA_HEIGHT
    PERSON_DETECTION_WIDTH = 0.33 # % of CAMERA_WIDTH



    TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
    TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
    TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
    LOGGING_LEVEL = logging.DEBUG

    #SLEEP_LIGHT_LEVEL = 85
    #WAKE_LIGHT_LEVEL = 105
    MINIMUM_SLEEP = 30 #seconds
    MINIMUM_WAKE = 30 #seconds

    try:
        greetings = [
            "Okay. I'll follow you."
        ]
        
        mqtt_client.publish(TOPIC_ROBUD_VOICE_TEXT_INPUT, greetings[random.randint(0,len(greetings)-1)])
        # send a speech to text request
        
        #wait for text to finish, this should be changed to detect when audio is complete, but we'll just put a 1 second delay here.
        sleep(1)
        
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
        stopped=True
        target_heading = 0

        def move_forward(stopped): #,target_heading):
            left_speed = MOTOR_SPEED_BASE
            right_speed = MOTOR_SPEED_BASE
            # current_heading = int(client_userdata["heading"])
            # if stopped:
            #     target_heading = current_heading
            # elif current_heading != target_heading: 
            #     #veering to the right, add more power to right wheel
            #     veerage = abs(target_heading-current_heading)
            #     max_speed_change = MOTOR_SPEED_ACCELERATED - MOTOR_SPEED_BASE
            #     if veerage > 180: # e.g. 355 & 5
            #         veerage = abs(360-veerage)
            #         current_heading *= -1
            #         target_heading *= -1
            #     if veerage > MAX_VEERAGE:
            #         veerage_pct = 1
            #     else:
            #         veerage_pct = veerage/MAX_VEERAGE

            #     if current_heading > target_heading:              
            #         right_speed = MOTOR_SPEED_BASE + (max_speed_change * veerage_pct)
            #     elif current_heading < target_heading:
            #         #veering to the left, add more power to left wheel
            #         left_speed = MOTOR_SPEED_BASE + (max_speed_change * veerage_pct)
            # print("move forward: target_heading:{}".format(target_heading))
            stopped = False
            mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, left_speed)
            mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, right_speed)
            return stopped #, target_heading

        def move_backward(stopped):
            print("move backward")
            stopped = False
            mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, -1 * MOTOR_SPEED_BASE)
            mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, -1 * MOTOR_SPEED_BASE)
            return stopped
        def turn_right(stopped):
            print("turn right")
            stopped = False
            mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, TURN_SPEED)
            mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, -1 * TURN_SPEED)
            return stopped
        def turn_left(stopped):
            print("turn left")
            stopped = False
            mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, -1 * TURN_SPEED)
            mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, TURN_SPEED)
            return stopped
        def stop(stopped):
            print("stop", target_heading)
            stopped = True
            mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, 0)
            mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, 0)
            return stopped
        def look_up(head_angle):
            print("look up")
            new_angle = head_angle + HEAD_ANGLE_CHANGE
            if new_angle >= HEAD_ANGLE_MAX: 
                new_angle = HEAD_ANGLE_MAX
            head_angle = new_angle
            mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE, head_angle,retain=True)
            return head_angle

        def look_down(head_angle):
            print("look down")
            new_angle = head_angle - HEAD_ANGLE_CHANGE
            if new_angle <= HEAD_ANGLE_MIN:
                new_angle = HEAD_ANGLE_MIN 
            head_angle = new_angle
            mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE, head_angle,retain=True)
            return head_angle

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
        #tof_range = -1
        sleeping = False
        wake_time = monotonic()
        sleep_time = 0
        #start by looking up at 135 degree angle
        gaze_vertical = position_up
        new_head_angle = 150
        gaze_horizontal = position_center
        last_person_detection = 0
        while client_userdata["published_state"] == "ROBUD_STATE_FOLLOW":
            loop_start = monotonic()
            duration = EXPRESSION_CHANGE_DURATION
            head_duration = 0
            tof_range = client_userdata["tof_range"]
            head_angle = client_userdata["head_angle"]
            
            selected_position = (gaze_horizontal,gaze_vertical)
            change_expression = True
            
            if loop_start - last_person_detection > PERSON_DETECTION_TIMEOUT:
                #look for a person to follow
                client_userdata["object_detections"] = None
                mqtt_client.publish(topic=TOPIC_OBJECT_DETECTION_REQUEST,payload=int(True))    
                logger.info("object detection requested")
                logger.info("waiting for object detection response...")
                start_wait = monotonic()
                while (
                    client_userdata["object_detections"] is None
                    and monotonic() - start_wait < 1
                ):
                    sleep(0.01)
                if client_userdata["object_detections"] is None:
                    logger.info("object detection timeout")
                    last_person_detection = monotonic()
                else:
                    logger.info("object detection response receieved")
                
            if client_userdata["object_detections"] is not None:
                for detection in client_userdata["object_detections"]:               
                    if (
                        detection["ClassLabel"] == "person" 
                        ):
                        logging.debug("PERSON DETECTED")
                        
                        # check if person is centered
                        person_horizontal_center = detection["Center"][0]
                        center_range_low = CAMERA_WIDTH/2 - CENTER_RANGE_WIDTH/2
                        center_range_high = CAMERA_WIDTH/2 + CENTER_RANGE_WIDTH/2

                        if person_horizontal_center < center_range_low:
                            #person to left
                            logging.debug("person detected to left")
                            turn_left("stopped")
                        elif person_horizontal_center > center_range_high:
                            #person to right
                            logging.debug("person detected to right")
                            turn_right("stopped")
                        else:
                            #person centered!
                            logging.debug("person centered!")
                            if tof_range > STOP_DISTANCE:
                                move_forward(stopped)
                            elif tof_range < BACK_UP_DISTANCE:
                                move_backward(stopped)



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
        logger.info("Finishing up of ROBUD_STATE_FOLLOW")
        mqtt_client.unsubscribe(TOPIC_OBJECT_DETECTION_DETECTIONS)
        logger.info("Unsubscribed from " + TOPIC_OBJECT_DETECTION_DETECTIONS)
        mqtt_client.unsubscribe(TOPIC_SENSORS_TOF_RANGE)
        logger.info("Unsubscribed from " + TOPIC_SENSORS_TOF_RANGE)
        mqtt_client.unsubscribe(TOPIC_HEAD_SERVO_ANGLE)
        logger.info("Unsubscribed from " + TOPIC_HEAD_SERVO_ANGLE)
        mqtt_client.unsubscribe(TOPIC_WAKEWORD_DETECTED)
        logger.info('Unsubscribed from' + TOPIC_WAKEWORD_DETECTED)
        logger.info("Exiting ROBUD_STATE_FOLLOW")
    except Exception as e:
        logger.critical(str(e) + "\n" + traceback.format_exc())              

if __name__ == "__main__":
    MQTT_BROKER_ADDRESS = "robud.local"
    MQTT_CLIENT_NAME = "robud_state_follow.py" + str(random.randint(0,999999999))
    client_userdata = {}
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME, userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start()
    logger.info('MQTT Client Connected')
    def on_message_robud_state(client, userdata, message):
        userdata["published_state"] = message.payload.decode()
    client_userdata["published_state"] = "ROBUD_STATE_FOLLOW"
    mqtt_client.subscribe(TOPIC_ROBUD_STATE)
    mqtt_client.message_callback_add(TOPIC_ROBUD_STATE,on_message_robud_state)
    logger.info('Subcribed to ' + TOPIC_ROBUD_STATE)
    mqtt_client.publish(topic=TOPIC_ROBUD_STATE, payload = "ROBUD_STATE_FOLLOW", retain=True)
    robud_state_follow(mqtt_client, client_userdata)

