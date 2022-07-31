from robud.robud_questions.robud_questions_config import (
    MQTT_BROKER_ADDRESS,
    WOLFRAM_ALPHA_APP_ID
)
from robud.robud_questions.robud_questions_common import(
    WOLFRAM_SPOKEN_RESULTS_API_URL,
    TOPIC_QUESTIONS
)
from robud.robud_voice.robud_voice_common import TOPIC_ROBUD_VOICE_TEXT_INPUT
from urllib.request import urlopen
from urllib.parse import urlencode
import urllib.error
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


random.seed()

MQTT_CLIENT_NAME = "robud_questions.py" + str(random.randint(0,999999999))

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.DEBUG

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/robud_questions_log_")
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
    def on_message_questions(client:mqtt.Client, userdata, message):
        try:
            logger.info("Question Recieved")
            pre_answers = [
                "Let me look that up for you."
                ,"Let's see."
                ,"Good question. Just a moment."
                ,"Let's find out."
            ]

            #client.publish(TOPIC_ROBUD_VOICE_TEXT_INPUT, payload=pre_answers[random.randint(0,len(pre_answers)-1)])
            
            question = message.payload.decode()
            logger.info("Question: " + question)
            data = urlencode({
                    "appid":WOLFRAM_ALPHA_APP_ID
                    ,"i":question
                })
            url = WOLFRAM_SPOKEN_RESULTS_API_URL + "?" + data
            logger.info("Sending request to Wolfram Alpha API...")
            answer = ""
            # with urlopen(url) as f:
            #     answer = (pre_answers[random.randint(0,len(pre_answers)-1)] 
            #      + " " + f.read().decode('utf-8').replace('Wolfram Alpha','Ro-Bud').replace('Stephen Wolfram', 'Scott Monaghan')
            #     )
            with urlopen(url) as f:
                answer = f.read().decode('utf-8').replace('Wolfram Alpha','Ro-Bud').replace('Stephen Wolfram', 'Scott Monaghan')
                
            logger.info("Answer recieved: " + answer)
            logger.info("Sending TOPIC_VOICE_TEXT_INPUT")
            #add period to answer
            answer = answer + "."
            client.publish(TOPIC_ROBUD_VOICE_TEXT_INPUT, payload=answer)
        except urllib.error.HTTPError as e:
            if e.code == 501:
                #501 not implemented, Wolfram Alpha doesn't know the answer
                client.publish(TOPIC_ROBUD_VOICE_TEXT_INPUT, payload="I don't know that.")
            
            logger.error(str(e))


    client_userdata = {}
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    logger.info('MQTT Client Connected')
    mqtt_client.subscribe(TOPIC_QUESTIONS)
    mqtt_client.message_callback_add(TOPIC_QUESTIONS,on_message_questions)
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