import pytweening
import pygame 
import random
import os


ROBUD_EYE_SPACING = 50
SCREENWIDTH = 800
SCREENHEIGHT = 480
BLINK_DURATION = 200
MINIMUM_BLINK_DELAY = 500
AVG_BLINK_DELAY = 3000


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

class ExpressionCoordinates():
        def __init__ (self,
            top_flat_lid = (-50,-250), 
            bottom_flat_lid = (-50,250),
            round_lid = (-50,250)
            ):
            self.top_flat_lid = top_flat_lid
            self.bottom_flat_lid = bottom_flat_lid
            self.round_lid = round_lid

Expressions = {
            ExpressionId.OPEN: ExpressionCoordinates(
                top_flat_lid = (-50,-250),
                bottom_flat_lid = (-50,250),
                round_lid = (-50,250)
            )
            , ExpressionId.HAPPY: ExpressionCoordinates(
                top_flat_lid = (-50,-250),
                bottom_flat_lid = (-50,175),
                round_lid = (-50,150)
            )  
            , ExpressionId.BLINKING: ExpressionCoordinates(
                top_flat_lid = (-50,-130)
                ,bottom_flat_lid = (-50,130)
                ,round_lid = (-50,130),
            )          
        }

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
                    self.is_blinking = True
                    self.left_eye.last_expression = self.left_eye.expression
                    self.right_eye.last_expression = self.right_eye.expression
                    self.left_eye.expression = Expressions[ExpressionId.BLINKING] 
                    self.right_eye.expression = Expressions[ExpressionId.BLINKING] 
                self.last_blink = pygame.time.get_ticks()
        elif current_time - self.last_blink > BLINK_DURATION:            
            self.is_blinking = False
            self.left_eye.expression = self.left_eye.last_expression
            self.right_eye.expression = self.right_eye.last_expression
            self.left_eye.last_expression = None
            self.right_eye.last_expression = None
        elif current_time - self.last_blink >= BLINK_DURATION/2:
            #animate it!
            time_since_blink_start = current_time - self.last_blink + BLINK_DURATION/2
            animation_percentage = pytweening.easeOutSine(time_since_blink_start/BLINK_DURATION/2) 
            top_left_total_distance_to_travel = self.left_eye.last_expression.top_flat_lid[1] - Expressions[ExpressionId.BLINKING].top_flat_lid[1]
            top_right_total_distance_to_travel = self.right_eye.last_expression.top_flat_lid[1] - Expressions[ExpressionId.BLINKING].top_flat_lid[1]
            bottom_left_total_distance_to_travel = self.left_eye.last_expression.bottom_flat_lid[1] - Expressions[ExpressionId.BLINKING].bottom_flat_lid[1]
            bottom_right_total_distance_to_travel = self.right_eye.last_expression.bottom_flat_lid[1] - Expressions[ExpressionId.BLINKING].bottom_flat_lid[1]
            left_cheek_total_distance_to_travel = self.left_eye.last_expression.round_lid[1] - Expressions[ExpressionId.BLINKING].round_lid[1]
            right_cheek_total_distance_to_travel = self.right_eye.last_expression.round_lid[1] - Expressions[ExpressionId.BLINKING].round_lid[1]
            top_left_animated = (-50, Expressions[ExpressionId.BLINKING].top_flat_lid[1] + int(animation_percentage * top_left_total_distance_to_travel))
            bottom_left_animated = (-50, Expressions[ExpressionId.BLINKING].bottom_flat_lid[1] + int(animation_percentage * bottom_left_total_distance_to_travel))
            left_cheek_animated = (-50,Expressions[ExpressionId.BLINKING].round_lid[1] + int(animation_percentage * left_cheek_total_distance_to_travel))
            top_right_animated = (-50, Expressions[ExpressionId.BLINKING].top_flat_lid[1] + int(animation_percentage * top_right_total_distance_to_travel))
            bottom_right_animated = (-50, Expressions[ExpressionId.BLINKING].bottom_flat_lid[1] + int(animation_percentage * bottom_right_total_distance_to_travel))
            right_cheek_animated = (-50,Expressions[ExpressionId.BLINKING].round_lid[1] + int(animation_percentage * right_cheek_total_distance_to_travel))
            self.left_eye.expression = ExpressionCoordinates( top_flat_lid = top_left_animated, bottom_flat_lid = bottom_left_animated, round_lid=left_cheek_animated)
            self.right_eye.expression = ExpressionCoordinates( top_flat_lid = top_right_animated, bottom_flat_lid = bottom_right_animated, round_lid=right_cheek_animated)


face_expression = None # [0] * FACE_EXPRESSION_ARRAY_SIZE

def callback(data):
    global face_expression
    face_expression = data.data

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

def main():
    #rospy.init_node('robud_face')
    #rospy.Subscriber('robud_face_expression', Int16MultiArray, callback)
    random.seed()
    #pygame.display.init()
    pygame.init()
    pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))

    screensize = (SCREENWIDTH, SCREENHEIGHT)
    screen = pygame.display.set_mode(screensize,pygame.FULLSCREEN)
    script_dir = os.path.dirname(__file__)
    robud_face = RobudFace(
        os.path.join(script_dir,"robud_eye.png"),
        os.path.join(script_dir,"robud_flat_lid.png"),
        os.path.join(script_dir,"robud_round_lid.png")
    )
    robud_face.right_eye.expression = Expressions[ExpressionId.OPEN]
    robud_face.left_eye.expression = Expressions[ExpressionId.OPEN]
    carry_on = True
    clock = pygame.time.Clock()
    face_angle = 0
    carry_on = True

    while carry_on:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                carry_on = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    print("pressed CTRL-C as an event")
                    carry_on = False
                if  event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    pygame.display.toggle_fullscreen()
        if face_expression is not None and not robud_face.is_blinking:
            apply_face_expression(robud_face, face_expression)
        
        robud_face.blink()
        screen.fill((0,0,0))
        robud_face.update()
        screen.blit(robud_face.rotated_image, 
            (
                int(SCREENWIDTH/2 - robud_face.rotated_image.get_width()/2)
                + robud_face.center_x_offset,
                int(SCREENHEIGHT/2 - robud_face.rotated_image.get_height()/2)
                + robud_face.center_y_offset
            )
        )
        pygame.display.flip()
 
if __name__ == '__main__':
    main()

pygame.quit()