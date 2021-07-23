import argparse
import sys
import numpy as np
import paho.mqtt.client as mqtt
import cv2
import time

from segnet_utils import *
RATE = 10 #10hz
topic_ai_image_segementation_mask = "robud/ai/image_segmentation/mask"


processor = {'is_processing':False,'last_frame_start':0}
# process frames until user exits
def on_message(client, userdata, message):
    processor = userdata
    if not processor['is_processing'] and time.time() - processor['last_frame_start'] > 1/RATE:
        processor['last_frame_start'] = time.time()
        processor['is_processing'] = True
        # capture the next image
        #img_input = input.Capture()
        payload=message.payload
        np_bytes = np.frombuffer(payload, np.uint8)
        cv_image = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
        cv_image = cv2.cvtColor(cv_image,cv2.COLOR_BGR2RGB)
        #convert to cuda image
        img_input = jetson.utils.cudaFromNumpy(cv_image)
        
        # allocate buffers for this size image
        buffers.Alloc(img_input.shape, img_input.format)

        # process the segmentation network
        net.Process(img_input, ignore_class=opt.ignore_class)
        #print("image processed")

        # generate the overlay
        if buffers.overlay:
            net.Overlay(buffers.overlay, filter_mode=opt.filter_mode)

        # generate the mask
        if buffers.mask:
            net.Mask(buffers.mask, filter_mode=opt.filter_mode)

        # composite the images
        if buffers.composite:
            jetson.utils.cudaOverlay(buffers.overlay, buffers.composite, 0, 0)
            jetson.utils.cudaOverlay(buffers.mask, buffers.composite, buffers.overlay.width, 0)

        cv_mask = jetson.utils.cudaToNumpy(buffers.mask)
        cv_mask = cv2.cvtColor(cv_mask, cv2.COLOR_RGB2BGR)
        jpg_mask = cv2.imencode('.jpg',cv_mask, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        payload=jpg_mask[1].tobytes()
        client.publish(topic=topic_ai_image_segementation_mask,payload=payload,qos=0)

        # render the output image
        #output.Render(buffers.output)
        processor['is_processing'] = False
    else: print("throttling until next frame")


# parse the command line
parser = argparse.ArgumentParser(description="Segment a live camera stream using an semantic segmentation DNN.", 
                                 formatter_class=argparse.RawTextHelpFormatter, epilog=jetson.inference.segNet.Usage() +
                                 jetson.utils.videoSource.Usage() + jetson.utils.videoOutput.Usage() + jetson.utils.logUsage())

parser.add_argument("input_URI", type=str, default="", nargs='?', help="URI of the input stream")
parser.add_argument("output_URI", type=str, default="", nargs='?', help="URI of the output stream")
parser.add_argument("--network", type=str, default="fcn-resnet18-voc", help="pre-trained model to load, see below for options")
parser.add_argument("--filter-mode", type=str, default="linear", choices=["point", "linear"], help="filtering mode used during visualization, options are:\n  'point' or 'linear' (default: 'linear')")
parser.add_argument("--visualize", type=str, default="overlay,mask", help="Visualization options (can be 'overlay' 'mask' 'overlay,mask'")
parser.add_argument("--ignore-class", type=str, default="void", help="optional name of class to ignore in the visualization results (default: 'void')")
parser.add_argument("--alpha", type=float, default=150.0, help="alpha blending value to use during overlay, between 0.0 and 255.0 (default: 150.0)")
parser.add_argument("--stats", action="store_true", help="compute statistics about segmentation mask class output")

is_headless = ["--headless"] if sys.argv[0].find('console.py') != -1 else [""]

try:
	opt = parser.parse_known_args()[0]
except:
	print("")
	parser.print_help()
	sys.exit(0)

#opt.network = 'fcn-resnet18-sun'
#opt.network='fcn-resnet18-sun'
# load the segmentation network
net = jetson.inference.segNet(opt.network, sys.argv)

# set the alpha blending value
net.SetOverlayAlpha(opt.alpha)

# create buffer manager
buffers = segmentationBuffers(net, opt)

# create video sources & outputs
#input = jetson.utils.videoSource(opt.input_URI, argv=sys.argv)
#output = jetson.utils.videoOutput(opt.output_URI, argv=sys.argv+is_headless)
import jetson.inference #needs to be imported after output is set (see https://github.com/dusty-nv/jetson-inference/issues/619)

broker_address="robud.local"
client = mqtt.Client(client_id="camera-test", userdata=processor) #create new instance
client.on_message=on_message 
print("connecting to broker")
client.connect(broker_address) #connect to broker
##time.sleep(4)
print("Subscribing to topic","robud/sensors/camera/raw")
client.subscribe("robud/sensors/camera/raw")
client.loop_forever()


