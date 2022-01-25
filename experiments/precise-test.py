#!/usr/bin/env python3

from pickle import FALSE
from precise_runner import PreciseEngine, PreciseRunner
from pyaudio import PyAudio, paInt16

AUDIO_INPUT_INDEX = 11 #Respeaker v2 4-mic array, plugged into Jetson Nano 
VAD_AGGRESSIVENESS = 3
SAMPLE_RATE = 16000
AUDIO_INPUT_INDEX = 11 #Respeaker v2 4-mic array, plugged into Jetson Nano 
CHUNK = 2048

engine = PreciseEngine('/home/robud/Downloads/precise-engine/precise-engine', '/home/robud/src/precise-data/hey-mycroft.pb')

def stream_callback():
    pass

pa = PyAudio()
stream = pa.open(
    rate=SAMPLE_RATE
    ,channels=1
    ,format = paInt16
    ,input=True
    ,frames_per_buffer=CHUNK
    ,input_device_index=AUDIO_INPUT_INDEX
    ,stream_callback=stream_callback
    ,output=False # keep output false until we integrate output
    #,start=False
)

runner = PreciseRunner(engine=engine, stream=stream, on_activation=lambda: print('activated!'))
runner.start()

# Sleep forever
from time import sleep
while True:
    sleep(10)
