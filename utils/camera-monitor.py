import cv2
import paho.mqtt.client as mqtt
import time
from io import BytesIO
import numpy as np

topic_ai_image_segementation_mask = "robud/ai/image_segmentation/mask"
topic_camera_raw="robud/sensors/camera/raw" 
TOPIC_OBJECT_DETECTION_VIDEO_FRAME = "robud/ai/object_detection/videoframe"

frame=None
monkey=None
processing_message = False
def on_message(client, userdata, message):
    global processing_message
    if processing_message == False:
        processing_message = True
        payload=message.payload
        np_bytes = np.frombuffer(payload, np.uint8)
        frame2 = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
        if message.topic == topic_ai_image_segementation_mask:
            window = "Image Segmentation Mask"
        elif message.topic == topic_camera_raw:
            window = "Robud Camera Raw"
        elif message.topic == TOPIC_OBJECT_DETECTION_VIDEO_FRAME:
            window = "Object Detection"
        cv2.imshow(window, frame2)
        cv2.waitKey(25)
        processing_message = False


broker_address="robud.local"
client = mqtt.Client("robud_utils_camera-monitor.py") #create new instance
client.on_message=on_message 
print("connecting to broker")
client.connect(broker_address) #connect to broker
topic = topic_ai_image_segementation_mask
print("Subscribing to topic",topic)
client.subscribe(topic)
topic = topic_camera_raw
print("Subscribing to topic",topic)
client.subscribe(topic)
topic = TOPIC_OBJECT_DETECTION_VIDEO_FRAME
print("Subscribing to topic",topic)
client.subscribe(topic)
client.loop_forever()
