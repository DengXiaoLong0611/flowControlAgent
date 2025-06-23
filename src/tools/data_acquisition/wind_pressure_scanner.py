import os
import time
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from communication_protocol.Adapter import AdapterFactory
from utils import parse_binary_packet

def get_final_one_path(folder_path):
    files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]
    sorted_files = sorted(files, key=os.path.getmtime, reverse=True)
    last_one_files = sorted_files[:1]
    return last_one_files

class WindAndPressureScanner:
    """
    压力扫描阀与皮托管风速采集工具类
    支持UDP触发采集、风速计算、压力分布读取
    """
    def __init__(self, device_ip: str, data_path: str):
        self.device_ip = device_ip
        self.data_path = data_path

    def trigger_udp_acquisition(self):
        """
        通过UDP触发压力扫描阀采集数据
        """
        Ad = AdapterFactory().create_adapter('UDP')
        os.makedirs(self.data_path, exist_ok=True)
        Ad.initialize(self.device_ip, 503)
        Ad.W('B', 1)
        print("Sent command to start scanning.")
        x = self.device_ip[-3:] + str(datetime.fromtimestamp(time.time(), tz=timezone.utc).strftime('%Y_%m_%d_%H_%M_%S')) + '.csv'
        path = os.path.join(self.data_path, x)
        Ad.R(348, parse_binary_packet, True, file_path=path)
        print(f"数据已保存到: {path}")
        return path

    def get_latest_wind_velocity(self) -> float:
        """
        读取最新数据文件，计算风速（皮托管）
        """
        file_path = get_final_one_path(self.data_path)[0]
        data = pd.read_csv(file_path)
        m_data = data.iloc[:, 12].apply(lambda x: eval(x))
        first_values = [row[62] for row in m_data[:800]]
        second_values = [row[63] for row in m_data[:800]]
        avg_first_value = np.mean(first_values)
        avg_second_value = np.mean(second_values)
        pressure_diff = avg_first_value - avg_second_value
        wind_velocity = np.sqrt(2 * abs(pressure_diff) / 1.204)
        wind_velocity_revise = wind_velocity - 0.1
        return wind_velocity_revise

    def get_latest_pressure_distribution(self) -> list:
        """
        读取最新数据文件，提取23通道压力分布
        """
        file_path = get_final_one_path(self.data_path)[0]
        data = pd.read_csv(file_path)
        m_data = data.iloc[:, 12].apply(lambda x: eval(x))
        state_pressure = []
        for i in range(23):
            column_pressure = [row[i] for row in m_data[:800]]
            column_avg = sum(column_pressure) / len(column_pressure)
            state_pressure.append(column_avg)
        return state_pressure

# 示例用法
if __name__ == '__main__':
    scanner = WindAndPressureScanner('191.30.90.241', r'./test_data')
    scanner.trigger_udp_acquisition()
    wind = scanner.get_latest_wind_velocity()
    print(f"Wind velocity: {wind}")
    pressures = scanner.get_latest_pressure_distribution()
    print(f"Pressure distribution: {pressures}") 