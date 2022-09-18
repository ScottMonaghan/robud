import logging

LOGGING_LEVEL = logging.DEBUG
MQTT_BROKER_ADDRESS = "robud.local"
SAMPLE_RATE = 16000
AUDIO_INPUT_INDEX = 11 #Respeaker v2 4-mic array, plugged into Jetson Nano 
CHUNK  = 1024
BYTES_PER_FRAME = 2 #16bit

#speech detection
SPEECH_DETECTION_PADDING_SEC = 0.5
SPEECH_DETECTION_RATIO = 0.75
SPEECH_TIMEOUT = 10 #timeout for speech detection in seconds 