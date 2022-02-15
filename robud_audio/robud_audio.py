#robud_audio.py
#Receives & Plays Audio Messages
#Records from microphone and publishes audio-input-related messages
#
# To-Do
#[x]Publish audio direction detection
#   [x] Read direction directly from respeaker hardware
#   [x] Publish audio direction
#[]Create Detected Speech Audio Stream
#   [x] Read speech detection directly from respeaker hardware
#   [] Process speech detection to smooth it out and provide padding 
#   [] Publish Speech Detection Audio Stream

from email.mime import audio
from io import BytesIO

from itsdangerous import NoneAlgorithm
from robud.robud_audio.robud_audio_common import (
    TOPIC_AUDIO_INPUT_COMMAND
    , TOPIC_AUDIO_INPUT_DATA
    , TOPIC_AUDIO_OUTPUT_DATA
    , AUDIO_INPUT_COMMAND_START
    , AUDIO_INPUT_COMMAND_STOP
    , TOPIC_AUDIO_INPUT_DIRECTION,
    TOPIC_SPEECH_INPUT_COMPLETE
    , TOPIC_SPEECH_INPUT_DATA
)
from robud.robud_audio.robud_audio_config import (
    LOGGING_LEVEL
    , MQTT_BROKER_ADDRESS
    , SAMPLE_RATE
    , AUDIO_INPUT_INDEX
    , CHUNK
    , SPEECH_DETECTION_PADDING_SEC
    , SPEECH_DETECTION_RATIO
    , BYTES_PER_FRAME
)

import random
import logging
import argparse
from robud.robud_logging.MQTTHandler import MQTTHandler
from datetime import datetime
import os
import traceback
import sys
import paho.mqtt.client as mqtt
import pickle
from time import sleep
from pyaudio import PyAudio, paInt16, paContinue, Stream
import pyaudio
#from precise_runner import PreciseEngine, PreciseRunner
import struct 
from robud.robud_audio.respeaker_v2 import Tuning, find
import collections, queue

random.seed()

MQTT_CLIENT_NAME = "robud_audio.py" + str(random.randint(0,999999999))

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.DEBUG

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/robud_audio_log_")
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

#initialize respeaker
respeaker = find()

#speech detection (based on https://github.com/coqui-ai/STT-examples/blob/r1.0/mic_vad_streaming/mic_vad_streaming.py)
num_padding_chunks = int((SAMPLE_RATE / CHUNK) * SPEECH_DETECTION_PADDING_SEC)
speech_ring_buffer = collections.deque(maxlen=num_padding_chunks)
speech_detection_triggered = False


