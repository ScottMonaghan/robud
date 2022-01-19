#!/usr/bin/env python3

from precise_runner import PreciseEngine, PreciseRunner
from pyaudio import PyAudio, paInt16

AUDIO_INPUT_INDEX = 11 #Respeaker v2 4-mic array, plugged into Jetson Nano 
VAD_AGGRESSIVENESS = 3
SAMPLE_RATE = 16000
AUDIO_INPUT_INDEX = 11 #Respeaker v2 4-mic array, plugged into Jetson Nano 

engine = PreciseEngine('/home/robud/Downloads/precise-engine/precise-engine', '/home/robud/src/precise-data/hey-mycroft.pb')

pa = PyAudio()
stream = pa.open(
    16000, 1, paInt16, True, frames_per_buffer=engine.chunk_size, input_device_index=AUDIO_INPUT_INDEX
)

runner = PreciseRunner(engine=engine, stream=stream, on_activation=lambda: print('activated!'))
runner.start()

# Sleep forever
from time import sleep
while True:
    sleep(10)
