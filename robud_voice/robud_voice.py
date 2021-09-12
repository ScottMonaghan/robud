import paho.mqtt.client as mqtt
import subprocess

MQTT_BROKER_ADDRESS = "localhost"
MQTT_CLIENT_NAME = "robud_voice.py"
TOPIC_ROBUD_VOICE_TEXT_INPUT = 'robud/robud_voice/text_input'

def on_message_robud_voice_text_input(client, userdata, message):
    tts = message.payload.decode()
    print (tts)
    subprocess.Popen('espeak-ng -m -v us-mbrola-1 -s 140 "'+ tts +'" --stdout | aplay -Dplug:ladspa -', shell=True)

client_userdata = {}
mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_NAME,userdata=client_userdata)
mqtt_client.connect(MQTT_BROKER_ADDRESS)
print('MQTT Client Connected')
mqtt_client.subscribe(TOPIC_ROBUD_VOICE_TEXT_INPUT)
mqtt_client.message_callback_add(TOPIC_ROBUD_VOICE_TEXT_INPUT,on_message_robud_voice_text_input)
print('Waiting for messages...')
mqtt_client.loop_forever()
