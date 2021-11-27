import pytweening
from time import time, sleep
from robud.robud_face.robud_face_common import *
import paho.mqtt.client as mqtt
import numpy as np
import pickle
import random
from robud.robud_logging.MQTTHandler import MQTTHandler
import argparse
import logging
from datetime import datetime
import os
import sys
import traceback

random.seed()

MQTT_BROKER_ADDRESS = "localhost"
MQTT_CLIENT_NAME = "robud_face_animator.py" + str(random.randint(0,999999999))

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL= logging.DEBUG

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/robud_face_animator_log_")
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
    def on_message_face_keyframes(client,userdata,message):
        #get the master keyframes list  used by the animation controller, passed in through userdata
        keyframes:list = userdata["keyframes"]
        #add received decoded pickle keyframes onto the end of the master keyframes object
        keyframes.extend(pickle.loads(message.payload))
        
    def robud_face_animator():
        #initialize a master keyframes list for the animation controller
        keyframes:list = []
        
        #initialize a face expression array we'll use to keep track of the current state of the face
        face_expression = np.zeros(shape=FACE_EXPRESSION_ARRAY_SIZE, dtype=np.int16)
        #initilize the face expression to the default open expression
        set_expression(face_expression, Expressions[ExpressionId.OPEN])
        #default head servro to 90 degrees
        #face_expression[HEAD_SERVO_ANGLE] = 90

        #initialize mqtt client
        client_userdata = {
            "keyframes":keyframes,
        }
        mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
        mqtt_client.connect(MQTT_BROKER_ADDRESS)
        mqtt_client.loop_start()
        logger.info('MQTT Client Connected')
        mqtt_client.subscribe(TOPIC_FACE_KEYFRAMES)
        mqtt_client.message_callback_add(TOPIC_FACE_KEYFRAMES,on_message_face_keyframes)
        logger.info('Subcribed to ' + TOPIC_FACE_KEYFRAMES)


        while True:
            while len(keyframes) > 0:
                #if there are any keyframes in the list, remove the first item in the list
                keyframe:face_keyframe = keyframes.pop(0)
                #run the animation based on the keyframe
                face_expression = run_animation(
                    mqtt_client=mqtt_client,
                    current_face_expression=face_expression,
                    new_left_expression=keyframe.left_expression,
                    new_right_expression=keyframe.right_expression,
                    new_position=keyframe.position,
                    duration=keyframe.duration,
                    #new_head_servo_angle=keyframe.head_servo_angle
                    )
            sleep(0.01)   
    if __name__ == '__main__':
        robud_face_animator()
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
