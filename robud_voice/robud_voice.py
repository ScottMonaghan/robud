from librosa.core import pitch
import paho.mqtt.client as mqtt
import subprocess
import random
from robud.robud_logging.MQTTHandler import MQTTHandler
import argparse
import logging
from datetime import datetime
import os
import sys
import traceback
from robud.robud_voice.robud_voice_common import TOPIC_ROBUD_VOICE_TEXT_INPUT
from robud.robud_audio.robud_audio_common import TOPIC_AUDIO_OUTPUT_DATA
import numpy as np
import librosa.effects
from scipy import signal
from time import monotonic, sleep
from collections import deque


random.seed()

MQTT_BROKER_ADDRESS = "robud.local"
MQTT_CLIENT_NAME = "robud_voice.py" + str(random.randint(0,999999999))

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.INFO

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/robud_voice_log_")
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
    def resample(data, input_rate, output_rate):
        """
        Args:
            data (binary): Input audio stream
            input_rate (int): Input audio rate to resample from
            output_rate (int): Output audio rate to resample to
        """
        data16 = np.frombuffer(buffer=data, dtype=np.int16)
        resample_size = int(len(data16) / input_rate * output_rate)
        resample = signal.resample(data16, resample_size)
        resample16 = np.array(resample, dtype=np.int16)
        return resample16.tobytes()

    def pitch_shift(data,sample_rate,semitones):
        """
        Args:
            data (binary): Input audio stream
            sample_rate (int): sample_rate of data
            output_rate (int): number of semitones to shift pitch of data
        """
        data16 = np.frombuffer(buffer=data, dtype=np.int16)
        data64 = np.array(data16, dtype=np.float64)
        resample = librosa.effects.pitch_shift(
            y=data64
            ,sr=sample_rate
            ,n_steps=semitones
            ,bins_per_octave=12      
        )
        resample16 = np.array(resample, dtype=np.int16) 
        return resample16.tobytes()

    sentence_queue = deque()

    def on_message_robud_voice_text_input(client:mqtt.Client, userdata, message):
        tts = message.payload.decode()
        logger.debug(tts)

        #split tts out by sentences
        sentences = tts.split(". ")
        sentence_queue.extend(sentences)
        # for sentence in sentences:
        #     result = subprocess.run(args=['espeak-ng', '-m', '-v', 'en-us-1', '-s', '155', '-p', '100', sentence, '--stdout'], stdout=subprocess.PIPE) #, shell=True)
        #     speech = result.stdout[result.stdout.find(b'data')+8:]
        #     speech = resample(speech,22050,16000)
    
        #     speech = pitch_shift(speech,16000,6)
        #     client.publish(topic=TOPIC_AUDIO_OUTPUT_DATA,payload=speech)
        #     sleep(2)
 
    client_userdata = {}
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    logger.info('MQTT Client Connected')
    mqtt_client.subscribe(TOPIC_ROBUD_VOICE_TEXT_INPUT)
    mqtt_client.message_callback_add(TOPIC_ROBUD_VOICE_TEXT_INPUT,on_message_robud_voice_text_input)
    logger.info('Waiting for messages...')
    mqtt_client.loop_start()

    while True:
        while len(sentence_queue) > 0:
            sentence = sentence_queue.popleft()
            result = subprocess.run(args=['espeak-ng', '-m', '-v', 'en-us-1', '-s', '155', '-p', '100', sentence, '--stdout'], stdout=subprocess.PIPE) #, shell=True)
            speech = result.stdout[result.stdout.find(b'data')+8:]
            speech = resample(speech,22050,16000)
    
            speech = pitch_shift(speech,16000,6)
            mqtt_client.publish(topic=TOPIC_AUDIO_OUTPUT_DATA,payload=speech)
            #sleep(2)
        sleep(0.1)
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
