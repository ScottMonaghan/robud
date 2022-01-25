#wakeword_detection.py
#Subscribes to audio input stream from robud.robud_audio.robud_audio.py (/robud/robud_audio/input/data)
#Feeds audio into mycroft precise wakeword detection engine 
#Remote streaming code inspired by https://pyshine.com/How-to-send-audio-from-PyAudio-over-socket/

from ast import Bytes
from pyaudio import PyAudio, paInt16, paContinue, Stream
from io import BytesIO
#from precise_runner import PreciseEngine
from precise_runner.runner import TriggerDetector, PreciseEngine
from robud.ai.wakeword_detection.wakeword_detection_config import(
    LOGGING_LEVEL
    , MQTT_BROKER_ADDRESS
    , SAMPLE_RATE
    , CHUNK
    , SENSITIVITY
    , TRIGGER_LEVEL
)
from robud.ai.wakeword_detection.wakeword_detection_common import(
     TOPIC_WAKEWORD_DETECTED
)
from robud.robud_audio.robud_audio_common import (
    TOPIC_AUDIO_INPUT_DATA
)

import random
import logging
import argparse
from robud.robud_logging.MQTTHandler import MQTTHandler
from datetime import datetime
import os
import paho.mqtt.client as mqtt
from time import sleep
import traceback
import sys
import pickle
import struct

random.seed()

MQTT_CLIENT_NAME = "wakeword_detection.py" + str(random.randint(0,999999999))

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.DEBUG

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/robud_stt_log_")
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
    client_userdata = {}
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
 
    def on_message_audio_input_data(client:mqtt.Client, userdata, message):
        if engine.proc: #this is the Popen external process run for the precise engine. It takes a bit to fully open so this prevents errors before it fully starts.
            chunk = message.payload
            handle_predictions(chunk)

    def handle_predictions(chunk):
        """Check Precise process output"""
        prob = engine.get_prediction(chunk)
        if detector.update(prob):
           mqtt_client.publish(topic=TOPIC_WAKEWORD_DETECTED, payload="True",qos=2)
           logger.info("Wakeword Detected!")

    #initialize mqtt client
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    logger.info('MQTT Client Connected')
    mqtt_client.subscribe(TOPIC_AUDIO_INPUT_DATA)
    mqtt_client.message_callback_add(TOPIC_AUDIO_INPUT_DATA, on_message_audio_input_data)   
    logger.info('Subscribed to ' + TOPIC_AUDIO_INPUT_DATA)
    logger.info('Waiting for messages...')
    
    #initialize precise engine
    engine = PreciseEngine('/home/robud/Downloads/precise-engine/precise-engine', '/home/robud/src/precise-data/hey-mycroft.pb')
    detector = TriggerDetector(CHUNK, SENSITIVITY, TRIGGER_LEVEL)
    engine.start()

    mqtt_client.loop_forever()
    
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
