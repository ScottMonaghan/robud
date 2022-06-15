import cv2
import paho.mqtt.client as mqtt
import time
from io import BytesIO
import numpy as np
from matplotlib import pyplot as plt

from gi.repository import Gtk
print(Gtk.get_major_version())
print(Gtk.get_minor_version())
print(Gtk.get_micro_version())
print(cv2.__version__)
topic_camera_raw="robud/sensors/camera/raw" 
frame=None
processing_message = False
def on_message(client, userdata, message):
    global processing_message
    if processing_message == False:
        processing_message = True
        payload=message.payload
        np_bytes = np.frombuffer(payload, np.uint8)
        frame2 = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
        window = "features experiment"
        #lets do some ORB stuff

        #initiate ORB detector
        orb = cv2.ORB_create()

        #find the keypoints with ORB
        kp = orb.detect(frame2,None)

        #compute the descriptors with ORB
        kp, des = orb.compute(frame2, kp)

        #draw keypoints
        frame3 = cv2.drawKeypoints(frame2, kp, None, color=(0,255,0), flags=0)

        #plt.imshow(frame3), plt.show

        cv2.imshow(window, frame3)
        cv2.waitKey(25)
        processing_message = False


broker_address="robud.local"
client = mqtt.Client("robud_utils_camera-monitor.py") #create new instance
client.on_message=on_message 
print("connecting to broker")
client.connect(broker_address) #connect to broker
topic = topic_camera_raw
print("Subscribing to topic",topic)
client.subscribe(topic)
client.loop_forever()