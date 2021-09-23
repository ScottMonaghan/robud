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

class MQTTHandler(logging.Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a MQTT server to a topic.
    """
    def __init__(self, hostname, topic, qos=0, retain=False,
            port=1883, client_id='', keepalive=60, will=None, auth=None,
            tls=None, protocol=mqtt.MQTTv31, transport='tcp', log_file:typing.TextIO =None):
        logging.Handler.__init__(self)
        self.topic = topic
        self.qos = qos
        self.retain = retain
        self.hostname = hostname
        self.port = port
        self.client_id = client_id
        self.keepalive = keepalive
        self.will = will
        self.auth = auth
        self.tls = tls
        self.protocol = protocol
        self.transport = transport
        self.log_file = log_file

    def emit(self, record):
        """
        Publish a single formatted logging record to a broker, then disconnect
        cleanly.
        """
        msg = self.format(record)
        publish.single(self.topic, msg, self.qos, self.retain,
            hostname=self.hostname, port=self.port,
            client_id=self.client_id, keepalive=self.keepalive,
            will=self.will, auth=self.auth, tls=self.tls,
            protocol=self.protocol, transport=self.transport)
        if self.log_file is not None and not self.log_file.closed:
            log_file.write(msg + "\n")
            log_file.flush()
            
        print(msg)

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
    parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="robud_log_")
    args = parser.parse_args()

    #initialize logger
    logger=logging.getLogger()
    log_file = open(args.Output + datetime.now().strftime("%Y-%m-%d") + ".txt","a")
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
    #time.sleep(5)
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
