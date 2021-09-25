import Jetson.GPIO as GPIO
import paho.mqtt.client as mqtt
from time import time, sleep
import random
from robud.robud_logging.MQTTHandler import MQTTHandler
import argparse
import logging
from datetime import datetime
import os
import sys
import traceback

random.seed()

LEFT_ENCODER_CHANNEL = 7
RIGHT_ENCODER_CHANNEL = 11
TOPIC_ODOMETRY_LEFT_TICKS = "robud/sensors/odometry/left/ticks"
TOPIC_ODOMETRY_LEFT_TICKSPEED = "robud/sensors/odometry/left/tickspeed"
TOPIC_ODOMETRY_RIGHT_TICKS = "robud/sensors/odometry/right/ticks"
TOPIC_ODOMETRY_RIGHT_TICKSPEED = "robud/sensors/odometry/right/tickspeed"
TICKSPEED_SAMPLE_RATE = 5 #htz 

MQTT_BROKER_ADDRESS = "robud.local"
MQTT_CLIENT_NAME = "odometry.py" + str(random.randint(0,999999999))

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.DEBUG

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/odometry_log_")
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

    logger.info("Starting")

    left_ticks = 0
    right_ticks = 0
    left_tickspeed = 0 #ticks per second
    right_tickspeed = 0 #ticks per second

    def tickDetected(channel):
        global left_ticks
        global right_ticks
        #global tickspeed

        if channel == LEFT_ENCODER_CHANNEL:
            left_ticks+=1
            mqtt_client.publish(TOPIC_ODOMETRY_LEFT_TICKS, payload=left_ticks, qos=2, retain=True)
        elif channel == RIGHT_ENCODER_CHANNEL:
            right_ticks+=1
            mqtt_client.publish(TOPIC_ODOMETRY_RIGHT_TICKS, payload=right_ticks, qos=2, retain=True)

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(LEFT_ENCODER_CHANNEL,GPIO.IN)
    GPIO.setup(RIGHT_ENCODER_CHANNEL,GPIO.IN)

    mqtt_client = mqtt.Client(MQTT_CLIENT_NAME) #create new instance
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start()
    mqtt_client.publish(TOPIC_ODOMETRY_LEFT_TICKS, payload=left_ticks, qos=2, retain=True)
    mqtt_client.publish(TOPIC_ODOMETRY_RIGHT_TICKS, payload=right_ticks, qos=2, retain=True)

    GPIO.add_event_detect(LEFT_ENCODER_CHANNEL, GPIO.BOTH, callback=tickDetected)
    GPIO.add_event_detect(RIGHT_ENCODER_CHANNEL, GPIO.BOTH, callback=tickDetected)

    while True:
        #calculate ticks per second every half second
        start_sample_time = time()
        start_left_ticks = left_ticks
        start_right_ticks = right_ticks
        sleep(1/TICKSPEED_SAMPLE_RATE)
        sample_duration = time() - start_sample_time
        total_left_ticks = left_ticks - start_left_ticks
        total_right_ticks = right_ticks - start_right_ticks
        left_tickspeed = int(total_left_ticks/sample_duration)
        right_tickspeed = int(total_right_ticks/sample_duration)
        mqtt_client.publish(TOPIC_ODOMETRY_LEFT_TICKSPEED, payload=left_tickspeed, qos=0)
        mqtt_client.publish(TOPIC_ODOMETRY_RIGHT_TICKSPEED, payload=right_tickspeed, qos=0)
 

except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
finally:    
    GPIO.cleanup()
    exit(0)



















