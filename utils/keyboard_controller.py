import sys, select, tty, termios
import paho.mqtt.client as mqtt
import time
import pygame

def on_heading_message(client, userdata, message):
        userdata["heading"] = int(float(message.payload))


if __name__ == '__main__':

    MQTT_BROKER_ADDRESS = "robud.local"
    MQTT_CLIENT_NAME = "robud_utils_keyboard_controller.py"
    TOPIC_MOTOR_LEFT_THROTTLE = 'robud/motors/motor_left/throttle'
    TOPIC_MOTOR_RIGHT_THROTTLE = 'robud/motors/motor_right/throttle'
    TOPIC_HEAD_SERVO_ANGLE = 'robud/motors/head_servo/angle'
    TOPIC_ORIENTATION_HEADING = 'robud/sensors/orientation/heading'
    HEAD_SERVO_MAX_ANGLE = 170
    HEAD_SERVO_MIN_ANGLE = 60
    SCREENHEIGHT = 320
    SCREENWIDTH = 640
    MOTOR_SPEED_BASE = 0.5
    MOTOR_SPEED_ACCELERATED = 0.7
    HEAD_ANGLE_CHANGE = 2
    HEAD_ANGLE_MAX = 180
    HEAD_ANGLE_MIN = 60

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
        if stopped:
            target_heading = current_heading
        elif current_heading > target_heading:
            #veering to the right, add more power to right wheel
            right_speed = MOTOR_SPEED_ACCELERATED
        elif current_heading < target_heading:
            #veering to the left, add more power to left wheel
            left_speed = MOTOR_SPEED_ACCELERATED
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
        print("stop")
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
        mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE, head_angle)
        return head_angle

    def look_down(head_angle):
        print("look down")
        new_angle = head_angle - HEAD_ANGLE_CHANGE
        if new_angle <= HEAD_ANGLE_MIN:
            new_angle = HEAD_ANGLE_MIN 
        head_angle = new_angle
        mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE, head_angle)
        return head_angle
    
    pygame.init()
    clock = pygame.time.Clock()
    screensize = (SCREENWIDTH, SCREENHEIGHT)
    screen = pygame.display.set_mode(screensize)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start()
    head_angle = 75
    mqtt_client.publish(TOPIC_HEAD_SERVO_ANGLE, head_angle)
    mqtt_client.subscribe(TOPIC_ORIENTATION_HEADING)
    mqtt_client.on_message=on_heading_message
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
        elif keys[pygame.K_LEFT]:
            stopped = turn_left(stopped)
        elif keys[pygame.K_RIGHT]:
            stopped = turn_right(stopped)
        else:
            stopped = stop(stopped)
        if keys[pygame.K_w]:
            head_angle = look_up(head_angle)
        elif keys[pygame.K_s]:
            head_angle = look_down(head_angle)

        clock.tick(rate)
                    
# if __name__ == '__main__':
#     try:
#         mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME)
#         mqtt_client.connect(MQTT_BROKER_ADDRESS)
#         mqtt_client.loop_start()
#         old_attr=termios.tcgetattr(sys.stdin)
#         tty.setcbreak(sys.stdin.fileno())
#         while True:
#             loop_start = time.time()
#             if select.select([sys.stdin], [], [], 0)[0] == [sys.stdin]:
#                 print(sys.stdin.read(1))
            
#             #make sure we're publishing at about the expected rate
#             loop_time = time.time() - loop_start            
#             if loop_time < 1/rate:
#                 time.sleep((1/rate) - loop_time)
#     except KeyboardInterrupt:
#         termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_attr)
#         print("Keybord Interrupt Detected. Exiting")
#         exit(0)