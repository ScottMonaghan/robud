import sys, select, tty, termios
import paho.mqtt.client as mqtt
import time
import pygame
if __name__ == '__main__':

    MQTT_BROKER_ADDRESS = "robud.local"
    MQTT_CLIENT_NAME = "robud_utils_keyboard_controller.py"
    TOPIC_MOTOR_LEFT_THROTTLE = 'robud/motors/motor_left/throttle'
    TOPIC_MOTOR_RIGHT_THROTTLE = 'robud/motors/motor_right/throttle'
    TOPIC_HEAD_SERVO_ANGLE = 'robud/motors/head_servo/angle'
    HEAD_SERVO_MAX_ANGLE = 180
    HEAD_SERVO_MIN_ANGLE = 0
    SCREENHEIGHT = 320
    SCREENWIDTH = 640
    MOTOR_SPEED_BASE = 0.5
    MOTOR_SPEED_ACCELERATED = 1

    rate = 100 #100hz rate for sending messages
    carry_on = True
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME)

    def move_forward():
        print("move forward")
        mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, MOTOR_SPEED_BASE)
        mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, MOTOR_SPEED_BASE)

    def move_backward():
        print("move backward")
        mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, -1 * MOTOR_SPEED_BASE)
        mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, -1 * MOTOR_SPEED_BASE)

    def turn_right():
        print("turn right")
        mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, MOTOR_SPEED_BASE)
        mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, -1 * MOTOR_SPEED_BASE)

    def turn_left():
        print("turn left")
        mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, -1 * MOTOR_SPEED_BASE)
        mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, MOTOR_SPEED_BASE)

    def stop():
        print("stop")
        mqtt_client.publish(TOPIC_MOTOR_LEFT_THROTTLE, 0)
        mqtt_client.publish(TOPIC_MOTOR_RIGHT_THROTTLE, 0)

    
    pygame.init()
    clock = pygame.time.Clock()
    screensize = (SCREENWIDTH, SCREENHEIGHT)
    screen = pygame.display.set_mode(screensize)
    mqtt_client.connect(MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start()
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
            move_forward()
        elif keys[pygame.K_DOWN]:
            move_backward()
        elif keys[pygame.K_LEFT]:
            turn_left()
        elif keys[pygame.K_RIGHT]:
            turn_right()
        else:
            stop()
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