from time import sleep
import logging
import argparse
from datetime import datetime
import os
import traceback
import pickle
import paho.mqtt.client as mqtt
import random
from robud.robud_logging.MQTTHandler import MQTTHandler
from  robud.robud_state.robud_state_idle import robud_state_idle
from robud.robud_state.robud_state_person_interaction import robud_state_person_interaction
from robud.robud_state.robud_state_sleeping import robud_state_sleeping
from robud.robud_state.robud_state_wakeword_detected import robud_state_wakeword_detected
from robud.robud_state.robud_state_exploring import robud_state_exploring
from robud.robud_state.robud_state_follow import robud_state_follow
from robud.robud_state.robud_state_common import TOPIC_ROBUD_STATE, logger

if __name__ == "__main__":
    try: 
        robud_state_functions = {
        "ROBUD_STATE_IDLE":robud_state_idle
        ,"ROBUD_STATE_PERSON_INTERACTION":robud_state_person_interaction
        ,"ROBUD_STATE_SLEEPING":robud_state_sleeping
        ,"ROBUD_STATE_WAKEWORD_DETECTED":robud_state_wakeword_detected
        ,"ROBUD_STATE_EXPLORING":robud_state_exploring
        ,"ROBUD_STATE_FOLLOW": robud_state_follow
        }

        MQTT_BROKER_ADDRESS = "robud.local"
        MQTT_CLIENT_NAME = "robud_state_manager.py" + str(random.randint(0,999999999))

        client_userdata = {}
        mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME, userdata=client_userdata)
        mqtt_client.connect(MQTT_BROKER_ADDRESS)
        mqtt_client.loop_start()
        logger.info('MQTT Client Connected')

        def on_message_robud_state(client, userdata, message):
            userdata["published_state"] = message.payload.decode()
        client_userdata["published_state"] = "ROBUD_STATE_IDLE"
        mqtt_client.subscribe(TOPIC_ROBUD_STATE)
        mqtt_client.message_callback_add(TOPIC_ROBUD_STATE,on_message_robud_state)
        logger.info('Subcribed to ' + TOPIC_ROBUD_STATE)
        mqtt_client.publish(topic=TOPIC_ROBUD_STATE, payload = "ROBUD_STATE_IDLE", retain=True)

        while True:
            robud_state_functions[client_userdata["published_state"]](mqtt_client,client_userdata)

    except Exception as e:
        logger.critical(str(e) + "\n" + traceback.format_exc())   