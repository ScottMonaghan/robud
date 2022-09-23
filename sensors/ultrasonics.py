import board
import busio
import adafruit_hcsr04
import time
import statistics
import paho.mqtt.client as mqtt
import random
from robud.robud_logging.MQTTHandler import MQTTHandler
import argparse
import logging
from datetime import datetime
import os
import sys
import traceback
from robud.sensors.ultrasonics_common import (
    TOPIC_SENSORS_ULTRASONICS_LEFT_FRONT_RANGE
    , TOPIC_SENSORS_ULTRASONICS_LEFT_RANGE
    , TOPIC_SENSORS_ULTRASONICS_RIGHT_FRONT_RANGE
    , TOPIC_SENSORS_ULTRASONICS_RIGHT_RANGE 
)

random.seed()

MQTT_BROKER_ADDRESS = "robud.local"
MQTT_CLIENT_NAME = "ultrasonics.py" + str(random.randint(0,999999999))

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.DEBUG

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/time-of-flight_log_")
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
    logger.info("starting")
    sensor_front_left = adafruit_hcsr04.HCSR04(trigger_pin=board.D16, echo_pin=board.D20)
    sensor_left = adafruit_hcsr04.HCSR04(trigger_pin=board.D26, echo_pin=board.D19)
    sensor_right = adafruit_hcsr04.HCSR04(trigger_pin=board.D11, echo_pin=board.D9)
    sensor_front_right = adafruit_hcsr04.HCSR04(trigger_pin=board.D25, echo_pin=board.D8)

    sample_size = 4
    tolerance = 0.1
    rate = 5 #publish rate in hz
    # topic = TOPIC_SENSORS_TOF_RANGE

    def get_range_from_sample(sample):
        if len(sample)>0:
            #first get median from sample
            median = statistics.median(sample)
            #now check if all values are in tolerance
            for measurement in sample:
                if abs(median - measurement) > tolerance * median:
                    sample.remove(measurement)
                    #return -1
            return int(sum(sample)/len(sample))
        else: return -1

    client = mqtt.Client(MQTT_CLIENT_NAME) #create new instance
    client.connect(MQTT_BROKER_ADDRESS)
    # #to make this useful, we'll only publish if the sample set are within tolerance of each other
    client.loop_start()
    while True:
        try:
            loop_start = time.time()
            sensor_front_left_sample = []
            sensor_left_sample = []
            sensor_front_right_sample = []
            sensor_right_sample = []
            for i in range(sample_size-1):
                try:
                    sensor_front_left_sample.append(sensor_front_left.distance)
                except RuntimeError:
                    pass #timeout
                try:
                    sensor_left_sample.append(sensor_left.distance)
                except RuntimeError:
                    pass #timeout
                try:
                    sensor_front_right_sample.append(sensor_front_right.distance)
                except RuntimeError:
                    pass #timeout  
                try:
                    sensor_right_sample.append(sensor_right.distance)
                except RuntimeError:
                    pass #timeout   
            front_left_range = get_range_from_sample(sensor_front_left_sample)
            left_range = get_range_from_sample(sensor_left_sample)
            front_right_range = get_range_from_sample(sensor_front_right_sample)
            right_range = get_range_from_sample(sensor_right_sample)
            print ((front_left_range,left_range, front_right_range, right_range))
            #logger.debug('{} cm'.format(tof_range))
            client.publish(topic=TOPIC_SENSORS_ULTRASONICS_LEFT_FRONT_RANGE,payload=front_left_range,qos=0)
            client.publish(topic=TOPIC_SENSORS_ULTRASONICS_LEFT_RANGE,payload=left_range,qos=0)
            client.publish(topic=TOPIC_SENSORS_ULTRASONICS_RIGHT_FRONT_RANGE,payload=front_right_range,qos=0)
            client.publish(topic=TOPIC_SENSORS_ULTRASONICS_RIGHT_RANGE,payload=right_range,qos=0)
            loop_time = time.time()-loop_start
            if (loop_time<1/rate):
                time.sleep( 1/rate - loop_time)
        except RuntimeError as e:
            logger.error("Timeout")
            time.sleep(0.1)
        except OSError as e:
            logger.error(str(e) + "\n" + traceback.format_exc())
            time.sleep(0.1)
   
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
finally:    
    exit(0)


  
    