import pickle
import random
from typing import Dict
from robud.robud_logging.MQTTHandler import MQTTHandler
import argparse
import logging
import os
from datetime import datetime
import traceback
import pickle
import paho.mqtt.client as mqtt
from robud.robud_state.robud_state_common import (
    TOPIC_ROBUD_STATE
    ,PERSON_DETECTION_HEIGHT
    ,PERSON_DETECTION_RANGE
    ,PERSON_DETECTION_TIMEOUT
    ,PERSON_DETECTION_WIDTH
    , move_eyes
    , logger
    )
from robud.robud_face.robud_face_common import *
from robud.ai.object_detection_common import TOPIC_OBJECT_DETECTION_DETECTIONS
from robud.motors.motors_common import TOPIC_HEAD_SERVO_ANGLE
from robud.robud_voice.robud_voice_common import TOPIC_ROBUD_VOICE_TEXT_INPUT
from robud.sensors.camera_common import CAMERA_HEIGHT, CAMERA_WIDTH
from robud.sensors.tof_common import TOPIC_SENSORS_TOF_RANGE
from robud.sensors.light_level_common import TOPIC_SENSORS_LIGHT_LEVEL
from time import monotonic

def robud_state_person_interaction(mqtt_client:mqtt.Client, client_userdata:Dict):
    try:
        logger.info("Starting ROBUD_STATE_PERSON_INTERACTION")

        def on_message_head_angle(client, userdata, message):
            userdata["head_angle"] = int(message.payload)
        #client_userdata["head_angle"] = 90
        mqtt_client.subscribe(TOPIC_HEAD_SERVO_ANGLE)
        mqtt_client.message_callback_add(TOPIC_HEAD_SERVO_ANGLE,on_message_head_angle)
        logger.info('Subcribed to ' + TOPIC_HEAD_SERVO_ANGLE)

        def on_message_animation_frame(client, userdata, message):
            #get the pointer to the main face_expression array
            face_expression = userdata["face_expression"]
            #get the new face expression from the buffer
            new_face_expression = np.frombuffer(buffer=message.payload,dtype=np.int16)
            #replace face expression with new values
            for i in range(0,FACE_EXPRESSION_ARRAY_SIZE):
                face_expression[i] = new_face_expression[i]
        client_userdata["face_expression"] = np.zeros(shape=FACE_EXPRESSION_ARRAY_SIZE, dtype=np.int16)
        set_expression(client_userdata["face_expression"], Expressions[ExpressionId.OPEN])
        mqtt_client.subscribe(TOPIC_FACE_ANIMATION_FRAME)
        mqtt_client.message_callback_add(TOPIC_FACE_ANIMATION_FRAME,on_message_animation_frame)
        logger.info('Subcribed to ' + TOPIC_FACE_ANIMATION_FRAME)

        def on_message_object_detections(client, userdata, message):
            object_detections = userdata["object_detections"]
            object_detections.clear()
            object_detections.extend(pickle.loads(message.payload))
        client_userdata["object_detections"] = []
        mqtt_client.subscribe(TOPIC_OBJECT_DETECTION_DETECTIONS)
        mqtt_client.message_callback_add(TOPIC_OBJECT_DETECTION_DETECTIONS,on_message_object_detections)
        logger.info('Subcribed to ' + TOPIC_OBJECT_DETECTION_DETECTIONS)

        def on_message_tof_range(client, userdata, message):
            userdata["tof_range"] = int(message.payload)
        client_userdata["tof_range"] = -1
        mqtt_client.subscribe(TOPIC_SENSORS_TOF_RANGE)
        mqtt_client.message_callback_add(TOPIC_SENSORS_TOF_RANGE,on_message_tof_range)
        logger.info('Subcribed to ' + TOPIC_SENSORS_TOF_RANGE)

        #Start interaction animation
        position_center = 0
        position_up = -50

        #greet the person!
        #randomize greeting
        greetings = [
            "Hello."
            ,"Hi!"
            ,"Sup?"
            ,"Yo."
            ,"Howdy."
        ]
        new_head_angle = 130
        gaze_vertical = position_up
        gaze_horizontal = position_center
        selected_position = (gaze_horizontal,gaze_vertical)
        change_expression = True
        left_expression = Expressions[ExpressionId.HAPPY]
        right_expression = Expressions[ExpressionId.HAPPY]

        logger.info("Initial animation")
        move_eyes(
            face_expression=client_userdata["face_expression"]
            ,right_expression=right_expression
            ,left_expression=left_expression
            ,selected_position = selected_position
            ,change_expression=change_expression
            ,new_head_angle = new_head_angle
            ,head_angle=client_userdata["head_angle"]
            ,mqtt_client=mqtt_client
        )

        mqtt_client.publish(TOPIC_ROBUD_VOICE_TEXT_INPUT, greetings[random.randint(0,len(greetings)-1)])

        last_person_detection = monotonic()

        while client_userdata["published_state"] == "ROBUD_STATE_PERSON_INTERACTION":
            #keep eye contact with person as long as they remain detected past timeout
            object_detections = client_userdata["object_detections"]
            tof_range = client_userdata["tof_range"]
            for detection in object_detections:
                
                    if (
                        detection["ClassLabel"] == "person" 
                        and detection["Height"] > CAMERA_HEIGHT*PERSON_DETECTION_HEIGHT
                        and detection["Width"] > CAMERA_WIDTH*PERSON_DETECTION_WIDTH
                        and tof_range > 30
                        and tof_range <= PERSON_DETECTION_RANGE
                        ):
                        
                            last_person_detection = monotonic()
            if monotonic() - last_person_detection > PERSON_DETECTION_TIMEOUT:
                logger.info("PERSON_DETECTION_TIMEOUT reached. Returning to ROBUD_STATE_IDLE")
                mqtt_client.publish(topic=TOPIC_ROBUD_STATE, payload = "ROBUD_STATE_IDLE", retain=True)
        
        logger.info("Finishing up of ROBUD_STATE_PERSON_INTERACTION")
        mqtt_client.unsubscribe(TOPIC_OBJECT_DETECTION_DETECTIONS)
        logger.info("Unsubscribed from " + TOPIC_OBJECT_DETECTION_DETECTIONS)
        mqtt_client.unsubscribe(TOPIC_SENSORS_TOF_RANGE)
        logger.info("Unsubscribed from " + TOPIC_OBJECT_DETECTION_DETECTIONS)
        mqtt_client.unsubscribe(TOPIC_FACE_ANIMATION_FRAME)
        logger.info("Unsubscribed from " + TOPIC_FACE_ANIMATION_FRAME)
        mqtt_client.unsubscribe(TOPIC_HEAD_SERVO_ANGLE)
        logger.info("Unsubscribed from " + TOPIC_HEAD_SERVO_ANGLE)
        logger.info("Exiting ROBUD_STATE_PERSON_INTERACTION")
    except Exception as e:
        logger.critical(str(e) + "\n" + traceback.format_exc())     

if __name__ == "__main__":
    MQTT_BROKER_ADDRESS = "robud.local"
    MQTT_CLIENT_NAME = "robud_state_person_interaction.py" + str(random.randint(0,999999999))
    client_userdata = {}
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME, userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start()
    logger.info('MQTT Client Connected')
    def on_message_robud_state(client, userdata, message):
        userdata["published_state"] = message.payload.decode()
    client_userdata["published_state"] = "ROBUD_STATE_PERSON_INTERACTION"
    mqtt_client.subscribe(TOPIC_ROBUD_STATE)
    mqtt_client.message_callback_add(TOPIC_ROBUD_STATE,on_message_robud_state)
    logger.info('Subcribed to ' + TOPIC_ROBUD_STATE)
    mqtt_client.publish(topic=TOPIC_ROBUD_STATE, payload = "ROBUD_STATE_PERSON_INTERACTION", retain=True)
    robud_state_person_interaction(mqtt_client, client_userdata)