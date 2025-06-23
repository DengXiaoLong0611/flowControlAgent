#!/usr/bin/env python
# -*- coding: utf_8 -*-
"""
 Modbus TestKit: Implementation of Modbus protocol in python

 (C)2009 - Luc Jean - luc.jean@gmail.com
 (C)2009 - Apidev - http://www.apidev.fr

 This is distributed under GNU LGPL license, see license.txt
"""
import struct
import serial
import os
import time
import numpy as np

def send(byte_array):
    arduino = serial.Serial(port='COM17', baudrate=115200, timeout=.1)
    time.sleep(2)  # 等待连接
    arduino.write(byte_array)  # 发送字节数据
    while True:
        count = arduino.inWaiting()
        if count >= 20:  # 接收到的字节应该是 5 个浮动数，每个 4 字节，总共 20 字节
            data = arduino.read_all()
            break
    return data

def ctrl_fin(array):
    """
    控制翼板。
    - 如果 `array` 不为 None，则计算并发送差值，同时更新 position_fin.npy。
    - 如果 `position_fin.npy` 文件不存在，会自动创建并初始化为 [0, 0, 0, 0]。
    """
    file_path = 'position_fin.npy'
    
    # 读取 position_fin.npy 文件并检查文件是否存在
    if os.path.exists(file_path):
        position = np.load(file_path).astype(np.float64)
    else:
        # 如果文件不存在，创建并写入初始值
        position = np.array([0, 0, 0, 0]).astype(np.float64)
        np.save(file_path, position)
    # 计算新的数组与旧数组的差
    diff = np.subtract(array, position)
    # 在差值数组前加上 1，变为 5 维数组
    data_np = np.hstack(([1.0], diff))  # 1.0 表示操作标识符（可以是控制命令）
    # 将数据打包为字节流
    byte_array = struct.pack('5f', *data_np)  # 5f 表示 5 个浮动数，每个 4 字节
    # 发送字节数据
    send(byte_array)
    # 更新 position_fin.npy 文件内容
    np.save(file_path, array)
    print('FIN OK')

def ctrl_angle(array):
    """
    控制翼板。
    - 如果 `array` 不为 None，则计算并发送差值，同时更新 position_fin.npy。
    - 如果 `position_fin.npy` 文件不存在，会自动创建并初始化为 [0, 0, 0, 0]。
    """
    file_path = 'position_angle.npy'
    
    # 读取 position_fin.npy 文件并检查文件是否存在
    if os.path.exists(file_path):
        position = np.load(file_path).astype(np.float64)
    else:
        # 如果文件不存在，创建并写入初始值
        position = np.array([0, 0, 0, 0]).astype(np.float64)
        np.save(file_path, position)
    # 计算新的数组与旧数组的差
    diff = np.subtract(array, position)
    # 在差值数组前加上 2，变为 5 维数组
    data_np = np.hstack(([2.0], diff))  # 1.0 表示操作标识符（可以是控制命令）
    # 将数据打包为字节流
    byte_array = struct.pack('5f', *data_np)  # 5f 表示 5 个浮动数，每个 4 字节
    # 发送字节数据
    send(byte_array)
    # 更新 position_fin.npy 文件内容
    np.save(file_path, array)
    print('ANGLE OK')


if __name__ == "__main__":
    ctrl_fin([0, 0, 0, 0])
    #time.sleep(1)
    # ctrl_angle([0, 0, 0, 0])















# # 向arduino发送命令
# def ctrl_fin(array):
#     data_np = np.hstack(([1], array))
#     data_string = '/'.join(map(str, data_np)) + '/'
#     send(data_string)
#     np.save('position_fin.npy', array)

# def ctrl_angle(number):
#     data_np = np.hstack(([2], [number], [0,0,0]))
#     data_string = '/'.join(map(str, data_np)) + '/'
#     send(data_string)
#     np.save('position_angle.npy', number)

# def send(x):
#     arduino = serial.Serial(port='COM17', baudrate=115200, timeout=.1)
#     time.sleep(2)
#     arduino.write(bytes(x, 'utf-8'))
#     while True:
#         count = arduino.inWaiting()
#         if count >= 10:
#             data = arduino.read_all()
#             break
#     return   data

# # 翼板返回原点
# def reset_fin():
#     file_path = 'position_fin.npy'
#     if os.path.exists(file_path):
#         position = np.load(file_path).astype(np.float64)
#         data_np = np.hstack(([0], position))
#         data_string = '/'.join(map(str, data_np)) + '/'
#         send(data_string)
#     position = np.array([0, 0, 0, 0]).astype(np.float64)
#     np.save(file_path, position)

# # 翼板返回原点
# def reset_angle():
#     file_path = 'position_angle.npy'
#     if os.path.exists(file_path):
#         position = np.load(file_path).astype(np.float64)
#         data_np = np.hstack(([2], position, [0,0,0]))
#         data_string = '/'.join(map(str, data_np)) + '/'
#         send(data_string)
#     position = np.array([0]).astype(np.float64)
#     np.save(file_path, position)

# if __name__ == "__main__":
#     time.sleep(2)
#     send('1/0/0/0/20')
#     print('ok')


# def ext():
#     send('1/0/0/0/2')
#     time.sleep(8)
#     print('ok')

# if __name__ == "__main__":
#     time.sleep(2)
#     send('1/0/0/0/20')
#     print('ok')