#[x]import larynx
import larynx
from larynx.constants import VocoderQuality, TextToSpeechResult

#[x]import pyaudio
from pyaudio import PyAudio, paInt16, paContinue, Stream

#[x]for pitch shift import librosa
import librosa.effects 
import pyrubberband 


#resample 
import numpy as np
from scipy import signal

def resample(data, input_rate, output_rate):
        """
        Microphone may not support our native processing sampling rate, so
        resample from input_rate to RATE_PROCESS here for webrtcvad and
        stt

        Args:
            data (binary): Input audio stream
            input_rate (int): Input audio rate to resample from
            output_rate (int): Output audio rate to resample to
        """
        data16 = np.frombuffer(buffer=data, dtype=np.int16)
        resample_size = int(len(data16) / input_rate * output_rate)
        resample = signal.resample(data16, resample_size)
        resample16 = np.array(resample, dtype=np.int16)
        return resample16.tobytes()

def pitch_shift(data,sample_rate,semitones):
    data16 = np.frombuffer(buffer=data, dtype=np.int16)
    data64 = np.array(data16, dtype=np.float64)
    resample = librosa.effects.pitch_shift(
        y=data64
        ,sr=sample_rate
        ,n_steps=semitones
        ,bins_per_octave=12      
    )
    resample16 = np.array(resample, dtype=np.int16) 
    return resample16.tobytes()

#[x]setup pyaudio output stream
pa = PyAudio()
stream = pa.open(
    rate=16000
    ,channels=1
    ,format = paInt16
    ,input=False
    ,frames_per_buffer=1024
    ,output_device_index=11 #Respeaker v2 4-mic array, plugged into Jetson Nano 
    ,output=True 
    ,start=True
)

#[x]use larynx to generate some speach audio
tts_results = larynx.text_to_speech(
   text="Hello my name is Ro-Bud."
   ,voice_or_lang="ljspeech-glow_tts"
   ,vocoder_or_quality = VocoderQuality.LOW
   ,tts_settings={
        "noise_scale": 0.667
   }
)

#[x]send the speech to the output stream
#[x]pitch shift the results
for result_idx, result in enumerate(tts_results):
    result_bytes = result.audio.tobytes()
    resampled_result = resample(result_bytes,22050,16000)
    pitch_shifted_result = pitch_shift(data=resampled_result,sample_rate=16000,semitones=5)
    stream.write(pitch_shifted_result)

