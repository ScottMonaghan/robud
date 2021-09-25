"""
MIT License
Copyright (c) 2016 Pipat Methavanitpong
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Original code copied from https://gist.github.com/FulcronZ/9948756fea515e6d18b8bc2c7182bdb8
"""

import logging
import random
import argparse
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from datetime import datetime
import os
import sys
import typing
import traceback
from MQTTHandler import MQTTHandler

try: 
    
    # This script will subscribe to the robud_log topics and output to a file

    #seed randomizer
    random.seed()

    #set MQTT constants
    TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
    MQTT_BROKER_ADDRESS = "robud.local"
    MQTT_CLIENT_NAME = "robud_logging_robud_logger.py" + str(random.randint(0,999999999))
    TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
    TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
    LOGGING_LEVEL= logging.DEBUG

    #handler for MQTT messages
    def on_message(client:mqtt.Client, userdata, message:mqtt.MQTTMessage):
        #if the message comes from this script, don't write it again, this script already logs.
        if message.topic != TOPIC_ROBUD_LOGGING_LOG_SIGNED:
            log=message.payload.decode() + "\n"
            log_file.write(log)
            log_file.flush()
            print(log)

    #parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/robud_log_")
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
    
    #initilize mqtt client
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME)
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER_ADDRESS)

    mqtt_client.subscribe(topic=TOPIC_ROBUD_LOGGING_LOG_ALL, qos=2)
    logger.info("Starting robud_logger")
    logger.info("Logger subscribed to " + TOPIC_ROBUD_LOGGING_LOG_ALL + " at " + MQTT_BROKER_ADDRESS)
    logger.info("Log file set to " + str(os.path.realpath(log_file.name)))
    logger.info("Logging level set to " + logging.getLevelName(logger.level))

    mqtt_client.loop_forever()
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
