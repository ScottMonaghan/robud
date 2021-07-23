import pytweening
from time import time
import re
import paho.mqtt.client as mqtt
from io import BytesIO
import numpy as np

EXPRESSION_CHANGE_DURATION = 0.2
EYE_MOVEMENT_DURATION = 0.1
PYTWEENING_S = 3

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
FACE_EXPRESSION_ARRAY_SIZE  = 14

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



def set_expression(face_expression, left_expression_coordinates:ExpressionCoordinates, right_expression_coordinates:ExpressionCoordinates = None):
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

def keys_cb(key_msg, args): 
    face_pub = args["face_pub"]
    rate = args["rate"]
    face_expression = args["face_expression"]
    face_expression_animated_values = args["face_expression_animated_values"]
    last_face_expression = args["last_face_expression"]
    next_face_expression = args["next_face_expression"]
    face_msg = args["face_msg"]
    expression_choice = key_msg.data[0]
    

    #while not rospy.is_shutdown():
    #expression_choice = input(
    print (
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
        #expression_choice = int(expression_choice)
        #assert expression_choice >= 0
        #assert expression_choice <= 15
        assert re.match(
            '^[0123456wasd]$',expression_choice
        ) is not None
    except (ValueError, AssertionError):
        print("Invalid Entry")
        exit()

    selected_expression = None
    selected_right_expression = None
    selected_position = None

    if expression_choice == "0": #quit
        exit()
    
    elif expression_choice == "1": #open
        print("Open chosen.")
        selected_expression = Expressions[ExpressionId.OPEN]

    elif expression_choice == "2": #happy
        print("Happy chosen.")
        selected_expression = Expressions[ExpressionId.HAPPY]
    
    elif expression_choice == "3": #overjoyed
        print("Overjoyed chosen.")
        selected_expression = Expressions[ExpressionId.OVERJOYED]
    
    elif expression_choice == "4": #bored
        print("Bored chosen.")
        selected_expression = Expressions[ExpressionId.BORED]

    elif expression_choice == "5": #angry
        print("Angry chosen.")
        selected_expression = Expressions[ExpressionId.ANGRY]

    elif expression_choice == "6": #skeptical
        print("Skeptical chosen.")
        selected_expression = Expressions[ExpressionId.SKEPTICAL_LEFT]
        selected_right_expression = Expressions[ExpressionId.SKEPTICAL_RIGHT]

    elif expression_choice == "w": 
        print("up")
        selected_position = (
            face_expression[CENTER_X_OFFSET],
            face_expression[CENTER_Y_OFFSET] - 100
            )
    elif expression_choice == "s": 
        print("down")
        selected_position = (
            face_expression[CENTER_X_OFFSET],
            face_expression[CENTER_Y_OFFSET] + 100
            )
    elif expression_choice == "a": 
        print("left")
        selected_position = (
            face_expression[CENTER_X_OFFSET] - 50,
            face_expression[CENTER_Y_OFFSET]
            )
    elif expression_choice == "d": 
        print("right")
        selected_position = (
            face_expression[CENTER_X_OFFSET] + 50,
            face_expression[CENTER_Y_OFFSET] 
            )

    
    last_face_expression = face_expression.copy()
    if selected_expression is not None:
        set_expression(face_expression,selected_expression, selected_right_expression)
    if selected_position is not None:
        face_expression[CENTER_X_OFFSET] = selected_position[0]
        face_expression[CENTER_Y_OFFSET] = selected_position[1]
    animation_start_time = time()
    
    for i in range(0,FACE_EXPRESSION_ARRAY_SIZE):
        face_expression_animated_values[i] = AnimatedValue(
            start_value=last_face_expression[i],
            end_value=face_expression[i],
            duration=EXPRESSION_CHANGE_DURATION,
            start_time=animation_start_time,
            animation_function=pytweening.easeInOutQuad,
            pytweening_s= PYTWEENING_S
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
    face_expression_animated_values[CENTER_X_OFFSET].duration = EYE_MOVEMENT_DURATION
    face_expression_animated_values[CENTER_Y_OFFSET].duration = EYE_MOVEMENT_DURATION

    while(time()-animation_start_time <= EXPRESSION_CHANGE_DURATION):
        for i in range(0,FACE_EXPRESSION_ARRAY_SIZE):
            face_expression[i] = face_expression_animated_values[i].get_updated_value()
        face_pub.publish(face_msg)
        rate.sleep()
    if selected_expression is not None:
        set_expression(face_expression,selected_expression, selected_right_expression)
    face_pub.publish(face_msg)
    rate.sleep()

def robud_face_controller():
    # face_pub = rospy.Publisher('robud_face_expression', Int16MultiArray, queue_size=1)
    # rospy.init_node('rospy_face_controller')
    # rate = rospy.Rate(60) #60hz (fps)
    face_expression =  [0] * FACE_EXPRESSION_ARRAY_SIZE
    face_expression_animated_values = [AnimatedValue()] * FACE_EXPRESSION_ARRAY_SIZE
    last_face_expression = None
    next_face_expression = None
    set_expression(face_expression, Expressions[ExpressionId.OPEN])

    # face_msg = Int16MultiArray()
    # face_msg.data = face_expression
    # face_msg.layout.dim = [MultiArrayDimension()]
    # face_msg.layout.dim[0].label = "face_expression"
    # face_msg.layout.dim[0].size = FACE_EXPRESSION_ARRAY_SIZE
    # face_msg.layout.dim[0].stride = FACE_EXPRESSION_ARRAY_SIZE
    

    # rospy.Subscriber(
    #     'keys', 
    #     String, 
    #     keys_cb, 
    #     {
    #         "face_pub":face_pub, 
    #         "rate":rate, 
    #         "face_expression":face_expression, 
    #         "face_expression_animated_values":face_expression_animated_values,
    #         "last_face_expression":last_face_expression,
    #         "next_face_expression":next_face_expression,
    #         "face_msg":face_msg
    #     }
    #     )
    # rospy.spin()
    # while not rospy.is_shutdown():
    #     expression_choice = input(
    #         "Choose an Expression:\n"
    #         + "[0] Quit\t\t\t"          + "[w] Up\n"
    #         + "[1] Open\t\t\t"          + "[s] Down\n"
    #         + "[2] Happy\t\t\t"         + "[a] Left\n"
    #         + "[3] Overjoyed\t\t\t"     + "[d] Right\n"
    #         + "[4] Bored\n"
    #         + "[5] Angry\n"
    #         + "[6] Skeptical\n"
    #         + "?: "
    #         )
    #     try: 
    #         #expression_choice = int(expression_choice)
    #         #assert expression_choice >= 0
    #         #assert expression_choice <= 15
    #         assert re.match(
    #             '^[0123456wasd]$',expression_choice
    #         ) is not None
    #     except (ValueError, AssertionError):
    #         print("Invalid Entry")
    #         continue

    #     selected_expression = None
    #     selected_right_expression = None
    #     selected_position = None

    #     if expression_choice == "0": #quit
    #         exit()
        
    #     elif expression_choice == "1": #open
    #         print("Open chosen.")
    #         selected_expression = Expressions[ExpressionId.OPEN]

    #     elif expression_choice == "2": #happy
    #         print("Happy chosen.")
    #         selected_expression = Expressions[ExpressionId.HAPPY]
        
    #     elif expression_choice == "3": #overjoyed
    #         print("Overjoyed chosen.")
    #         selected_expression = Expressions[ExpressionId.OVERJOYED]
        
    #     elif expression_choice == "4": #bored
    #         print("Bored chosen.")
    #         selected_expression = Expressions[ExpressionId.BORED]

    #     elif expression_choice == "5": #angry
    #         print("Angry chosen.")
    #         selected_expression = Expressions[ExpressionId.ANGRY]

    #     elif expression_choice == "6": #skeptical
    #         print("Skeptical chosen.")
    #         selected_expression = Expressions[ExpressionId.SKEPTICAL_LEFT]
    #         selected_right_expression = Expressions[ExpressionId.SKEPTICAL_RIGHT]

    #     elif expression_choice == "w": 
    #         print("up")
    #         selected_position = (
    #             face_expression[CENTER_X_OFFSET],
    #             face_expression[CENTER_Y_OFFSET] - 100
    #             )
    #     elif expression_choice == "s": 
    #         print("down")
    #         selected_position = (
    #             face_expression[CENTER_X_OFFSET],
    #             face_expression[CENTER_Y_OFFSET] + 100
    #             )
    #     elif expression_choice == "a": 
    #         print("left")
    #         selected_position = (
    #             face_expression[CENTER_X_OFFSET] - 50,
    #             face_expression[CENTER_Y_OFFSET]
    #             )
    #     elif expression_choice == "d": 
    #         print("right")
    #         selected_position = (
    #             face_expression[CENTER_X_OFFSET] + 50,
    #             face_expression[CENTER_Y_OFFSET] 
    #             )

        
    #     last_face_expression = face_expression.copy()
    #     if selected_expression is not None:
    #         set_expression(face_expression,selected_expression, selected_right_expression)
    #     if selected_position is not None:
    #         face_expression[CENTER_X_OFFSET] = selected_position[0]
    #         face_expression[CENTER_Y_OFFSET] = selected_position[1]
    #     animation_start_time = time()
        
    #     for i in range(0,FACE_EXPRESSION_ARRAY_SIZE):
    #         face_expression_animated_values[i] = AnimatedValue(
    #             start_value=last_face_expression[i],
    #             end_value=face_expression[i],
    #             duration=EXPRESSION_CHANGE_DURATION,
    #             start_time=animation_start_time,
    #             animation_function=pytweening.easeInOutQuad,
    #             pytweening_s= PYTWEENING_S
    #         )

    #     #use back tween for y values
    #     face_expression_animated_values[LEFT_BOTTOM_FLAT_LID_Y].animation_function = pytweening.easeInOutBack
    #     face_expression_animated_values[LEFT_TOP_FLAT_LID_Y].animation_function = pytweening.easeInOutBack
    #     face_expression_animated_values[LEFT_ROUND_LID_Y].animation_function = pytweening.easeInOutBack
    #     face_expression_animated_values[RIGHT_BOTTOM_FLAT_LID_Y].animation_function = pytweening.easeInOutBack
    #     face_expression_animated_values[RIGHT_TOP_FLAT_LID_Y].animation_function = pytweening.easeInOutBack
    #     face_expression_animated_values[RIGHT_ROUND_LID_Y].animation_function = pytweening.easeInOutBack
        
    #     #eye position movement settings
    #     face_expression_animated_values[CENTER_Y_OFFSET].animation_function = pytweening.easeOutBack
    #     face_expression_animated_values[CENTER_X_OFFSET].animation_function = pytweening.easeOutBack
    #     face_expression_animated_values[CENTER_X_OFFSET].duration = EYE_MOVEMENT_DURATION
    #     face_expression_animated_values[CENTER_Y_OFFSET].duration = EYE_MOVEMENT_DURATION

    #     while(time()-animation_start_time <= EXPRESSION_CHANGE_DURATION):
    #         for i in range(0,FACE_EXPRESSION_ARRAY_SIZE):
    #             face_expression[i] = face_expression_animated_values[i].get_updated_value()
    #         pub.publish(msg)
    #         rate.sleep()
    #     if selected_expression is not None:
    #         set_expression(face_expression,selected_expression, selected_right_expression)
    #     pub.publish(msg)
    #     rate.sleep()

    
if __name__ == '__main__':
    #try:
        robud_face_controller()
        #rospy.spin()
    # except rospy.ROSInterruptException:
    #     pass

