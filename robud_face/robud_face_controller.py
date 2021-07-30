import pytweening
from time import time
import re
from robud_face_common import *
import paho.mqtt.client as mqtt
import numpy as np
import pickle

MQTT_BROKER_ADDRESS = "localhost" #"robud.local"
MQTT_CLIENT_NAME = "robud_face_controller.py"

def on_message_face_keyframes(client,userdata,message):
    #decode message (should be list of keyframe objects)
    keyframes:list = pickle.loads(message.payload)
    face_expression:np.ndarray = userdata["face_expression"]
    sleep(1)
    for i in range(0,len(keyframes)):
        keyframe:face_keyframe = keyframes[i]  
        run_animation(
            mqtt_client=client,
            current_face_expression=face_expression,
            new_left_expression=keyframe.left_expression,
            new_right_expression=keyframe.right_expression,
            new_position=keyframe.position,
            duration=keyframe.duration
            )

def robud_face_controller():
    face_expression = np.zeros(shape=FACE_EXPRESSION_ARRAY_SIZE, dtype=np.int16)
    client_userdata = {
        "face_expression":face_expression,
    }
    set_expression(face_expression, Expressions[ExpressionId.OPEN])
    selected_expression = Expressions[ExpressionId.OPEN]
    selected_right_expression = None
    selected_position = None
    
    #initialize mqtt client
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start()
    print('MQTT Client Connected')
    # mqtt_client.subscribe(TOPIC_FACE_KEYFRAMES)
    # mqtt_client.message_callback_add(TOPIC_FACE_KEYFRAMES,on_message_face_keyframes)
    # print('Subcribed to', TOPIC_FACE_KEYFRAMES)

    while True:
            expression_choice = input(
                    "Choose an Expression:\n"
                    + "[0] Quit\t\t\t"          + "[w] Up\n"
                    + "[1] Open\t\t\t"          + "[s] Down\n"
                    + "[2] Happy\t\t\t"         + "[a] Left\n"
                    + "[3] Overjoyed\t\t\t"     + "[d] Right\n"
                    + "[4] Bored\n"
                    + "[5] Angry\n"
                    + "[6] Skeptical\n"
                    + "?: "
            )
            try: 
                assert re.match(
                    '^[0123456wasd]$',expression_choice
                ) is not None
            except (ValueError, AssertionError):
                print("Invalid Entry")
                #exit()

            if expression_choice == "0": #quit
                exit()
            
            elif expression_choice == "1": #open
                print("Open chosen.")
                selected_expression = Expressions[ExpressionId.OPEN]
                selected_right_expression = None
            
            elif expression_choice == "2": #happy
                print("Happy chosen.")
                selected_expression = Expressions[ExpressionId.HAPPY]
                selected_right_expression = None
        
            elif expression_choice == "3": #overjoyed
                print("Overjoyed chosen.")
                selected_expression = Expressions[ExpressionId.OVERJOYED]
                selected_right_expression = None
            
            elif expression_choice == "4": #bored
                print("Bored chosen.")
                selected_expression = Expressions[ExpressionId.BORED]
                selected_right_expression = None

            elif expression_choice == "5": #angry
                print("Angry chosen.")
                selected_expression = Expressions[ExpressionId.ANGRY]
                selected_right_expression = None

            elif expression_choice == "6": #skeptical
                print("Skeptical chosen.")
                selected_expression = Expressions[ExpressionId.SKEPTICAL_LEFT]
                selected_right_expression = Expressions[ExpressionId.SKEPTICAL_RIGHT]

            elif expression_choice == "w": 
                print("up")
                face_expression[CENTER_Y_OFFSET] -= 100
                selected_position = (
                    face_expression[CENTER_X_OFFSET],
                    face_expression[CENTER_Y_OFFSET]
                    )
            elif expression_choice == "s": 
                print("down")
                face_expression[CENTER_Y_OFFSET] += 100
                selected_position = (
                    face_expression[CENTER_X_OFFSET],
                    face_expression[CENTER_Y_OFFSET]
                    )
            elif expression_choice == "a": 
                print("left")
                face_expression[CENTER_X_OFFSET] -= 50
                selected_position = (
                    face_expression[CENTER_X_OFFSET],
                    face_expression[CENTER_Y_OFFSET] 
                    )
            elif expression_choice == "d": 
                print("right")
                face_expression[CENTER_X_OFFSET] += 50
                selected_position = (
                    face_expression[CENTER_X_OFFSET],
                    face_expression[CENTER_Y_OFFSET] 
                    )
            #put the animation in a keyframe and send it!
            keyframe = face_keyframe(
                left_expression=selected_expression,
                right_expression=selected_right_expression,
                position=selected_position,
                duration=EXPRESSION_CHANGE_DURATION
            )
            #add the keyframe to a list
            keyframes = [keyframe]

            #publish it!
            mqtt_client.publish(TOPIC_FACE_KEYFRAMES,pickle.dumps(keyframes),qos=2)
          

   

    
if __name__ == '__main__':
    robud_face_controller()

