# import jetson.utils
# import paho.mqtt.client as mqtt
# import time
# from io import BytesIO
# import numpy as np

# rate=30
# camera = jetson.utils.videoSource("csi://0")
# output_path = "output.jpg"
# output= jetson.utils.videoOutput("file://" + output_path)
# #output=jetson.utils.videoOutput("display://0")
# topic_camera_raw = "robud/sensors/camera/raw"
# broker_address="127.0.0.1"
# client = mqtt.Client("P2") #create new instance
# client.connect(broker_address)
# client.loop_start()
# resized_image = jetson.utils.cudaAllocMapped(width=1280 * 0.5, 
#                                           height=720 * 0.5, 
#                                           format='rgb8')
# while True:
#     loop_start = time.time()
#     img = camera.Capture()
#     #jetson.utils.cudaResize(img, resized_image)
#     #output.Render(imgOutput)
#     #imgOutput.Render()
#     img_np = jetson.utils.cudaToNumpy(img)
#     jetson.utils.cudaDeviceSynchronize()
#     np_bytes = BytesIO()
#     np.save(np_bytes, img_np, allow_pickle=True)
#     client.publish(topic=topic_camera_raw,payload=np_bytes.getvalue())
#     loop_time = time.time()-loop_start
#     if (loop_time<1/rate):
#         time.sleep( 1/rate - loop_time)
#     #print(time.time()-loop_start)    

import cv2
import nanocamera as nano
import paho.mqtt.client as mqtt
import time
from io import BytesIO
import numpy as np

topic_camera_raw = "robud/sensors/camera/raw"
broker_address="127.0.0.1"
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
        client.publish(topic=topic_camera_raw,payload=payload,qos=2)
        #np_bytes = np.frombuffer(payload, np.uint8)
        #frame2 = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
        #cv2.imshow("Video Frame", frame)
        #cv2.imshow("Video Frame 2", frame2)
        #if cv2.waitKey(25) & 0xFF == ord('q'):
        #    break
    except KeyboardInterrupt:
        break

    # close the camera instance
camera.release()

    # remove camera object
del camera
