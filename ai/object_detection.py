import jetson.inference
import jetson.utils
import numpy as np
import paho.mqtt.client as mqtt
import cv2
import time
import pickle

OBJECT_DETECTION_RATE = 10 #hz

TOPIC_OBJECT_DETECTION_VIDEO_FRAME = "robud/ai/object_detection/videoframe"
TOPIC_OBJECT_DETECTION_DETECTIONS = "robud/ai/object_detection/detections"
TOPIC_CAMERA_RAW = "robud/sensors/camera/raw"
BROKER_ADDRESS = "robud.local"
CLIENT_NAME = "object_detection.py"

def on_message(client:mqtt.Client,userdata,message):
    processor = userdata
    if not processor['is_processing'] and time.time() - processor['last_frame_start'] > 1/OBJECT_DETECTION_RATE:
        processor['last_frame_start'] = time.time()
        processor['is_processing'] = True

        payload=message.payload
        np_bytes = np.frombuffer(payload, np.uint8)
        cv_image = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
        cv_image = cv2.cvtColor(cv_image,cv2.COLOR_BGR2RGB)
        #convert to cuda image
        img_input = jetson.utils.cudaFromNumpy(cv_image)

        detections = net.Detect(img_input)
        detections_out = [] * len(detections)
        for detection in detections:
            detection_out = {
                "ClassID":detection.ClassID,
                "Confidence":detection.Confidence,
                "Left":detection.Left,
                "Top":detection.Top,
                "Right":detection.Right,
                "Bottom":detection.Bottom,
                "Width":detection.Width,
                "Height":detection.Height,
                "Area":detection.Area,
                "Center":detection.Center
            }
            detections_out.append(detection_out)
        #I *think* the above actually changes the image as well
        cv_image = jetson.utils.cudaToNumpy(img_input)
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
        jpg_image = cv2.imencode('.jpg',cv_image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        detection_video_frame_payload=jpg_image[1].tobytes()

        client.publish(TOPIC_OBJECT_DETECTION_DETECTIONS, payload=pickle.dumps(detections_out))
        client.publish(TOPIC_OBJECT_DETECTION_VIDEO_FRAME, payload=detection_video_frame_payload)
        processor['is_processing'] = False

#load model
net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)

processor = {'is_processing':False,'last_frame_start':0}
mqtt_client = mqtt.Client(client_id=CLIENT_NAME, userdata=processor) #create new instance
mqtt_client.on_message=on_message 
print("connecting to broker")
mqtt_client.connect(BROKER_ADDRESS) #connect to broker

print("Subscribing to topic",TOPIC_CAMERA_RAW)
mqtt_client.subscribe(TOPIC_CAMERA_RAW)
mqtt_client.loop_forever()



