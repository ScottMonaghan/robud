import board
import busio
import adafruit_vl53l0x
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
from robud.sensors.tof_common import TOPIC_SENSORS_TOF_RANGE

random.seed()

MQTT_BROKER_ADDRESS = "robud.local"
MQTT_CLIENT_NAME = "time-of-flight.py" + str(random.randint(0,999999999))

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
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_vl53l0x.VL53L0X(i2c)
    sample_size = 4
    tolerance = 0.05
    rate = 5 #publish rate in hz
    topic = TOPIC_SENSORS_TOF_RANGE

    def get_range_from_sample(sample):
        #first get median from sample
        median = statistics.median(sample)
        #now check if all values are in tolerance
        for measurement in sample:
            if abs(median - measurement) > tolerance * median:
                return -1
        return int(sum(sample)/len(sample)/10)

    client = mqtt.Client(MQTT_CLIENT_NAME) #create new instance
    client.connect(MQTT_BROKER_ADDRESS)
    #to make this useful, we'll only publish if the sample set are within tolerance of each other
    client.loop_start()
    while True:
        try:
            loop_start = time.time()
            sample = []
            for i in range(sample_size-1):
                sample.append(sensor.range)
            tof_range = get_range_from_sample(sample)
            #logger.debug('{} cm'.format(tof_range))
            if tof_range > -1:
                client.publish(topic=topic,payload=tof_range,qos=2)
            loop_time = time.time()-loop_start
            if (loop_time<1/rate):
                time.sleep( 1/rate - loop_time)
        except OSError as e:
            logger.error(str(e) + "\n" + traceback.format_exc())
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
finally:    
    exit(0)


  
    