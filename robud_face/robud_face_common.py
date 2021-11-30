import pygame
from time import time, sleep
import pytweening
import numpy as np
import paho.mqtt.client as mqtt

#CONFIG CONSTANTS
ROBUD_EYE_SPACING = 50
SCREENWIDTH = 800
SCREENHEIGHT = 480
BLINK_DURATION = 200
MINIMUM_BLINK_DELAY = 500
AVG_BLINK_DELAY = 3000
ANIMATION_FPS = 60

EXPRESSION_CHANGE_DURATION = 0.2
EYE_MOVEMENT_DURATION = 0.1
PYTWEENING_S = 3

TOPIC_FACE_ANIMATION_FRAME = 'robud/robud_face/animation_frame'
TOPIC_FACE_KEYFRAMES = 'robud/robud_face/keyframes'
TOPIC_FACE_ENABLE_BLINK = 'robud/robud_face/enable_blink'
#TOPIC_HEAD_SERVO_ANGLE = 'robud/motors/head_servo/angle'

#Face Expression Array Constants
LEFT_TOP_FLAT_LID_X         = 0
LEFT_TOP_FLAT_LID_Y         = 1
LEFT_BOTTOM_FLAT_LID_X      = 2
LEFT_BOTTOM_FLAT_LID_Y      = 3
LEFT_ROUND_LID_X            = 4
LEFT_ROUND_LID_Y            = 5
RIGHT_TOP_FLAT_LID_X        = 6
RIGHT_TOP_FLAT_LID_Y        = 7
RIGHT_BOTTOM_FLAT_LID_X     = 8
RIGHT_BOTTOM_FLAT_LID_Y     = 9
RIGHT_ROUND_LID_X           = 10
RIGHT_ROUND_LID_Y           = 11
CENTER_X_OFFSET             = 12
CENTER_Y_OFFSET             = 13 
HEAD_SERVO_ANGLE            = 14
FACE_EXPRESSION_ARRAY_SIZE  = 15

#ExpressionId Enum Class
class ExpressionId():
        OPEN = 0
        BLINKING = 1
        HAPPY = 2
        OVERJOYED = 3
        SAD = 4
        ANGRY = 5
        SCARED = 6
        BORED = 7
        SKEPTICAL_LEFT = 8
        SKEPTICAL_RIGHT = 9

#ExpressionCoordinates class as container for the coordinates of an eye
class ExpressionCoordinates():
        HIDDEN = (-9999,-9999)
        def __init__ (self,
            top_flat_lid = HIDDEN, 
            bottom_flat_lid = HIDDEN,
            round_lid = HIDDEN
            ):
            self.top_flat_lid = top_flat_lid
            self.bottom_flat_lid = bottom_flat_lid
            self.round_lid = round_lid

#Dictionary of Pre-Set Expressions
Expressions = {
           ExpressionId.OPEN: ExpressionCoordinates(
                top_flat_lid = (-50,-250)
                ,bottom_flat_lid = (-50,250)
                ,round_lid = (-50,250)
            )
            , ExpressionId.HAPPY: ExpressionCoordinates(
                top_flat_lid = (-50,-250)
                ,bottom_flat_lid = (-50,175)
                ,round_lid = (-50,150)
            )  
            , ExpressionId.BLINKING: ExpressionCoordinates(
                top_flat_lid = (-50,-130)
                ,bottom_flat_lid = (-50,130)
                ,round_lid = (-50,130),
            )          
            , ExpressionId.OVERJOYED: ExpressionCoordinates(
                top_flat_lid = (-50,-250)
                ,bottom_flat_lid = (-50,75)
                ,round_lid = (-50,50)
            )          
            , ExpressionId.BORED: ExpressionCoordinates(
                top_flat_lid = (-50,-130)
                ,bottom_flat_lid = (-50,250)
                ,round_lid = (-50,250)
            )          
            , ExpressionId.ANGRY: ExpressionCoordinates(
                top_flat_lid = (-50,-130)
                ,bottom_flat_lid = (-50,175)
                ,round_lid = (-50,150)
            )
            , ExpressionId.SKEPTICAL_LEFT: ExpressionCoordinates(
                top_flat_lid = (-50,-130)
                ,bottom_flat_lid = (-50,250)
                ,round_lid = (-50,250)
            )       
            , ExpressionId.SKEPTICAL_RIGHT: ExpressionCoordinates(
                top_flat_lid = (-50,-180)
                ,bottom_flat_lid = (-50,250)
                ,round_lid = (-50,250)
            )       
        }

