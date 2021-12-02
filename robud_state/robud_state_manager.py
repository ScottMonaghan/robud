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
from robud_state.robud_state_person_interaction import robud_state_person_interaction
from robud.robud_state.robud_state_common import TOPIC_ROBUD_STATE, logger



if __name__ == "__main__":
    try: 
        robud_state_functions = {
        "ROBUD_STATE_IDLE":robud_state_idle
        ,"ROBUD_STATE_PERSON_INTERACTION":robud_state_person_interaction
        }

        MQTT_BROKER_ADDRESS = "robud.local"
        MQTT_CLIENT_NAME = "robud_state_manager.py" + str(random.randint(0,999999999))
        # TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
        # TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
        # TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
        
        # LOGGING_LEVEL = logging.DEBUG

        # #parse arguments
        # parser = argparse.ArgumentParser()
        # parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/robud_state_manager_log_")
        # args = parser.parse_args()

        # #initialize logger
        # logger=logging.getLogger()
        # file_path = args.Output + datetime.now().strftime("%Y-%m-%d") + ".txt"
        # directory = os.path.dirname(file_path)
        # if not os.path.exists(directory):
        #     os.makedirs(directory)
        # log_file = open(file_path, "a")
        # myHandler = MQTTHandler(hostname=MQTT_BROKER_ADDRESS, topic=TOPIC_ROBUD_LOGGING_LOG_SIGNED, qos=2, log_file=log_file)
        # myHandler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(filename)s: %(message)s'))
        # logger.addHandler(myHandler)
        # logger.level = LOGGING_LEVEL

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
            robud_state_functions[client_userdata["published_state"]]()
            sleep(1)

    except Exception as e:
        logger.critical(str(e) + "\n" + traceback.format_exc())   