import serial
import time

# Change 'COM3' to your actual COM port
# On Mac/Linux: '/dev/ttyUSB0' or '/dev/tty.SLAB_USBtoUART'
ser = serial.Serial('COM3', 115200, timeout=2)

time.sleep(2)  # Wait for ESP32 to reset

# Read until we see "READY"
# while True:
#     line = ser.readline().decode().strip()
#     if line == "READY":
#         print("ESP32 is ready!")
#         break

# Send '1' to vibrate motor
print("Sending '1'...")
ser.write(b'1')

# Wait for response
response = ser.readline().decode().strip()
print(f"ESP32 says: {response}")

ser.close()