import sys, select, tty, termios
import paho.mqtt.client as mqtt
import time
import pygame
import pickle
from robud.robud_face.robud_face_common import *

HEAD_SERVO_MAX_ANGLE = 170
HEAD_SERVO_MIN_ANGLE = 60
SCREENHEIGHT = 320
SCREENWIDTH = 640
MOTOR_SPEED_BASE = 1
MOTOR_SPEED_ACCELERATED = 0.8
MOTOR_SPEED_MIN = 0.2
HEAD_ANGLE_CHANGE = 2
HEAD_ANGLE_MAX = 180
HEAD_ANGLE_MIN = 10
MAX_VEERAGE = 10
MQTT_BROKER_ADDRESS = "robud.local"
MQTT_CLIENT_NAME = "robud_utils_keyboard_controller.py"
TOPIC_MOTOR_LEFT_THROTTLE = 'robud/motors/motor_left/throttle'
TOPIC_MOTOR_RIGHT_THROTTLE = 'robud/motors/motor_right/throttle'
TOPIC_HEAD_SERVO_ANGLE = 'robud/motors/head_servo/angle'
TOPIC_ORIENTATION_HEADING = 'robud/sensors/orientation/heading'
#TOPIC_ODOMETRY_LEFT_TICKS = "robud/sensors/odometry/left/ticks"
#TOPIC_ODOMETRY_LEFT_TICKSPEED = "robud/sensors/odometry/left/tickspeed"
#TOPIC_ODOMETRY_RIGHT_TICKS = "robud/sensors/odometry/right/ticks"
#TOPIC_ODOMETRY_RIGHT_TICKSPEED = "robud/sensors/odometry/right/tickspeed"

def on_heading_message(client, userdata, message):
        if message.topic == TOPIC_ORIENTATION_HEADING:
            userdata["heading"] = int(float(message.payload))
        # elif message.topic == TOPIC_ODOMETRY_LEFT_TICKSPEED:
        #     userdata["left_tickspeed"] = float(message.payload)
        # elif message.topic == TOPIC_ODOMETRY_RIGHT_TICKSPEED:
        #     userdata["right_tickspeed"] = float(message.payload)
        # elif message.topic == TOPIC_ODOMETRY_RIGHT_TICKS:
        #     userdata["right_ticks"] = int(message.payload)
        # elif message.topic == TOPIC_ODOMETRY_RIGHT_TICKS:
        #     userdata["left_ticks"] = int(message.payload)


