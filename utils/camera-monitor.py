import cv2
import paho.mqtt.client as mqtt
import time
from io import BytesIO
import numpy as np
#import nanocamera as nano

frame=None
monkey=None
processing_message = False
def on_message(client, userdata, message):
    global processing_message
    if processing_message == False:
    #print ("processing message")
        processing_message = True
        payload=message.payload
        np_bytes = np.frombuffer(payload, np.uint8)
        frame2 = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
        cv2.imshow("Robud Camera Monitor", frame2)
        cv2.waitKey(25)
        processing_message = False


broker_address="robud.local"
client = mqtt.Client("robud_utils_camera-monitor.py") #create new instance
client.on_message=on_message 
print("connecting to broker")
client.connect(broker_address) #connect to broker
##time.sleep(4)
print("Subscribing to topic","robud/sensors/camera/raw")
client.subscribe("robud/sensors/camera/raw")
client.loop_forever()
