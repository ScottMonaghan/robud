import cv2
import nanocamera as nano
import paho.mqtt.client as mqtt
import time
from io import BytesIO
import numpy as np

topic_camera_raw = "robud/sensors/camera/raw"
broker_address="robud.local"
client = mqtt.Client("camera") #create new instance
client.connect(broker_address)
client.loop_start()
# Create the Camera instance for 640 by 480
camera = nano.Camera(flip=2, width=640, height=360, fps=15)
while camera.isReady():
    try:
        # read the camera image
        frame = camera.read()
        encoded_frame = cv2.imencode('.jpg',frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        payload=encoded_frame[1].tobytes()
        client.publish(topic=topic_camera_raw,payload=payload,qos=0)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(e)

    # close the camera instance
camera.release()

    # remove camera object
del camera
