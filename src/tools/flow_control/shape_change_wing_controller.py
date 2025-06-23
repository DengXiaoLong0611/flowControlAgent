"""
ShapeChangeWingController
========================

可形变翼板控制工具类。
- 支持多翼板位置、角度控制，自动保存状态，串口通信。
- 适用于主动流动控制、气动实验等场景。

依赖：
    - serial
    - numpy
    - struct

用法示例：
    from tools.flow_control.shape_change_wing_controller import ShapeChangeWingController
    controller = ShapeChangeWingController(port='COM17', baudrate=115200)
    controller.set_fin_position([0, 0, 0, 0])
    controller.set_fin_angle([10, 0, 0, 0])
    controller.reset_position()
    controller.reset_angle()
"""

import struct
import serial
import os
import time
import numpy as np

class ShapeChangeWingController:
    """
    可形变翼板控制工具类
    """
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def _send(self, byte_array):
        arduino = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        time.sleep(2)  # 等待连接
        arduino.write(byte_array)
        while True:
            count = arduino.inWaiting()
            if count >= 20:
                data = arduino.read_all()
                break
        arduino.close()
        return data

    def set_fin_position(self, array):
        """
        设置翼板位置
        :param array: 4元组或列表，目标位置
        """
        file_path = 'position_fin.npy'
        if os.path.exists(file_path):
            position = np.load(file_path).astype(np.float64)
        else:
            position = np.array([0, 0, 0, 0]).astype(np.float64)
            np.save(file_path, position)
        diff = np.subtract(array, position)
        data_np = np.hstack(([1.0], diff))
        byte_array = struct.pack('5f', *data_np)
        self._send(byte_array)
        np.save(file_path, array)
        print('FIN OK')

    def set_fin_angle(self, array):
        """
        设置翼板角度
        :param array: 4元组或列表，目标角度
        """
        file_path = 'position_angle.npy'
        if os.path.exists(file_path):
            position = np.load(file_path).astype(np.float64)
        else:
            position = np.array([0, 0, 0, 0]).astype(np.float64)
            np.save(file_path, position)
        diff = np.subtract(array, position)
        data_np = np.hstack(([2.0], diff))
        byte_array = struct.pack('5f', *data_np)
        self._send(byte_array)
        np.save(file_path, array)
        print('ANGLE OK')

    def reset_position(self):
        """
        翼板位置复位
        """
        self.set_fin_position([0, 0, 0, 0])

    def reset_angle(self):
        """
        翼板角度复位
        """
        self.set_fin_angle([0, 0, 0, 0])

# Example usage
if __name__ == '__main__':
    controller = ShapeChangeWingController(port='COM17', baudrate=115200)
    controller.set_fin_position([0, 0, 0, 0])
    controller.set_fin_angle([10, 0, 0, 0])
    controller.reset_position()
    controller.reset_angle() 