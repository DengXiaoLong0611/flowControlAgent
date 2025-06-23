import serial  # pip install pyserial
import time


gap_time = 3

arduino = serial.Serial(port='COM10', baudrate=115200, timeout=.1)
time.sleep(3)

def write_read(x):
    arduino.write(bytes(x, 'utf-8'))
    
    while True:
        count = arduino.inWaiting()
        # print(count)
        if count >= 4:
            data = arduino.read_all()
            break
    return   data

def send(str):

    value   = write_read(str)
    time.sleep(gap_time)
   
    print(value)

if __name__ == '__main__':
    send('0.00/0.00/0.00/0.00/0.55/0.00/0.00/0.00/0.00/0.00/0.00/0.00/0.00/0.00/0.00/') # 两位小数
    time.sleep(5)


