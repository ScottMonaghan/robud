import board
import busio
import time
import paho.mqtt.client as mqtt
import adafruit_bno055
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bno055.BNO055_I2C(i2c)
rate = 15 #publish rate in hz
topic_orientation_euler = "robud/sensors/orientation/euler"
topic_orientation_heading = "robud/sensors/orientation/heading"
topic_orientation_pitch = "robud/sensors/orientation/pitch"
topic_orientation_roll = "robud/sensors/orientation/roll"
topic_orientation_calibration_status_sys = "robud/sensors/orientation/calibration_status/sys"
topic_orientation_calibration_status_gyro = "robud/sensors/orientation/calibration_status/gyro"
topic_orientation_calibration_status_accel = "robud/sensors/orientation/calibration_status/accel"
topic_orientation_calibration_status_mag = "robud/sensors/orientation/calibration_status/mag"


broker_address="127.0.0.1"
client = mqtt.Client("orientation") #create new instance
client.connect(broker_address)
client.loop_start()
while True:
    loop_start = time.time()
    orientation_euler = sensor.euler
    orientation_heading = orientation_euler[0]
    orientation_roll = orientation_euler[1]
    orientation_pitch = orientation_euler[2]
    orientation_calibration_status = sensor.calibration_status
    orientation_calibration_status_sys = sensor.calibration_status[0]
    orientation_calibration_status_gyro = sensor.calibration_status[1]
    orientation_calibration_status_accel = sensor.calibration_status[2]
    orientation_calibration_status_mag = sensor.calibration_status[3]

    print(
        'heading:{0:.0f}\ttilt:{1:.0f}\t\troll:{2:.0f}\t\tcalibration:{3}'
        .format(
            orientation_heading,
            orientation_pitch,
            orientation_roll,
            orientation_calibration_status)
        )
    client.publish(topic=topic_orientation_heading,payload=orientation_heading,retain=True)
    client.publish(topic=topic_orientation_roll,payload=orientation_roll,retain=True)
    client.publish(topic=topic_orientation_pitch,payload=orientation_pitch,retain=True)
    client.publish(topic=topic_orientation_calibration_status_sys,payload=orientation_calibration_status_sys,retain=True)
    client.publish(topic=topic_orientation_calibration_status_gyro,payload=orientation_calibration_status_gyro,retain=True)
    client.publish(topic=topic_orientation_calibration_status_accel,payload=orientation_calibration_status_accel,retain=True)
    client.publish(topic=topic_orientation_calibration_status_mag,payload=orientation_calibration_status_mag,retain=True)
    loop_time = time.time()-loop_start
    if (loop_time<1/rate):
        time.sleep( 1/rate - loop_time)
   
