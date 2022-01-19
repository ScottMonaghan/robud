from copyreg import remove_extension
from robud.ai.stt.stt_config import (
    MQTT_BROKER_ADDRESS 
    ,AUDIO_INPUT_INDEX 
    ,STT_MODEL_PATH
    ,STT_SCORER_PATH
    ,VAD_AGGRESSIVENESS
    ,SAMPLE_RATE

)
from robud.ai.stt.stt_common import(
    TOPIC_STT_OUTPUT,
    TOPIC_STT_REQUEST
)
from robud.ai.stt.vadaudio import Audio, VADAudio
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
import pyaudio
import wave
import webrtcvad
from halo import Halo
from scipy import signal
import threading, collections, queue, os.path
from robud.robud_voice.robud_voice_common import TOPIC_ROBUD_VOICE_TEXT_INPUT
from robud.robud_questions.robud_questions_common import TOPIC_QUESTIONS
import re #regular expressions

random.seed()

MQTT_CLIENT_NAME = "stt.py" + str(random.randint(0,999999999))

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
    def on_message_stt_request(client:mqtt.Client, userdata, message):
        logger.info("STT request received")
        #handle stt_request
        model:stt.Model = userdata["model"]
        vad_audio:VADAudio = userdata["vad_audio"]
        vad_audio.stream.start_stream()
        # Start audio with VAD
        stream_context = model.createStream()
        frames = vad_audio.vad_collector(padding_ms=500)
        for frame in frames:
            if frame is not None:
                logging.debug("streaming frame")
                stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
            else:
                logging.debug("end utterence")
                vad_audio.stream.stop_stream()
                text = stream_context.finishStream()
                #there is a hotword bug that puts junk single characters after hotwords
                #this is a quick and dirty replacement
                #TODO: actually traverse list of hotwords and remove singel characters that fall after specific hotwords
                print("\"" + text + "\"")
                text=re.sub('(\s[a-z]){2,}\s',' ',text) #at least two occurence of single letters surrounded by spaces
                #trim trailing spaces
                text = text.strip()
                logging.info("Recognized: %s" % text)
                #if len(text) > 0:
                client.publish(TOPIC_QUESTIONS,qos=2, payload=text)
                return

    # Load STT model

    print('Initializing model...')
    logging.info("STT_MODEL_PATH: %s", STT_MODEL_PATH)
    model = stt.Model(STT_MODEL_PATH)

    #load scorer
    logging.info("STT_SCORER_PATH: %s", STT_SCORER_PATH)
    model.enableExternalScorer(STT_SCORER_PATH)
    
    #Add hotwords
    #TODO: move to external configuration
    model.addHotWord("tomorrow", 25.0) #STT "tomorrow" often interprets as "to morrow"
    model.addHotWord("weather", 15.0) #STT "weather" often interprets as "whether"

    # Start audio with VAD
    vad_audio = VADAudio(aggressiveness=VAD_AGGRESSIVENESS
                         ,device=AUDIO_INPUT_INDEX
                         ,input_rate=SAMPLE_RATE)
    vad_audio.stream.stop_stream()

    client_userdata = {
        "model":model
        ,"vad_audio":vad_audio
    }
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    logger.info('MQTT Client Connected')
    mqtt_client.subscribe(TOPIC_STT_REQUEST)
    mqtt_client.message_callback_add(TOPIC_STT_REQUEST,on_message_stt_request)
    logger.info('Waiting for messages...')
    mqtt_client.loop_forever()
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)