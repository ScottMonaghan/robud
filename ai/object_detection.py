import jetson.inference
import jetson.utils
import numpy as np
import paho.mqtt.client as mqtt
import cv2
import time
import pickle
import random
from robud.robud_logging.MQTTHandler import MQTTHandler
import argparse
import logging
from datetime import datetime
import os
import sys
import traceback
from robud.ai.object_detection_common import TOPIC_OBJECT_DETECTION_DETECTIONS, TOPIC_OBJECT_DETECTION_REQUEST, TOPIC_OBJECT_DETECTION_VIDEO_FRAME
from robud.sensors.camera_common import TOPIC_CAMERA_RAW

random.seed()

MQTT_BROKER_ADDRESS = "robud.local"
MQTT_CLIENT_NAME = "object_detection.py" + str(random.randint(0,999999999))

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.DEBUG
FRAME_TIMEOUT = 2

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/object_detection_log_")
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


OBJECT_DETECTION_RATE = 5 #hz

try:
    logger.info("starting")
    def on_message(client:mqtt.Client,userdata,message):
        processor = userdata
        if not processor['is_processing'] and time.time() - processor['last_frame_start'] > 1/OBJECT_DETECTION_RATE:
            processor['last_frame_start'] = time.time()
            processor['is_processing'] = True

            payload=message.payload
            np_bytes = np.frombuffer(payload, np.uint8)
            cv_image = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
            cv_image = cv2.cvtColor(cv_image,cv2.COLOR_BGR2RGB)
            #convert to cuda image
            img_input = jetson.utils.cudaFromNumpy(cv_image)

            detections = net.Detect(img_input)
            detections_out = [] * len(detections)
            for detection in detections:
                detection_out = {
                    "ClassID":detection.ClassID,
                    "ClassLabel":net.GetClassDesc(detection.ClassID),
                    "Confidence":detection.Confidence,
                    "Left":detection.Left,
                    "Top":detection.Top,
                    "Right":detection.Right,
                    "Bottom":detection.Bottom,
                    "Width":detection.Width,
                    "Height":detection.Height,
                    "Area":detection.Area,
                    "Center":detection.Center
                }
                detections_out.append(detection_out)
            #I *think* the above actually changes the image as well
            cv_image = jetson.utils.cudaToNumpy(img_input)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
            jpg_image = cv2.imencode('.jpg',cv_image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            detection_video_frame_payload=jpg_image[1].tobytes()

            client.publish(TOPIC_OBJECT_DETECTION_DETECTIONS, payload=pickle.dumps(detections_out))
            client.publish(TOPIC_OBJECT_DETECTION_VIDEO_FRAME, payload=detection_video_frame_payload)
            processor['is_processing'] = False
    
    def on_message_camera_raw(client,userdata,message):
        #grab the raw frame messages but perform no processing here to not waste resources
        userdata["last_frame_message"] = message.payload
        userdata["last_frame_time"] = time.time()
        pass
    
    def on_message_object_detection_request(client:mqtt.Client,userdata,message):
        object_detection_request = bool(int(message.payload))
        if object_detection_request == True:
            logger.info("Object detection request reveived")
            client.publish(topic=TOPIC_OBJECT_DETECTION_REQUEST, payload=int(False), retain=True)
            if "last_frame_time" in userdata and time.time() - userdata["last_frame_time"]<=FRAME_TIMEOUT:
                np_bytes = np.frombuffer(userdata["last_frame_message"], np.uint8)
                cv_image = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
                cv_image = cv2.cvtColor(cv_image,cv2.COLOR_BGR2RGB)
                #convert to cuda image
                img_input = jetson.utils.cudaFromNumpy(cv_image)

                detections = net.Detect(img_input)
                detections_out = [] * len(detections)
                for detection in detections:
                    detection_out = {
                        "ClassID":detection.ClassID,
                        "ClassLabel":net.GetClassDesc(detection.ClassID),
                        "Confidence":detection.Confidence,
                        "Left":detection.Left,
                        "Top":detection.Top,
                        "Right":detection.Right,
                        "Bottom":detection.Bottom,
                        "Width":detection.Width,
                        "Height":detection.Height,
                        "Area":detection.Area,
                        "Center":detection.Center
                    }
                    detections_out.append(detection_out)
                #I *think* the above actually changes the image as well
                cv_image = jetson.utils.cudaToNumpy(img_input)
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
                jpg_image = cv2.imencode('.jpg',cv_image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                detection_video_frame_payload=jpg_image[1].tobytes()

                client.publish(TOPIC_OBJECT_DETECTION_DETECTIONS, payload=pickle.dumps(detections_out))
                client.publish(TOPIC_OBJECT_DETECTION_VIDEO_FRAME, payload=detection_video_frame_payload)

    #load model
    net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)

    #processor = {'is_processing':False,'last_frame_start':0}
    client_userdata = {}
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME, userdata=client_userdata) #create new instance
    #mqtt_client.on_message=on_message
    mqtt_client.message_callback_add(TOPIC_OBJECT_DETECTION_REQUEST,on_message_object_detection_request)
    mqtt_client.message_callback_add(TOPIC_CAMERA_RAW,on_message_camera_raw)
    logger.info("connecting to broker")
    mqtt_client.connect(MQTT_BROKER_ADDRESS) #connect to broker

    logger.info("Subscribing to topic" + TOPIC_CAMERA_RAW)
    mqtt_client.subscribe(TOPIC_CAMERA_RAW)
    logger.info("Subscribing to topic" + TOPIC_OBJECT_DETECTION_REQUEST)
    mqtt_client.subscribe(TOPIC_OBJECT_DETECTION_REQUEST)    
    mqtt_client.loop_forever()
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
finally:    
    exit(0)


