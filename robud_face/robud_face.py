import pytweening
import pygame 
import random
import os
from robud.robud_face.robud_face_common import *
import paho.mqtt.client as mqtt
import numpy as np
import time
import random
from robud.robud_logging.MQTTHandler import MQTTHandler
import argparse
import logging
from datetime import datetime
import os
import sys
import traceback


random.seed()

MQTT_BROKER_ADDRESS = "robud.local"
MQTT_CLIENT_NAME = "robud_face.py" + str(random.randint(0,999999999))

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.DEBUG

TOPIC_ROBUD_VOICE_TEXT_INPUT = 'robud/robud_voice/text_input'
CAPTION_TIMEOUT = 20

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/robud_face_log_")
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

try: 
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

    def on_message_tts(client, userdata, message):
        userdata["tts"] = message.payload.decode()
        userdata["tts_time"] = time.monotonic()

    def on_message_enable_blink(client, userdata, message):
        userdata["enable_blink"] = bool(int(message.payload))
   
    # draw some text into an area of a surface
    # automatically wraps words
    # returns any text that didn't get blitted
    def drawText(surface, text, color, rect, font, aa=False, bkg=None):
        rect = pygame.Rect(rect)
        y = rect.top
        lineSpacing = -2

        # get the height of the font
        fontHeight = font.size("Tg")[1]

        while text:
            i = 1

            # determine if the row of text will be outside our area
            if y + fontHeight > rect.bottom:
                break

            # determine maximum width of line
            while font.size(text[:i])[0] < rect.width and i < len(text):
                i += 1

            # if we've wrapped the text, then adjust the wrap to the last word      
            if i < len(text): 
                i = text.rfind(" ", 0, i) + 1

            # render the line and blit it to the surface
            if bkg:
                image = font.render(text[:i], 1, color, bkg)
                image.set_colorkey(bkg)
            else:
                image = font.render(text[:i], aa, color)

            surface.blit(image, (rect.left + ((rect.w - image.get_width())/2 ), y)) #center text
            y += fontHeight + lineSpacing

            # remove the text we just blitted
            text = text[i:]

        return text

    def main():
        #set initial expression to basic open
        face_expression = np.zeros(shape=FACE_EXPRESSION_ARRAY_SIZE, dtype=np.int16)
        set_expression(face_expression, Expressions[ExpressionId.OPEN])

        tts="" #received text-to-speech

        #initialize mqtt client
        client_userdata = {
            "face_expression":face_expression,
            "tts":"",
            "tts_time":0
        }

        mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
        mqtt_client.connect(MQTT_BROKER_ADDRESS)
        mqtt_client.loop_start()
        logger.info('MQTT Client Connected')
        mqtt_client.subscribe(TOPIC_FACE_ANIMATION_FRAME)
        mqtt_client.message_callback_add(TOPIC_FACE_ANIMATION_FRAME,on_message_animation_frame)
        logger.info('Subcribed to' + TOPIC_FACE_ANIMATION_FRAME)
        mqtt_client.subscribe(TOPIC_ROBUD_VOICE_TEXT_INPUT)
        mqtt_client.message_callback_add(TOPIC_ROBUD_VOICE_TEXT_INPUT, on_message_tts)
        logger.info('Subcribed to' + TOPIC_ROBUD_VOICE_TEXT_INPUT)
        mqtt_client.subscribe(TOPIC_FACE_ENABLE_BLINK)
        mqtt_client.message_callback_add(TOPIC_FACE_ENABLE_BLINK, on_message_enable_blink)
        logger.info('Subcribed to' + TOPIC_FACE_ENABLE_BLINK)
        
        #initiaize randomizer
        random.seed()
        #initialize pygame
        pygame.init()
        #remove cursor from screen
        #pygame.event.set_grab(True)
        pygame.mouse.set_visible(False) #set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))

        #set screensize
        screensize = (SCREENWIDTH, SCREENHEIGHT)
        #update the display mode
        screen = pygame.display.set_mode(screensize, pygame.FULLSCREEN)
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

        #set up text display
        font = pygame.font.Font('freesansbold.ttf', 24)
        odom = 0
        client_userdata["enable_blink"]=True
        while carry_on:
            loop_start = time.monotonic()
            enable_blink = client_userdata["enable_blink"]
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    carry_on = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    #Quit on CTRL-C
                        logger.info("pressed CTRL-C as an event")
                        carry_on = False
                    if event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    #Toggle fullscreen on CTRL-F
                        logger.info("Toggle Fullscrreen")
                        pygame.display.toggle_fullscreen()
            
            #if not blinking apply the newest face frame
            if face_expression is not None and not robud_face.is_blinking:
                apply_face_expression(robud_face, face_expression)
            
            #fire blink check
            if enable_blink:
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
            #get relative mouse positions
            # odom += pygame.mouse.get_rel()[1]
            # text = str(odom)
            # text_surface = font.render(text, True, (0, 255, 0), (0, 0, 128))
            # screen.blit(text_surface, text_surface.get_rect())
            if (time.monotonic() - client_userdata["tts_time"] < CAPTION_TIMEOUT):
                tts = client_userdata["tts"]
            else: tts = ""
            margin = 20
            drawText(screen, tts, (255,255,255), ((margin,margin),(SCREENWIDTH-margin*2,SCREENHEIGHT-margin*2)),font,True)
            #tts_surface = font.render(tts, True, (255,255,255))
            
            #screen.blit(tts_surface, ((SCREENWIDTH-tts_surface.get_width())/2,SCREENHEIGHT-tts_surface.get_height()))
            #update the display and show next frame
            pygame.display.flip()
            loop_duration = time.monotonic() - loop_start
            if loop_duration < 1/ANIMATION_FPS:
                time.sleep((1/ANIMATION_FPS)-loop_duration)
            
    
    if __name__ == '__main__':
        main()

    logger.info("Exiting Normally")
    pygame.quit()
except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)