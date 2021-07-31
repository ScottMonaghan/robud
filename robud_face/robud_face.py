import pytweening
import pygame 
import random
import os
from robud_face_common import *
import paho.mqtt.client as mqtt
import numpy as np

MQTT_BROKER_ADDRESS = "localhost"
MQTT_CLIENT_NAME = "robud_face.py"
            
#RobudFace contains both RobudEyes as well as the rotation of the face. It also keeps track of blinking.
class RobudFace():
    def __init__(self,eye_image_path,flat_lid_image_path,round_lid_image_path):
        self.right_eye = RobudEye(eye_image_path,flat_lid_image_path,round_lid_image_path)
        self.left_eye = RobudEye(eye_image_path,flat_lid_image_path,round_lid_image_path)
        self.image = pygame.Surface((self.right_eye.image.get_width() * 2 + ROBUD_EYE_SPACING,self.right_eye.image.get_height()))
        self.rotated_image = None
        self.rect = self.image.get_rect()
        self.rect.x = int(SCREENWIDTH/2 - self.image.get_width()/2)
        self.rect.y = int(SCREENHEIGHT/2 - self.image.get_height()/2)
        self.is_blinking = False
        self.blink_start = None
        self.last_blink = 0
        self.rotation = 0
        self.center_x_offset = 0
        self.center_y_offset = 0

    def update(self):
        self.right_eye.update()
        self.left_eye.update()
        self.image.blits((
            (self.left_eye.image, (0,0)),
            (self.right_eye.image, (self.left_eye.image.get_width() + ROBUD_EYE_SPACING,0))
        ))
        self.rotated_image = pygame.transform.rotate(self.image,self.rotation)
    
    def blink(self):
        current_time = pygame.time.get_ticks()
        open_top = -250
        open_bottom = 250

        if not self.is_blinking: 
            if current_time - self.last_blink > MINIMUM_BLINK_DELAY: 
                if random.random() < MINIMUM_BLINK_DELAY / AVG_BLINK_DELAY:
                    #if blink fires, go staight to closed eyes (no animation)
                    self.is_blinking = True
                    self.left_eye.last_expression = self.left_eye.expression
                    self.right_eye.last_expression = self.right_eye.expression
                    self.left_eye.expression = Expressions[ExpressionId.BLINKING] 
                    self.right_eye.expression = Expressions[ExpressionId.BLINKING] 
                self.last_blink = pygame.time.get_ticks()
        elif current_time - self.last_blink >= BLINK_DURATION/2 and current_time - self.last_blink < BLINK_DURATION:
            #to smooth the blink effect, we animate the opening of the eyes 
            #if we're halfway through the BLINK_DURATION it's time to start animating

            #get time since last blink, taking into acound the BLINK progressed
            time_since_blink_start = current_time - self.last_blink + BLINK_DURATION/2
            
            #figure out the percentage of animation that we should be showing for this frame
            animation_percentage = pytweening.easeOutSine(time_since_blink_start/BLINK_DURATION/2) 
            
            #figure out the total animation distance to travel for each of the lids to complete the blink and return to the previous expression
            top_left_total_distance_to_travel = self.left_eye.last_expression.top_flat_lid[1] - Expressions[ExpressionId.BLINKING].top_flat_lid[1]
            top_right_total_distance_to_travel = self.right_eye.last_expression.top_flat_lid[1] - Expressions[ExpressionId.BLINKING].top_flat_lid[1]
            bottom_left_total_distance_to_travel = self.left_eye.last_expression.bottom_flat_lid[1] - Expressions[ExpressionId.BLINKING].bottom_flat_lid[1]
            bottom_right_total_distance_to_travel = self.right_eye.last_expression.bottom_flat_lid[1] - Expressions[ExpressionId.BLINKING].bottom_flat_lid[1]
            left_cheek_total_distance_to_travel = self.left_eye.last_expression.round_lid[1] - Expressions[ExpressionId.BLINKING].round_lid[1]
            right_cheek_total_distance_to_travel = self.right_eye.last_expression.round_lid[1] - Expressions[ExpressionId.BLINKING].round_lid[1]
            
            #calculate the coordinates of the lids 
            top_left_animated = (-50, Expressions[ExpressionId.BLINKING].top_flat_lid[1] + int(animation_percentage * top_left_total_distance_to_travel))
            bottom_left_animated = (-50, Expressions[ExpressionId.BLINKING].bottom_flat_lid[1] + int(animation_percentage * bottom_left_total_distance_to_travel))
            left_cheek_animated = (-50,Expressions[ExpressionId.BLINKING].round_lid[1] + int(animation_percentage * left_cheek_total_distance_to_travel))
            top_right_animated = (-50, Expressions[ExpressionId.BLINKING].top_flat_lid[1] + int(animation_percentage * top_right_total_distance_to_travel))
            bottom_right_animated = (-50, Expressions[ExpressionId.BLINKING].bottom_flat_lid[1] + int(animation_percentage * bottom_right_total_distance_to_travel))
            right_cheek_animated = (-50,Expressions[ExpressionId.BLINKING].round_lid[1] + int(animation_percentage * right_cheek_total_distance_to_travel))
            
            #set the coordinates of the lids for each eye
            self.left_eye.expression = ExpressionCoordinates( top_flat_lid = top_left_animated, bottom_flat_lid = bottom_left_animated, round_lid=left_cheek_animated)
            self.right_eye.expression = ExpressionCoordinates( top_flat_lid = top_right_animated, bottom_flat_lid = bottom_right_animated, round_lid=right_cheek_animated)
        elif current_time - self.last_blink > BLINK_DURATION:            
            #if the total blink duration has completed return the pre-blink expression
            self.is_blinking = False
            self.left_eye.expression = self.left_eye.last_expression
            self.right_eye.expression = self.right_eye.last_expression
            self.left_eye.last_expression = None
            self.right_eye.last_expression = None



