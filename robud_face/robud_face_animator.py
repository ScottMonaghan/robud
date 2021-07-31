import pytweening
from time import time, sleep
from robud.robud_face.robud_face_common import *
import paho.mqtt.client as mqtt
import numpy as np
import pickle

MQTT_BROKER_ADDRESS = "localhost"
MQTT_CLIENT_NAME = "robud_face_animator.py"

def on_message_face_keyframes(client,userdata,message):
    #get the master keyframes list  used by the animation controller, passed in through userdata
    keyframes:list = userdata["keyframes"]
    #add received decoded pickle keyframes onto the end of the master keyframes object
    keyframes.extend(pickle.loads(message.payload))
    
def robud_face_animator():
    #initialize a master keyframes list for the animation controller
    keyframes:list = []
    
    #initialize a face expression array we'll use to keep track of the current state of the face
    face_expression = np.zeros(shape=FACE_EXPRESSION_ARRAY_SIZE, dtype=np.int16)
    #initilize the face expression to the default open expression
    set_expression(face_expression, Expressions[ExpressionId.OPEN])
    
    #initialize mqtt client
    client_userdata = {
        "keyframes":keyframes,
    }
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start()
    print('MQTT Client Connected')
    mqtt_client.subscribe(TOPIC_FACE_KEYFRAMES)
    mqtt_client.message_callback_add(TOPIC_FACE_KEYFRAMES,on_message_face_keyframes)
    print('Subcribed to', TOPIC_FACE_KEYFRAMES)


    while True:
        while len(keyframes) > 0:
            #if there are any keyframes in the list, remove the first item in the list
            keyframe:face_keyframe = keyframes.pop(0)
            #run the animation based on the keyframe
            face_expression = run_animation(
                mqtt_client=mqtt_client,
                current_face_expression=face_expression,
                new_left_expression=keyframe.left_expression,
                new_right_expression=keyframe.right_expression,
                new_position=keyframe.position,
                duration=keyframe.duration
                )
        sleep(0.1)   

if __name__ == '__main__':
    robud_face_animator()