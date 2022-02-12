import logging
from larynx.constants import VocoderQuality

ROBUD_LOGGING_LEVEL = logging.INFO
MQTT_BROKER_ADDRESS = "robud.local"
SAMPLE_RATE = 16000
AUDIO_INPUT_INDEX = 11 #Respeaker v2 4-mic array, plugged into Jetson Nano 
CHUNK  = 1024
PITCH_SHIFT_SEMITONES = 4
LARYNX_VOICE = "ljspeech-glow_tts"
LARYNX_VOCODER_QUALITY = VocoderQuality.LOW
LARYNX_NOISE_SCALE = 0.667
LARYNX_LENGTH_SCALE = 1.25