try:
    #initialize audio
    logging.info("Initializing audio...")

    audio_output_buffer = collections.deque(maxlen=300) #2048 per chunk @ 16khz 
    audio_input_buffer = collections.deque(maxlen=300)
    speech_output_buffer = collections.deque(maxlen=6)

    BYTES_PER_CHUNK = CHUNK * BYTES_PER_FRAME
    def stream_callback(in_data, frame_count, time_info, status):
        global audio_output_buffer
        global audio_input_buffer
        #global speech_ring_buffer
        #global speech_detection_triggered

        #keep this minimal to prevent ALSA from timing out

        #capture input
        audio_input_buffer.append((in_data,respeaker.direction,respeaker.is_speech()))

        #prepare output
        if audio_output_buffer and len(audio_output_buffer) > 0: #FRAME_BYTES:
            out_data = audio_output_buffer.popleft()
            out_data += bytes(BYTES_PER_CHUNK - len(out_data)) # make sure the size is always correct
        else:
            out_data = bytes(BYTES_PER_CHUNK)
        return (out_data, pyaudio.paContinue)
    pa = PyAudio()
    stream = pa.open(
        rate=SAMPLE_RATE
        ,channels=1
        ,format = paInt16
        ,input=True
        ,frames_per_buffer=CHUNK
        ,input_device_index=AUDIO_INPUT_INDEX
        ,stream_callback=stream_callback
        ,output=True 
        ,start=True
    )


    #initialize mqtt
    def on_message_audio_input_command(client:mqtt.Client, userdata, message):
        command = message.payload.decode()
        logger.info('Audio Input Command Recieved: ' + command)
        userdata["command"]=command

    def on_message_audio_output_data(client:mqtt.Client, userdata, message):
        global audio_output_buffer
        audio = message.payload
        bytes_per_chunk = CHUNK * BYTES_PER_FRAME
        #logger.info('Audio Output Command Recieved: ' + command)
        while len(audio) > 0:
            if len(audio) > bytes_per_chunk:
                audio_output_buffer.append(audio[:bytes_per_chunk])
                audio =  audio[bytes_per_chunk:]
            else:
                audio_output_buffer.append(audio)
                audio = ""
        return

    client_userdata = {"command":""}
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    logger.info('MQTT Client Connected')
    mqtt_client.subscribe(TOPIC_AUDIO_INPUT_COMMAND)
    mqtt_client.message_callback_add(TOPIC_AUDIO_INPUT_COMMAND, on_message_audio_input_command)   
    logger.info('Subscribed to ' + TOPIC_AUDIO_INPUT_COMMAND)
    mqtt_client.subscribe(TOPIC_AUDIO_OUTPUT_DATA)
    mqtt_client.message_callback_add(TOPIC_AUDIO_OUTPUT_DATA, on_message_audio_output_data)   
    logger.info('Subscribed to ' + TOPIC_AUDIO_OUTPUT_DATA)
    #stream.start_stream()
    logger.info('Waiting for messages...')
    mqtt_client.loop_start()

    #

    #When I tried to put the below in the mqtt callback, it would never fully stop the stream and would never compelte the callback
    while True:
        if len(client_userdata["command"]) > 0:
            command = client_userdata["command"]
            if command == AUDIO_INPUT_COMMAND_START and stream.is_stopped():
                logger.info("Starting Stream")
                #stream.start_stream()
                logger.info("Stream Started")
            elif command == AUDIO_INPUT_COMMAND_STOP and not(stream.is_stopped()):
                logger.info("Stopping Stream")
                #stream.stop_stream()
                logger.info("Stream Stopped")
            client_userdata["command"] = ""
        elif len(audio_input_buffer) > 0:
            #process input audio
            
            #publish raw audio input
            while len(audio_input_buffer) > 0:
                data, direction, is_speech = audio_input_buffer.popleft()
                #publish raw data
                mqtt_client.publish(TOPIC_AUDIO_INPUT_DATA,payload=data,qos=2)
                #publish direction 
                mqtt_client.publish(TOPIC_AUDIO_INPUT_DIRECTION,payload=direction,qos=2)
                #now check for speech
                if not speech_detection_triggered:
                    speech_ring_buffer.append((data,is_speech))
                    num_voiced = len([chunk for chunk, speech in speech_ring_buffer if speech])
                    if num_voiced > SPEECH_DETECTION_RATIO * speech_ring_buffer.maxlen:
                        speech_detection_triggered = True
                        logger.debug("Speech Detected")
                        speechchunks = bytes()
                        for chunk, s in speech_ring_buffer:
                            mqtt_client.publish(TOPIC_SPEECH_INPUT_DATA,payload=chunk,qos=2)
                        speech_ring_buffer.clear()
                else:
                    #keep publishing audio until speech stops
                    mqtt_client.publish(TOPIC_SPEECH_INPUT_DATA,payload=data,qos=2)
                    speech_ring_buffer.append((data, is_speech))
                    num_unvoiced = len([chunk for chunk, speech in speech_ring_buffer if not speech])
                    if num_unvoiced > SPEECH_DETECTION_RATIO * speech_ring_buffer.maxlen:
                        speech_detection_triggered = False
                        speech_ring_buffer.clear()
                        mqtt_client.publish(TOPIC_SPEECH_INPUT_COMPLETE,payload="True",qos=2)
        else:
            sleep(0.1)
       
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
    try:
        stream.stop_stream()
        stream.close()
        respeaker.close()
        sys.exit(0)
    except SystemExit:
        stream.stop_stream()
        stream.close()
        respeaker.close()
        os._exit(0)