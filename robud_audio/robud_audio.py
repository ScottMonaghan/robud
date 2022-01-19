#robud_audio.py
#Receives & Plays Audio Messages
#Records from microphone and publishes audio-input-related messages
#
# To-Do
# []Audio Input
#   []Enable/Disable
#   []Publish input
#   []Update wakeword & stt to receieve audio via messages
#   []Update robud_state with wake word prompt & question prompt
#
# []Audio Output
#   []Enable/Disable
#   []Add pitch shifter helper class
#   []Receive Messages
#   []Callbacks for when audio is complete
#   []Update robud_voice to publish messages to audio out 
#       []Use pitch shifter helper class instead of LASPA plugin
#       []Split into separate sentences
#       []Sync with captions

from robud.robud_audio.robud_audio_common import *
from robud.robud_audio.robud_audio_config import *

import random
import logging
import argparse
from robud.robud_logging.MQTTHandler import MQTTHandler
from datetime import datetime
import os
import traceback
import sys
import paho.mqtt.client as mqtt
import time
import stt
import numpy as np
from pyaudio import PyAudio, paInt16
import wave
import webrtcvad
from halo import Halo
from scipy import signal
import threading, collections, queue, os.path
from robud.robud_voice.robud_voice_common import TOPIC_ROBUD_VOICE_TEXT_INPUT
from robud.robud_questions.robud_questions_common import TOPIC_QUESTIONS
import re #regular expressions

random.seed()

MQTT_CLIENT_NAME = "robud_audio.py" + str(random.randint(0,999999999))

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
    #initialize audio

    pass
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)