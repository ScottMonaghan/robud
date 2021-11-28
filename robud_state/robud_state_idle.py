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

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.DEBUG

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
    TOPIC_HEAD_SERVO_ANGLE = 'robud/motors/head_servo/angle'

    AVG_GAZE_CHANGE = 5.0 #in seconds
    AVG_EXPRESSION_CHANGE = 15.0 #in seconds

    if __name__ == '__main__':
        rate = 100 #100hz rate for sending messages
        carry_on = True
        client_userdata = {}
        mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME, userdata=client_userdata)
        stopped=True
        
        def move_eyes(
            face_expression, 
            left_expression:ExpressionCoordinates, 
            right_expression:ExpressionCoordinates, 
            selected_position:tuple,
            change_expression:bool,
            mqtt_client:mqtt.Client):    
            if (
                change_expression
                or
                face_expression[CENTER_X_OFFSET] != selected_position[0]
                or 
                face_expression[CENTER_Y_OFFSET] != selected_position[1]
                ):
                face_expression[CENTER_X_OFFSET] = selected_position[0]
                face_expression[CENTER_Y_OFFSET] = selected_position[1]
                keyframe = face_keyframe(
                    left_expression=left_expression,
                    right_expression=right_expression,
                    position=selected_position,
                    duration=EXPRESSION_CHANGE_DURATION
                )
                #add the keyframe to a list
                keyframes = [keyframe]

                #publish it!
                mqtt_client.publish(TOPIC_FACE_KEYFRAMES,pickle.dumps(keyframes),qos=2)
                change_expression = False
            return face_expression, change_expression

        mqtt_client.connect(MQTT_BROKER_ADDRESS)
        mqtt_client.loop_start()
        head_angle = 75
        mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE, head_angle)
        
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
        angle_up = 105
        angle_center = 90
        angle_down = 75
        selected_position = (position_center,position_center)
        change_expression:bool = False

        while carry_on:
            loop_start = monotonic()

            #randomize position
            chance = random.random()
            if chance <= (1/(rate*AVG_GAZE_CHANGE)):
                #print('change gaze')
                #choose random updown
                gaze_vertical = position_center
                head_angle = angle_center
                chance = random.randint(1,3)
                if chance == 1:
                    gaze_vertical = position_up
                    head_angle = angle_up
                elif chance == 2:
                    gaze_vertical = position_down
                    head_angle = angle_down

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
            face_expression, change_expression = move_eyes(
                    face_expression = face_expression,
                    left_expression = left_expression,
                    right_expression = right_expression,
                    selected_position = selected_position,
                    change_expression = change_expression,
                    mqtt_client = mqtt_client
                    )
            mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE, head_angle,retain=True)
            loop_time = monotonic() - loop_start
            if loop_time < 1/rate:
                sleep(1/rate - loop_time)
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())              