#applies a face expression
def apply_face_expression(robud_face:RobudFace, face_expression):
    robud_face.left_eye.expression = ExpressionCoordinates(
        top_flat_lid = (
            face_expression[LEFT_TOP_FLAT_LID_X],
            face_expression[LEFT_TOP_FLAT_LID_Y]
        )
        ,round_lid = (
            face_expression[LEFT_ROUND_LID_X],
            face_expression[LEFT_ROUND_LID_Y]
        )
        ,bottom_flat_lid = (
            face_expression[LEFT_BOTTOM_FLAT_LID_X],
            face_expression[LEFT_BOTTOM_FLAT_LID_Y]            
        ) 
    )

    robud_face.right_eye.expression = ExpressionCoordinates(
        top_flat_lid = (
            face_expression[RIGHT_TOP_FLAT_LID_X],
            face_expression[RIGHT_TOP_FLAT_LID_Y]
        )
        ,round_lid = (
            face_expression[RIGHT_ROUND_LID_X],
            face_expression[RIGHT_ROUND_LID_Y]
        )
        ,bottom_flat_lid = (
            face_expression[RIGHT_BOTTOM_FLAT_LID_X],
            face_expression[RIGHT_BOTTOM_FLAT_LID_Y]            
        ) 
    )

    robud_face.center_x_offset = face_expression[CENTER_X_OFFSET]
    robud_face.center_y_offset = face_expression[CENTER_Y_OFFSET]

def on_message_animation_frame(client, userdata, message):
    #get the pointer to the main face_expression arrary
    face_expression = userdata["face_expression"]
    #get the new face expression from the buffer
    new_face_expression = np.frombuffer(buffer=message.payload,dtype=np.int16)
    #replace face expression with new values
    for i in range(0,FACE_EXPRESSION_ARRAY_SIZE):
        face_expression[i] = new_face_expression[i]
    

def main():
    #set initial expression to basic open
    face_expression = np.zeros(shape=FACE_EXPRESSION_ARRAY_SIZE, dtype=np.int16)
    set_expression(face_expression, Expressions[ExpressionId.OPEN])

    #initialize mqtt client
    client_userdata = {
        "face_expression":face_expression,
    }
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start()
    print('MQTT Client Connected')
    mqtt_client.subscribe(TOPIC_FACE_ANIMATION_FRAME)
    mqtt_client.message_callback_add(TOPIC_FACE_ANIMATION_FRAME,on_message_animation_frame)
    print('Subcribed to', TOPIC_FACE_ANIMATION_FRAME)
    
    #initiaize randomizer
    random.seed()
    #initialize pygame
    pygame.init()
    #remove cursor from screen
    pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))

    #set screensize
    screensize = (SCREENWIDTH, SCREENHEIGHT)
    #update the display mode
    screen = pygame.display.set_mode(screensize,pygame.FULLSCREEN)
    #get script dir for local file paths
    script_dir = os.path.dirname(__file__)
    #initilialize the face object
    robud_face = RobudFace(
        os.path.join(script_dir,"robud_eye.png"),
        os.path.join(script_dir,"robud_flat_lid.png"),
        os.path.join(script_dir,"robud_round_lid.png")
    )
    
    clock = pygame.time.Clock()
    #set initial face angle to neutral
    face_angle = 0

    #loop control variable
    carry_on = True

    while carry_on:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                carry_on = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                #Quit on CTRL-C
                    print("pressed CTRL-C as an event")
                    carry_on = False
                if event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_CTRL:
                #Toggle fullscreen on CTRL-F
                    print("Toggle Fullscrreen")
                    pygame.display.toggle_fullscreen()
        
        #if not blinking apply the newest face frame
        if face_expression is not None and not robud_face.is_blinking:
            apply_face_expression(robud_face, face_expression)
        
        #fire blink check
        robud_face.blink()
        
        #clear screen and update the face
        screen.fill((0,0,0))
        robud_face.update()

        #Last rotate and re-center if necessary
        screen.blit(robud_face.rotated_image, 
            (
                int(SCREENWIDTH/2 - robud_face.rotated_image.get_width()/2)
                + robud_face.center_x_offset,
                int(SCREENHEIGHT/2 - robud_face.rotated_image.get_height()/2)
                + robud_face.center_y_offset
            )
        )
        #update the display and show next frame
        pygame.display.flip()
 
if __name__ == '__main__':
    main()

pygame.quit()