import paho.mqtt.client as mqtt
from typing import Dict
import random
from time import monotonic
import traceback
from robud.ai.wakeword_detection.wakeword_detection_common import TOPIC_WAKEWORD_DETECTED
from robud.motors.motors_common import HEAD_SERVO_MIN_ANGLE, TOPIC_HEAD_SERVO_ANGLE
from robud.sensors.light_level_common import TOPIC_SENSORS_LIGHT_LEVEL
from robud.ai.wakeword_detection.wakeword_detection_common import TOPIC_WAKEWORD_DETECTED
from robud.robud_state.robud_state_common import (
    POSITION_CENTER, 
    VERTICAL_POSITION_SLEEP,
    SLEEP_LIGHT_LEVEL,
    WAKE_LIGHT_LEVEL,
    SLEEP_ANIMATION_DURATION,
    WAKE_ANIMATION_DURATION,
    MINIMUM_SLEEP,
    MINIMUM_WAKE,
    TOPIC_ROBUD_STATE,
    move_eyes,
    logger
)
from robud.robud_face.robud_face_common import *

def robud_state_sleeping(mqtt_client:mqtt.Client, client_userdata:Dict):
    try:
        logger.info("Starting ROBUD_STATE_SLEEPING")
        # def on_message_light_level(client, userdata, message):
        #     userdata["light_level"] = int(message.payload)
        # mqtt_client.subscribe(TOPIC_SENSORS_LIGHT_LEVEL)
        # mqtt_client.message_callback_add(TOPIC_SENSORS_LIGHT_LEVEL,on_message_light_level)
        # logger.info('Subcribed to ' + TOPIC_SENSORS_LIGHT_LEVEL)

        def on_message_wakeword_detected(client, userdata, message):
            mqtt_client.publish(topic=TOPIC_ROBUD_STATE, payload="ROBUD_STATE_WAKEWORD_DETECTED")

        def on_message_head_angle(client, userdata, message):
            userdata["head_angle"] = int(message.payload)
        #client_userdata["head_angle"] = 90
        mqtt_client.subscribe(TOPIC_HEAD_SERVO_ANGLE)
        mqtt_client.message_callback_add(TOPIC_HEAD_SERVO_ANGLE,on_message_head_angle)
        logger.info('Subcribed to ' + TOPIC_HEAD_SERVO_ANGLE)

        def on_message_animation_frame(client, userdata, message):
            userdata["face_expression"] = np.frombuffer(buffer=message.payload,dtype=np.int16)

        client_userdata["face_expression"] = np.zeros(shape=FACE_EXPRESSION_ARRAY_SIZE, dtype=np.int16)
        set_expression(client_userdata["face_expression"], Expressions[ExpressionId.OPEN])
        mqtt_client.subscribe(TOPIC_WAKEWORD_DETECTED)
        mqtt_client.message_callback_add(TOPIC_WAKEWORD_DETECTED,on_message_wakeword_detected)
        logger.info('Subcribed to ' + TOPIC_WAKEWORD_DETECTED)
        mqtt_client.subscribe(TOPIC_FACE_ANIMATION_FRAME)
        mqtt_client.message_callback_add(TOPIC_FACE_ANIMATION_FRAME,on_message_animation_frame)
        logger.info('Subcribed to ' + TOPIC_FACE_ANIMATION_FRAME)
        #fall asleep
        sleep_time = monotonic()
        new_head_angle = HEAD_SERVO_MIN_ANGLE
        gaze_vertical = VERTICAL_POSITION_SLEEP
        gaze_horizontal = POSITION_CENTER
        selected_position = (gaze_horizontal,gaze_vertical)
        left_expression = Expressions[ExpressionId.BLINKING]
        right_expression = Expressions[ExpressionId.BLINKING]
        duration=SLEEP_ANIMATION_DURATION
        head_duration=SLEEP_ANIMATION_DURATION
        change_expression = True
        mqtt_client.publish(TOPIC_FACE_ENABLE_BLINK, int(False))
        logger.info('Beginning sleep animation...')
        move_eyes(
            face_expression=client_userdata["face_expression"].copy()
            ,right_expression=right_expression
            ,left_expression=left_expression
            ,selected_position = selected_position
            ,change_expression=change_expression
            ,new_head_angle = new_head_angle
            ,head_angle=client_userdata["head_angle"]
            ,mqtt_client=mqtt_client
            ,duration=duration
            ,head_duration=head_duration
        )
        sleep(SLEEP_ANIMATION_DURATION)
        while (
            client_userdata["published_state"]=="ROBUD_STATE_SLEEPING"
            and (
                monotonic() - sleep_time < MINIMUM_SLEEP
                or client_userdata["light_level"] < WAKE_LIGHT_LEVEL)
            ):
            sleep(0.1)
        #time to wake up!
        logger.info('Beginning wake animation...')
        sleeping = False
        wake_time = monotonic()
        new_head_angle = 90
        gaze_vertical = POSITION_CENTER
        gaze_horizontal = POSITION_CENTER
        selected_position = (gaze_horizontal,gaze_vertical)
        left_expression = Expressions[ExpressionId.BORED]
        right_expression = Expressions[ExpressionId.BORED]
        duration=WAKE_ANIMATION_DURATION
        head_duration=WAKE_ANIMATION_DURATION
        change_expression = True
        mqtt_client.publish(TOPIC_FACE_ENABLE_BLINK, int(True))
        move_eyes(
            face_expression=client_userdata["face_expression"].copy()
            ,right_expression=right_expression
            ,left_expression=left_expression
            ,selected_position = selected_position
            ,change_expression=change_expression
            ,new_head_angle = new_head_angle
            ,head_angle=client_userdata["head_angle"]
            ,mqtt_client=mqtt_client
            ,duration=duration
            ,head_duration=head_duration
        )
        sleep(WAKE_ANIMATION_DURATION)
        logger.info("Awoken.")
        #mqtt_client.publish(topic=TOPIC_ROBUD_STATE, payload = "ROBUD_STATE_IDLE", retain=True)
        
        logger.info("Finishing up of ROBUD_STATE_SLEEPING")

        
        mqtt_client.unsubscribe(TOPIC_SENSORS_LIGHT_LEVEL)
        logger.info("Unsubscribed from " + TOPIC_SENSORS_LIGHT_LEVEL)
        mqtt_client.unsubscribe(TOPIC_HEAD_SERVO_ANGLE)
        logger.info("Unsubscribed from " + TOPIC_HEAD_SERVO_ANGLE)
        mqtt_client.unsubscribe(TOPIC_FACE_ANIMATION_FRAME)
        logger.info("Unsubscribed from " + TOPIC_FACE_ANIMATION_FRAME)
        

        logger.info("Exiting ROBUD_STATE_SLEEPING")
    except Exception as e:
        logger.critical(str(e) + "\n" + traceback.format_exc())  

if __name__ == "__main__":
    MQTT_BROKER_ADDRESS = "robud.local"
    MQTT_CLIENT_NAME = "robud_state_sleeping.py" + str(random.randint(0,999999999))
    client_userdata = {}
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME, userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start()
    logger.info('MQTT Client Connected')
    def on_message_robud_state(client, userdata, message):
        userdata["published_state"] = message.payload.decode()
    client_userdata["published_state"] = "ROBUD_STATE_SLEEPING"
    mqtt_client.subscribe(TOPIC_ROBUD_STATE)
    mqtt_client.message_callback_add(TOPIC_ROBUD_STATE,on_message_robud_state)
    logger.info('Subcribed to ' + TOPIC_ROBUD_STATE)
    mqtt_client.publish(topic=TOPIC_ROBUD_STATE, payload = "ROBUD_STATE_SLEEPING", retain=True)
    robud_state_sleeping(mqtt_client, client_userdata)