if __name__ == '__main__':
    rate = 100 #100hz rate for sending messages
    carry_on = True
    client_userdata = {"heading":0}
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME, userdata=client_userdata)
    stopped=True
    target_heading = 0

    def move_forward(stopped,target_heading):
        left_speed = MOTOR_SPEED_BASE
        right_speed = MOTOR_SPEED_BASE
        current_heading = int(client_userdata["heading"])
        #right_tickspeed = float(client_userdata["left_tickspeed"])
        #left_tickspeed = float(client_userdata["right_tickspeed"])
        # if stopped:
        #     target_heading = current_heading
        # # elif left_tickspeed != right_tickspeed:
        # #     veerage = abs(left_tickspeed - right_tickspeed)
        # #     max_speed_change = MOTOR_SPEED_BASE - MOTOR_SPEED_MIN
        # #     if veerage > MAX_VEERAGE:
        # #         veerage_pct = 1
        # #     else:
        # #         veerage_pct = veerage/MAX_VEERAGE
        # #     if left_tickspeed > right_tickspeed:
        # #         left_speed = MOTOR_SPEED_BASE - (max_speed_change * veerage_pct)
        # #     elif right_tickspeed > left_tickspeed:
        # #         right_speed = MOTOR_SPEED_BASE - (max_speed_change * veerage_pct)
        # elif current_heading != target_heading: 
        #     #veering to the right, add more power to right wheel
        #     veerage = abs(target_heading-current_heading)
        #     max_speed_change = MOTOR_SPEED_ACCELERATED - MOTOR_SPEED_BASE
        #     if veerage > 180: # e.g. 355 & 5
        #         veerage = abs(360-veerage)
        #         current_heading *= -1
        #         target_heading *= -1
        #     if veerage > MAX_VEERAGE:
        #         veerage_pct = 1
        #     else:
        #         veerage_pct = veerage/MAX_VEERAGE

        #     if current_heading > target_heading:              
        #         right_speed = MOTOR_SPEED_BASE + (max_speed_change * veerage_pct)
        #     elif current_heading < target_heading:
        #         #veering to the left, add more power to left wheel
        #         left_speed = MOTOR_SPEED_BASE + (max_speed_change * veerage_pct)
        print("move forward: target_heading:{}".format(target_heading))
        stopped = False
        mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, left_speed)
        mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, right_speed)
        return stopped, target_heading

    def move_backward(stopped):
        print("move backward")
        stopped = False
        mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, -1 * MOTOR_SPEED_BASE)
        mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, -1 * MOTOR_SPEED_BASE)
        return stopped
    def turn_right(stopped):
        print("turn right")
        stopped = False
        mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, MOTOR_SPEED_BASE)
        mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, -1 * MOTOR_SPEED_BASE)
        return stopped
    def turn_left(stopped):
        print("turn left")
        stopped = False
        mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, -1 * MOTOR_SPEED_BASE)
        mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, MOTOR_SPEED_BASE)
        return stopped
    def stop(stopped):
        print("stop", target_heading)
        stopped = True
        mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, 0)
        mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, 0)
        return stopped
    def look_up(head_angle):
        print("look up")
        new_angle = head_angle + HEAD_ANGLE_CHANGE
        if new_angle >= HEAD_ANGLE_MAX: 
            new_angle = HEAD_ANGLE_MAX
        head_angle = new_angle
        mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE, head_angle,retain=True)
        return head_angle

    def look_down(head_angle):
        print("look down")
        new_angle = head_angle - HEAD_ANGLE_CHANGE
        if new_angle <= HEAD_ANGLE_MIN:
            new_angle = HEAD_ANGLE_MIN 
        head_angle = new_angle
        mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE, head_angle,retain=True)
        return head_angle
    
    def move_eyes(
        face_expression, 
        left_expression:ExpressionCoordinates, 
        right_expression:ExpressionCoordinates, 
        selected_position:tuple,
        change_expression:bool,
        #head_angle:int,
        mqtt_client:mqtt.Client):    
        if (
            change_expression
            or
            face_expression[CENTER_X_OFFSET] != selected_position[0]
            or 
            face_expression[CENTER_Y_OFFSET] != selected_position[1]
            #or
            #face_expression[HEAD_SERVO_ANGLE] != head_angle
            ):
            face_expression[CENTER_X_OFFSET] = selected_position[0]
            face_expression[CENTER_Y_OFFSET] = selected_position[1]
            #face_expression[HEAD_SERVO_ANGLE] = head_angle
            
            #put the animation in a keyframe and send it!
            keyframe = face_keyframe(
                left_expression=left_expression,
                right_expression=right_expression,
                position=selected_position,
                duration=EXPRESSION_CHANGE_DURATION
                #head_servo_angle=None
            )
            #add the keyframe to a list
            keyframes = [keyframe]

            #publish it!
            mqtt_client.publish(TOPIC_FACE_KEYFRAMES,pickle.dumps(keyframes),qos=2)
            change_expression = False
        return face_expression, change_expression

    pygame.init()
    clock = pygame.time.Clock()
    screensize = (SCREENWIDTH, SCREENHEIGHT)
    screen = pygame.display.set_mode(screensize)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start()
    head_angle = 75
    mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE, head_angle)
    mqtt_client.subscribe(TOPIC_ORIENTATION_HEADING)
    #mqtt_client.subscribe(TOPIC_ODOMETRY_LEFT_TICKSPEED)
    #mqtt_client.subscribe(TOPIC_ODOMETRY_RIGHT_TICKSPEED)
    mqtt_client.on_message=on_heading_message
    
    #init face expression
    face_expression = np.zeros(shape=FACE_EXPRESSION_ARRAY_SIZE, dtype=np.int16)
    set_expression(face_expression, Expressions[ExpressionId.OPEN])
    selected_expression = Expressions[ExpressionId.OPEN]
    left_expression:ExpressionCoordinates = Expressions[ExpressionId.OPEN]
    right_expression:ExpressionCoordinates = Expressions[ExpressionId.OPEN]
    position_left = 50
    position_right = -50
    position_center = 0
    position_up = -50
    position_down = 50
    selected_position = (position_center,position_center)
    change_expression:bool = False

    while carry_on:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                carry_on = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    print("pressed CTRL-C as an event")
                    carry_on = False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            stopped, target_heading = move_forward(stopped, target_heading)
        elif keys[pygame.K_DOWN]:
            stopped = move_backward(stopped)
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            stopped = turn_left(stopped)
            #look left
            selected_position = (
                    position_left,
                    selected_position[1]
                    )
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            stopped = turn_right(stopped)
            #look right
            selected_position = (
                    position_right,
                    selected_position[1]
                    )
        else:
            stopped = stop(stopped)
            #center eyes
            selected_position = (
                    position_center,
                    selected_position[1]
                    )
        if keys[pygame.K_w]:
            head_angle = look_up(head_angle)
            #look up
            selected_position = (
                    selected_position[0],
                    position_up
                    )
        elif keys[pygame.K_s]:
            head_angle = look_down(head_angle)
            #look down
            selected_position = (
                    selected_position[0],
                    position_down
                    )
        else:
            #look center
            selected_position = (
                    selected_position[0],
                    position_center
                    )
        if keys[pygame.K_1] or keys[pygame.K_KP1]:
            if left_expression != Expressions[ExpressionId.OPEN] and right_expression != Expressions[ExpressionId.OPEN]:
                left_expression = Expressions[ExpressionId.OPEN]
                right_expression = Expressions[ExpressionId.OPEN]
                change_expression = True
        if keys[pygame.K_2] or keys[pygame.K_KP2]:
            if left_expression != Expressions[ExpressionId.HAPPY] and right_expression != Expressions[ExpressionId.HAPPY]:
                left_expression = Expressions[ExpressionId.HAPPY]
                right_expression = Expressions[ExpressionId.HAPPY]
                change_expression = True
        if keys[pygame.K_3] or keys[pygame.K_KP3]:
            if left_expression != Expressions[ExpressionId.OVERJOYED] and right_expression != Expressions[ExpressionId.OVERJOYED]:
                left_expression = Expressions[ExpressionId.OVERJOYED]
                right_expression = Expressions[ExpressionId.OVERJOYED]
                change_expression = True
        if keys[pygame.K_4] or keys[pygame.K_KP4]:
            if left_expression != Expressions[ExpressionId.BORED] and right_expression != Expressions[ExpressionId.BORED]:
                left_expression = Expressions[ExpressionId.BORED]
                right_expression = Expressions[ExpressionId.BORED]
                change_expression = True
        if keys[pygame.K_5] or keys[pygame.K_KP5]:
            if left_expression != Expressions[ExpressionId.ANGRY] and right_expression != Expressions[ExpressionId.ANGRY]:
                left_expression = Expressions[ExpressionId.ANGRY]
                right_expression = Expressions[ExpressionId.ANGRY]
                change_expression = True
        if keys[pygame.K_6] or keys[pygame.K_KP6]:
            if left_expression != Expressions[ExpressionId.SKEPTICAL_LEFT] and right_expression != Expressions[ExpressionId.SKEPTICAL_RIGHT]:
                left_expression = Expressions[ExpressionId.SKEPTICAL_LEFT]
                right_expression = Expressions[ExpressionId.SKEPTICAL_RIGHT]
                change_expression = True
        face_expression, change_expression = move_eyes(
                face_expression = face_expression,
                left_expression = left_expression,
                right_expression = right_expression,
                selected_position = selected_position,
                change_expression = change_expression,
                #head_angle = head_angle,
                mqtt_client = mqtt_client
                )
        clock.tick(rate)
"Exiting"
pygame.quit()
exit()                
