#robud_audio.py
#Receives & Plays Audio Messages
#Records from microphone and publishes audio-input-related messages
#
# To-Do
# []Audio Input
#   [x]Enable/Disable   -- 18-Jan 2022
#   [x]Publish input    -- 18-Jan 2022 
#   [x]Update wakeword & stt to receieve audio via messages
#   []Update robud_state with wake word prompt & question prompt
#
# []Audio Output
#   []Enable/Disable
#   [x]Add pitch shifter helper class -- in robud_voice
#   []Receive Messages
#   []Callbacks for when audio is complete
#   []Update robud_voice to publish messages to audio out 
#       []Use pitch shifter helper class instead of LASPA plugin
#       []Split into separate sentences
#       []Sync with captions

from email.mime import audio
from io import BytesIO

from itsdangerous import NoneAlgorithm
from robud.robud_audio.robud_audio_common import (
    TOPIC_AUDIO_INPUT_COMMAND
    , TOPIC_AUDIO_INPUT_DATA
    , TOPIC_AUDIO_OUTPUT_DATA
    , AUDIO_INPUT_COMMAND_START
    , AUDIO_INPUT_COMMAND_STOP
)
from robud.robud_audio.robud_audio_config import (
    LOGGING_LEVEL
    , MQTT_BROKER_ADDRESS
    , SAMPLE_RATE
    , AUDIO_INPUT_INDEX
    , CHUNK
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

try:
    #initialize audio
    logging.info("Initializing audio...")

    audio_output_buffer:bytes = b""
   
    def stream_callback(in_data, frame_count, time_info, status):
        global audio_output_buffer
        FRAME_BYTES = frame_count * 2
        #Receive each chunk of audio captured, and publish it
        mqtt_client.publish(TOPIC_AUDIO_INPUT_DATA,payload=in_data,qos=2)
        if audio_output_buffer and len(audio_output_buffer) > FRAME_BYTES:
            out_data = audio_output_buffer[:FRAME_BYTES]
            audio_output_buffer = audio_output_buffer[FRAME_BYTES:]
        else:
            out_data = bytes(FRAME_BYTES)
        #print("stream_callback")
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

    # output_stream = pa.open(
    #     rate=SAMPLE_RATE
    #     ,channels=1
    #     ,format = paInt16
    #     ,input=True
    #     ,frames_per_buffer=CHUNK
    #     ,input_device_index=AUDIO_INPUT_INDEX
    #     ,output=True 
    #     ,start=True
    # )

    #initialize mqtt
    def on_message_audio_input_command(client:mqtt.Client, userdata, message):
        command = message.payload.decode()
        logger.info('Audio Input Command Recieved: ' + command)
        userdata["command"]=command

    def on_message_audio_output_data(client:mqtt.Client, userdata, message):
        global audio_output_buffer
        audio = message.payload
        #logger.info('Audio Output Command Recieved: ' + command)
        audio_output_buffer += audio
        #stream.write(audio)

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
        else:
            sleep(0.1)
       
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)