from robud.robud_face.robud_face_common import *
from robud.robud_head.robud_head_common import TOPIC_HEAD_KEYFRAMES, head_keyframe
import argparse
import logging
import pickle
import random
from datetime import datetime
import os
from robud.robud_logging.MQTTHandler import MQTTHandler

TOPIC_ROBUD_STATE = 'robud/robud_state'
HEAD_SERVO_SPEED = 150 #degrees/sec
PERSON_DETECTION_TIMEOUT = 5 #seconds
PERSON_DETECTION_RANGE = 80 #centimeters or less
PERSON_DETECTION_HEIGHT = 0.67 # % of CAMERA_HEIGHT
PERSON_DETECTION_WIDTH = 0.33 # % of CAMERA_WIDTH
MQTT_BROKER_ADDRESS = "robud.local"

SLEEP_LIGHT_LEVEL = 85
WAKE_LIGHT_LEVEL = 105
MINIMUM_SLEEP = 30 #seconds
MINIMUM_WAKE = 30 #seconds
SLEEP_ANIMATION_DURATION = 4
WAKE_ANIMATION_DURATION = 4
VERTICAL_POSITION_SLEEP = 100 
POSITION_CENTER = 0


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

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + "robud_state" + str(random.randint(0,999999999))
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"

LOGGING_LEVEL = logging.DEBUG

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/robud_state_person_interaction_log_")
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