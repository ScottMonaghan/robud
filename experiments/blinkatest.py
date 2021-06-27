import board
import digitalio
import busio

print("Hello blinka!")

# Try to great a Digital input
pin = digitalio.DigitalInOut(board.D4)
print("Digital IO ok!")

# Try to create an I2C device
i2c = busio.I2C(board.SCL, board.SDA)
print("I2C 1 ok!")
i2c = busio.I2C(board.SCL_1, board.SDA_1)
print("I2C 2 ok!")

print("done!")