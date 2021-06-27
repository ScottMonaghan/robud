import board
import busio
import adafruit_vl53l0x
import time
import statistics
import paho.mqtt.client as mqtt
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_vl53l0x.VL53L0X(i2c)
sample_size = 4
tolerance = 0.05
rate = 15 #publish rate in hz
topic = "robud/sensors/tof/range"

def get_range_from_sample(sample):
    #first get median from sample
    median = statistics.median(sample)
    #now check if all values are in tolerance
    for measurement in sample:
        if abs(median - measurement) > tolerance * median:
            return -1
    return int(sum(sample)/len(sample)/10)

broker_address="127.0.0.1"
client = mqtt.Client("tof") #create new instance
client.connect(broker_address)
#to make this useful, we'll only publish if the sample set are within tolerance of each other
client.loop_start()
while True:
    loop_start = time.time()
    sample = []
    for i in range(sample_size-1):
        sample.append(sensor.range)
        #time.sleep(0.01)
    tof_range = get_range_from_sample(sample)
    print('{} cm'.format(tof_range))
    client.publish(topic=topic,payload=tof_range,qos=2)
    loop_time = time.time()-loop_start
    if (loop_time<1/rate):
        time.sleep( 1/rate - loop_time)
    