import cv2
import paho.mqtt.client as mqtt
from time import sleep
from io import BytesIO
import numpy as np
from robud.sensors.light_level_common import TOPIC_SENSORS_LIGHT_LEVEL
from robud.sensors.camera_common import TOPIC_CAMERA_RAW, CAMERA_HEIGHT, CAMERA_WIDTH
import random
from robud.robud_logging.MQTTHandler import MQTTHandler
import argparse
import logging
from datetime import datetime
import os
import sys
import traceback

random.seed()

PUBLISH_RATE = 5 #hz

MQTT_BROKER_ADDRESS = "robud.local"
MQTT_CLIENT_NAME = "camera.py" + str(random.randint(0,999999999))

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.DEBUG
MQTT_BROKER_ADDRESS = "robud.local"
MQTT_CLIENT_NAME = "robud_light_level.py" + str(random.randint(0,999999999))
LIGHT_LEVEL_SAMPLE_SIZE = 1000
NUMBER_OF_FRAMES_TO_AVERAGE = 5

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/camera_log_")
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

logger.info("Starting")

def on_message_camera_raw(client, userdata, message):
    payload=message.payload
    np_bytes = np.frombuffer(payload, np.uint8)
    userdata["frame"] = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
        
try:
    client_userdata = {"frame":None}
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME, userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start()
    logger.info('MQTT Client Connected')
    mqtt_client.subscribe(TOPIC_CAMERA_RAW)
    mqtt_client.message_callback_add(TOPIC_CAMERA_RAW,on_message_camera_raw)
    logger.info('Subcribed to ' + TOPIC_CAMERA_RAW)
    while True:
        summed_pixel_values = 0
        for frame_count in range(NUMBER_OF_FRAMES_TO_AVERAGE):
            frame = client_userdata["frame"]
            if frame is not None:
                #convert to grayscale
                grayscale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                #get average light level from random sample size LIGHT_LEVEL_SAMPLE_SIZE
                for i in range(LIGHT_LEVEL_SAMPLE_SIZE-1):
                    summed_pixel_values += grayscale_frame[random.randint(0,CAMERA_HEIGHT-1)][random.randint(0,CAMERA_WIDTH)-1]
                sleep(1/PUBLISH_RATE)
        avg_pixel_value = int(summed_pixel_values/LIGHT_LEVEL_SAMPLE_SIZE/NUMBER_OF_FRAMES_TO_AVERAGE)
        mqtt_client.publish(TOPIC_SENSORS_LIGHT_LEVEL,avg_pixel_value)
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())   