#RobudEye class that keeps track of the state each eye and its lids
class RobudEye():
    def __init__(self,eye_image_path,flat_lid_image_path,round_lid_image_path):
        self.eye_image = pygame.image.load(eye_image_path).convert_alpha()
        self.flat_lid_image = pygame.image.load(flat_lid_image_path).convert_alpha()
        self.round_lid_image = pygame.image.load(round_lid_image_path).convert_alpha()
        self.image = pygame.Surface((self.eye_image.get_width(),self.eye_image.get_height()))
        self.rect = self.image.get_rect()       
        self.expression = Expressions[ExpressionId.OPEN]
        self.last_expression = None 

    def update(self):
        #clear the eye
        self.image.fill(pygame.Color(0,0,0,0))
        #get the base eye
        self.image.blits((
            (self.eye_image,(0,0)),
            (self.flat_lid_image, self.expression.top_flat_lid),        
            (self.flat_lid_image, self.expression.bottom_flat_lid),
            (self.round_lid_image, self.expression.round_lid)        
        ))

#AnimatedValue calculates a tweened numeric value based on the start & end values, duration, start time, and current time.
class AnimatedValue():
    def __init__ (
        self,
        start_value = 0, 
        end_value = 0,
        duration = 0 ,
        start_time = time(),
        animation_function = pytweening.easeInOutSine,
        pytweening_s = None

    ):
        self.start_value = start_value
        self.end_value = end_value
        self.duration = duration
        self.start_time = start_time
        self.animation_function = animation_function
        self.pytweening_s = pytweening_s
    
    def get_updated_value(self):
        time_since_animation_start = time() - self.start_time
        if time_since_animation_start >= self.duration:
            return self.end_value
        else:
            animation_percent_complete = time_since_animation_start/self.duration
            tween_modifier = None
            if (
                self.animation_function in [pytweening.easeInOutBack, pytweening.easeInBack, pytweening.easeOutBack]
                and self.pytweening_s is not None
            ):
                tween_modifier = self.animation_function(n = animation_percent_complete, s = self.pytweening_s)
            else:
                tween_modifier = self.animation_function(n = animation_percent_complete)
            return int(
                self.start_value
                + tween_modifier 
                * (self.end_value - self.start_value)
            )
#keyframe: face expression array with duration representing time in seconds we want it to take to complete this expression
class face_keyframe():
    def __init__(
        self
        ,left_expression:ExpressionCoordinates
        ,right_expression:ExpressionCoordinates
        ,position:tuple
        ,duration:float
        #,head_servo_angle:int = None
    ) -> None:
        self.left_expression = left_expression
        self.right_expression = right_expression
        self.position = position
        self.duration = duration
        #self.head_servo_angle = head_servo_angle

#updates face_expression array with new coordinates
def set_expression(face_expression:np.ndarray, left_expression_coordinates:ExpressionCoordinates, right_expression_coordinates:ExpressionCoordinates = None):
    if right_expression_coordinates is None:
        right_expression_coordinates = left_expression_coordinates
    face_expression[LEFT_BOTTOM_FLAT_LID_X] = left_expression_coordinates.bottom_flat_lid[0]
    face_expression[LEFT_BOTTOM_FLAT_LID_Y] = left_expression_coordinates.bottom_flat_lid[1]
    face_expression[RIGHT_BOTTOM_FLAT_LID_X] = right_expression_coordinates.bottom_flat_lid[0]
    face_expression[RIGHT_BOTTOM_FLAT_LID_Y] = right_expression_coordinates.bottom_flat_lid[1]
    face_expression[LEFT_TOP_FLAT_LID_X] = left_expression_coordinates.top_flat_lid[0]
    face_expression[LEFT_TOP_FLAT_LID_Y] = left_expression_coordinates.top_flat_lid[1]
    face_expression[RIGHT_TOP_FLAT_LID_X] = right_expression_coordinates.top_flat_lid[0]
    face_expression[RIGHT_TOP_FLAT_LID_Y] = right_expression_coordinates.top_flat_lid[1]
    face_expression[LEFT_ROUND_LID_X] = left_expression_coordinates.round_lid[0]
    face_expression[LEFT_ROUND_LID_Y] = left_expression_coordinates.round_lid[1]
    face_expression[RIGHT_ROUND_LID_X] = right_expression_coordinates.round_lid[0]
    face_expression[RIGHT_ROUND_LID_Y] = right_expression_coordinates.round_lid[1]

