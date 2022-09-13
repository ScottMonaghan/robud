import paho.mqtt.client as mqtt
from robud.robud_logging.MQTTHandler import MQTTHandler
import argparse
import logging
import random
from datetime import datetime
import os
import sys
import robud_stick_config
import robud_stick_common
import board
import adafruit_pcf8591.pcf8591 as PCF
from adafruit_pcf8591.analog_in import AnalogIn
from time import sleep
import traceback
from robud.motors.motors_common import TOPIC_MOTOR_LEFT_THROTTLE, TOPIC_MOTOR_RIGHT_THROTTLE

random.seed()

MQTT_BROKER_ADDRESS = "robud.local"
MQTT_CLIENT_NAME = "robud_stick.py" + str(random.randint(0,999999999))

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.INFO

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/robud_stick_log_")
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

STICK_MAX = 65280
STICK_MIN = 0
STICK_IDLE_MAX = 34000
STICK_IDLE_MIN = 32000
TURN_SPEED = 0.9
FORWARD_SPEED = 1
BACK_SPEED = 0.9
MIN_SPEED = 0.7

try:
    client_userdata = {}
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    logger.info('MQTT Client Connected')
    #logger.info('Waiting for messages...')
    mqtt_client.loop_start()

    logger.info('Initializing PCF8591 ADC')
    i2c = board.I2C()
    pcf = PCF.PCF8591(i2c)
    logger.info('PCF8591 ADC Initialized')

    stick_button = AnalogIn(pcf,PCF.A1)
    stick_y = AnalogIn(pcf,PCF.A2)
    stick_x = AnalogIn(pcf,PCF.A3)
    logger.info('Ready for user input...')
    while True:
        #print(f'x: {stick_x.value} \t\t y:{stick_y.value}')
        
        #+x is forward
        #-x is back
        #+y is left
        #-y is right
        speed = 0
        if stick_x.value > STICK_IDLE_MAX:
            #forward
            speed = (stick_x.value - STICK_IDLE_MAX )/(STICK_MAX - STICK_IDLE_MAX) * (FORWARD_SPEED-MIN_SPEED) + MIN_SPEED
            mqtt_client.publish(topic=TOPIC_MOTOR_LEFT_THROTTLE,payload=speed,qos=0) 
            mqtt_client.publish(topic=TOPIC_MOTOR_RIGHT_THROTTLE,payload=speed,qos=0) 
        elif stick_x.value < STICK_IDLE_MIN:
            #back
            speed = (STICK_IDLE_MIN - stick_x.value)/STICK_IDLE_MIN * (BACK_SPEED - MIN_SPEED) + MIN_SPEED
            mqtt_client.publish(topic=TOPIC_MOTOR_LEFT_THROTTLE,payload=-1*speed,qos=0) 
            mqtt_client.publish(topic=TOPIC_MOTOR_RIGHT_THROTTLE,payload=-1*speed,qos=0) 
        elif stick_y.value > STICK_IDLE_MAX:
            #left
            speed = (stick_y.value - STICK_IDLE_MAX)/(STICK_MAX - STICK_IDLE_MAX) * (TURN_SPEED - MIN_SPEED) + MIN_SPEED
            mqtt_client.publish(topic=TOPIC_MOTOR_LEFT_THROTTLE,payload=-1*speed,qos=0) 
            mqtt_client.publish(topic=TOPIC_MOTOR_RIGHT_THROTTLE,payload=speed,qos=0) 
        elif stick_y.value < STICK_IDLE_MIN:
            #right
            speed = (STICK_IDLE_MIN - stick_y.value)/STICK_IDLE_MIN * (TURN_SPEED- MIN_SPEED) + MIN_SPEED
            mqtt_client.publish(topic=TOPIC_MOTOR_LEFT_THROTTLE,payload=speed,qos=0) 
            mqtt_client.publish(topic=TOPIC_MOTOR_RIGHT_THROTTLE,payload=-1*speed,qos=0) 
        #print(speed)

        sleep(0.05)
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
