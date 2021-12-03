import pytweening
from time import time, sleep
from robud.motors.motors_common import TOPIC_HEAD_SERVO_ANGLE
from robud.robud_face.robud_face_common import *
import paho.mqtt.client as mqtt
import numpy as np
import pickle
import random
from robud.robud_logging.MQTTHandler import MQTTHandler
import argparse
import logging
from datetime import datetime
import os
import sys
import traceback

TOPIC_HEAD_KEYFRAMES = "robud/robud_head/keyframes"

#keyframe: head angle duration representing time in seconds we want it to take to complete the movement
class head_keyframe():
    def __init__(
        self
        ,angle:int
        ,duration:float
    ) -> None:
        self.angle = angle
        self.duration = duration



#publishes animation frames to transition to new_left_expression & new_right_expression
def run_head_animation(
    mqtt_client:mqtt.Client,
    current_angle:int,
    new_angle: int,
    duration:float
    ):
    
    head_angle = current_angle
    #set last face expression to current frame
    last_angle = current_angle 
    
    #get the start time of the entire animation
    animation_start_time = time()

    #create array to hold animated values for each expression array value
    head_animated_value = AnimatedValue(
        start_value=last_angle,
        end_value=new_angle,
        duration=duration,
        start_time=animation_start_time,
        animation_function=pytweening.easeInOutQuad,
        pytweening_s = PYTWEENING_S
    )

    while(time()-animation_start_time <= duration):
        loopstart = time()
        head_angle = head_animated_value.get_updated_value()
        mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE,head_angle,qos=2, retain=True)
        #if face_expression[HEAD_SERVO_ANGLE] != None:
        #    print (face_expression[HEAD_SERVO_ANGLE])
        #    mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE,int(face_expression[HEAD_SERVO_ANGLE]),qos=2)

        loop_duration = time() - loopstart
        if loop_duration < 1/ANIMATION_FPS:
            sleep(1/ANIMATION_FPS - loop_duration)
    #always publish last frame
    mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE,new_angle,qos=2,retain=True)
    return head_angle