#publishes animation frames to transition to new_left_expression & new_right_expression
def run_animation(
    mqtt_client:mqtt.Client,
    current_face_expression:np.ndarray,
    new_left_expression:ExpressionCoordinates,
    new_right_expression:ExpressionCoordinates = None,
    new_position = None,
    #new_head_servo_angle:int = None,
    duration = EXPRESSION_CHANGE_DURATION
    ):
    
    face_expression = current_face_expression
    #set last face expression to current frame
    last_face_expression = face_expression.copy()
    
    #if no new right expression is included default right eye to match left eye
    if new_right_expression == None:
        new_right_expression = new_left_expression

    #set the new expression values in the face expression array
    set_expression(face_expression,new_left_expression, new_right_expression)
    
    #if the position is changing set those as well in face expression array
    if new_position is not None:
        face_expression[CENTER_X_OFFSET] = new_position[0]
        face_expression[CENTER_Y_OFFSET] = new_position[1]
    
    #if the head servo angle is changing set that as well in the face expression arrary
    #if new_head_servo_angle is not None:
    #    face_expression[HEAD_SERVO_ANGLE] = new_head_servo_angle  
    
    #get the start time of the entire animation
    animation_start_time = time()

    #create array to hold animated values for each expression array value
    face_expression_animated_values = [None] * FACE_EXPRESSION_ARRAY_SIZE
    for i in range(0,FACE_EXPRESSION_ARRAY_SIZE):
        face_expression_animated_values[i] = AnimatedValue(
            start_value=last_face_expression[i],
            end_value=face_expression[i],
            duration=duration,
            start_time=animation_start_time,
            animation_function=pytweening.easeInOutQuad,
            pytweening_s = PYTWEENING_S
        )

    #use back tween for y values
    face_expression_animated_values[LEFT_BOTTOM_FLAT_LID_Y].animation_function = pytweening.easeInOutBack
    face_expression_animated_values[LEFT_TOP_FLAT_LID_Y].animation_function = pytweening.easeInOutBack
    face_expression_animated_values[LEFT_ROUND_LID_Y].animation_function = pytweening.easeInOutBack
    face_expression_animated_values[RIGHT_BOTTOM_FLAT_LID_Y].animation_function = pytweening.easeInOutBack
    face_expression_animated_values[RIGHT_TOP_FLAT_LID_Y].animation_function = pytweening.easeInOutBack
    face_expression_animated_values[RIGHT_ROUND_LID_Y].animation_function = pytweening.easeInOutBack
    
    #eye position movement settings
    face_expression_animated_values[CENTER_Y_OFFSET].animation_function = pytweening.easeOutBack
    face_expression_animated_values[CENTER_X_OFFSET].animation_function = pytweening.easeOutBack
    
    #head servo movement settings
    #face_expression_animated_values[HEAD_SERVO_ANGLE].animation_function = pytweening.easeOutBack

    while(time()-animation_start_time <= duration):
        loopstart = time()
        for i in range(0,FACE_EXPRESSION_ARRAY_SIZE):
            face_expression[i] = face_expression_animated_values[i].get_updated_value()
        face_expression_bytes = face_expression.tobytes()
        mqtt_client.publish(TOPIC_FACE_ANIMATION_FRAME,face_expression_bytes,qos=2)
        #if face_expression[HEAD_SERVO_ANGLE] != None:
        #    print (face_expression[HEAD_SERVO_ANGLE])
        #    mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE,int(face_expression[HEAD_SERVO_ANGLE]),qos=2)

        loop_duration = time() - loopstart
        if loop_duration < 1/ANIMATION_FPS:
            sleep(1/ANIMATION_FPS - loop_duration)
    if new_left_expression is not None:
        set_expression(face_expression,new_left_expression, new_right_expression)
        face_expression_bytes = face_expression.tobytes()
    mqtt_client.publish(TOPIC_FACE_ANIMATION_FRAME,face_expression_bytes,qos=2)
    return face_expression
   