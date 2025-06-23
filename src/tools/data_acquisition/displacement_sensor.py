import time
import numpy as np
import pandas as pd
import scipy.optimize as optimize
from scipy.signal import savgol_filter
import socket

class LaserDisplacementSensor:
    """
    激光位移计数据采集与处理工具类
    支持采集触发、RMS读取、采样数据读取、正弦拟合等
    """
    def __init__(self, data_file_path: str):
        self.data_file_path = data_file_path

    def trigger_acquisition(self, wait_time: float = 2.7, udp_host: str = 'localhost', udp_port: int = 12345):
        """
        触发LabVIEW进行数据采集
        :param wait_time: 采集后等待时间（秒）
        :param udp_host: UDP主机
        :param udp_port: UDP端口
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(b'001', (udp_host, udp_port))
        finally:
            sock.close()
        print(f"已发送采集触发信号，等待{wait_time}秒...")
        time.sleep(wait_time)

    def get_rms_and_samples(self):
        """
        读取RMS值和采样数据（5秒300点）
        :return: (rms_value, sampled_data)
        """
        df = pd.read_csv(self.data_file_path, usecols=['Time', 'Laser1234Ave'])
        rms_value = df.loc[df['Time'] == 'RMS', 'Laser1234Ave'].values[0]
        last_5_seconds_data = df['Laser1234Ave'].values[-2500:]
        indices = np.linspace(0, 2500, 300, endpoint=False).astype(int)
        sampled_data = last_5_seconds_data[indices]
        return float(rms_value), sampled_data

    def get_rms_and_samples_1s(self):
        """
        读取RMS值和采样数据（1秒10点）
        :return: (rms_value, sampled_data)
        """
        df = pd.read_csv(self.data_file_path, usecols=['Time', 'Laser1234Ave'])
        rms_value = df.loc[df['Time'] == 'RMS', 'Laser1234Ave'].values[0]
        last_0_99seconds_data = df['Laser1234Ave'].values[-495:]
        indices = np.linspace(0, 495, 10, endpoint=False).astype(int)
        sampled_data = last_0_99seconds_data[indices]
        return float(rms_value), sampled_data

    def fit_sine(self):
        """
        对采集到的平均位移数据进行正弦拟合
        :return: 拟合参数(a0, a1, a2, a3)
        """
        df = pd.read_csv(self.data_file_path, usecols=['Time', 'LaserPlacementAverage'])
        Time = df['Time'].values[1:150].astype(float)
        PlacementAve = df['LaserPlacementAverage'].values[1:150]
        PlacementAve = savgol_filter(PlacementAve, 20, 3)
        def target_func(x, a0, a1, a2, a3):
            return a0 * np.sin(a1 * x + a2) + a3
        fs = np.fft.fftfreq(len(Time), Time[1] - Time[0])
        Y = abs(np.fft.fft(Time))
        freq = abs(fs[np.argmax(Y[1:]) + 1])
        a0 = max(PlacementAve) - min(PlacementAve)
        a1 = 2 * np.pi * freq
        a2 = 0
        a3 = np.mean(PlacementAve)
        p0 = [a0, a1, a2, a3]
        para, _ = optimize.curve_fit(target_func, Time, PlacementAve, p0=p0)
        print(f"正弦拟合参数: {para}")
        return tuple(para)

# 示例用法
if __name__ == '__main__':
    sensor = LaserDisplacementSensor(r'C:/data/data.csv')
    sensor.trigger_acquisition()
    rms, samples = sensor.get_rms_and_samples()
    print(f"RMS: {rms}")
    print(f"Samples: {samples}")
    params = sensor.fit_sine()
    print(f"Sine fit params: {params}") 