import Jetson.GPIO as GPIO
import paho.mqtt.client as mqtt
from time import time, sleep

LEFT_ENCODER_CHANNEL = 7
RIGHT_ENCODER_CHANNEL = 11
TOPIC_ODOMETRY_LEFT_TICKS = "robud/sensors/odometry/left/ticks"
TOPIC_ODOMETRY_LEFT_TICKSPEED = "robud/sensors/odometry/left/tickspeed"
TOPIC_ODOMETRY_RIGHT_TICKS = "robud/sensors/odometry/right/ticks"
TOPIC_ODOMETRY_RIGHT_TICKSPEED = "robud/sensors/odometry/right/tickspeed"
BROKER_ADDRESS="localhost"
CLIENT_NAME="odometry.py"
TICKSPEED_SAMPLE_RATE = 5 #htz 

left_ticks = 0
right_ticks = 0
left_tickspeed = 0 #ticks per second
right_tickspeed = 0 #ticks per second

def tickDetected(channel):
    global left_ticks
    global right_ticks
    #global tickspeed

    if channel == LEFT_ENCODER_CHANNEL:
        left_ticks+=1
        mqtt_client.publish(TOPIC_ODOMETRY_LEFT_TICKS, payload=left_ticks, qos=2, retain=True)
    elif channel == RIGHT_ENCODER_CHANNEL:
        right_ticks+=1
        mqtt_client.publish(TOPIC_ODOMETRY_RIGHT_TICKS, payload=right_ticks, qos=2, retain=True)
    #print("Left Ticks:",left_ticks, "\t\tRight Ticks:",right_ticks)

GPIO.setmode(GPIO.BOARD)
GPIO.setup(LEFT_ENCODER_CHANNEL,GPIO.IN)
GPIO.setup(RIGHT_ENCODER_CHANNEL,GPIO.IN)

mqtt_client = mqtt.Client(CLIENT_NAME) #create new instance
mqtt_client.connect(BROKER_ADDRESS)
mqtt_client.loop_start()
mqtt_client.publish(TOPIC_ODOMETRY_LEFT_TICKS, payload=left_ticks, qos=2, retain=True)
mqtt_client.publish(TOPIC_ODOMETRY_RIGHT_TICKS, payload=right_ticks, qos=2, retain=True)

GPIO.add_event_detect(LEFT_ENCODER_CHANNEL, GPIO.BOTH, callback=tickDetected)
GPIO.add_event_detect(RIGHT_ENCODER_CHANNEL, GPIO.BOTH, callback=tickDetected)

try:
    while True:
        #calculate ticks per second every half second
        start_sample_time = time()
        start_left_ticks = left_ticks
        start_right_ticks = right_ticks
        sleep(1/TICKSPEED_SAMPLE_RATE)
        sample_duration = time() - start_sample_time
        total_left_ticks = left_ticks - start_left_ticks
        total_right_ticks = right_ticks - start_right_ticks
        left_tickspeed = int(total_left_ticks/sample_duration)
        right_tickspeed = int(total_right_ticks/sample_duration)
        mqtt_client.publish(TOPIC_ODOMETRY_LEFT_TICKSPEED, payload=left_tickspeed, qos=0)
        mqtt_client.publish(TOPIC_ODOMETRY_RIGHT_TICKSPEED, payload=right_tickspeed, qos=0)
        #print(left_tickspeed, "\t\t\t", right_tickspeed)


except KeyboardInterrupt:
    print("CTRL-C Detected")
    GPIO.cleanup()
    exit(0)



















