import numpy as np
import os
import time
from communication_protocol.Adapter import AdapterFactory
from tools.data_saving import is_string_or_list_of_strings, is_list_of_strings
from datetime import datetime, timezone
from utils import parse_binary_packet
import threading


class MPS4264():

    def __init__(self, device_ip):
        self.device_ip = device_ip


    def UDP_transfer_data(self, device_ip, data_path):
        Ad = AdapterFactory().create_adapter('UDP')
        initial_path = data_path
        os.makedirs(initial_path, exist_ok=True)
        if not is_string_or_list_of_strings(device_ip):
            print('The data type should be a string or a list of string!')
        elif isinstance(device_ip, str):
            send_start_scan_command(Ad, device_ip, initial_path)
        elif ((len(device_ip) == 1) and isinstance(device_ip[0], str)):
            send_start_scan_command(Ad, device_ip[0], initial_path)


    def TCP_send_command(self, device_ip, command):
        Ad = AdapterFactory().create_adapter('TCP')
        if not is_string_or_list_of_strings(device_ip):
            print('The data type should be a string or a list of strings!')
        elif isinstance(device_ip, str):
            Ad.initialize(device_ip, 23)
            Ad.W(f'{len(command)}s',command.encode('ascii') + b"\n")
        elif ((len(device_ip) == 1) and isinstance(device_ip[0], str)):
            Ad.initialize(device_ip[0], 23)
            Ad.W(command)
        else:
            for ip in device_ip:
                Ad.initialize(ip, 23)
                Ad.W(command)
    
    def Double_UDP_transfer_data(self, device_ip, data_path, info1='info1', info2 = 'info2'):
        Ad_1 = AdapterFactory().create_adapter('UDP')
        Ad_2 = AdapterFactory().create_adapter('UDP')
        initial_path = data_path
        os.makedirs(initial_path, exist_ok=True)
        sync_event = threading.Event()
        if not is_list_of_strings(device_ip):
            print('The data type should be a list of strings!')
        else:
            thread1 = threading.Thread(target=send_signal, args=(sync_event, Ad_1, device_ip[0], data_path))
            thread1.setDaemon(True)
            thread2 = threading.Thread(target=send_signal, args=(sync_event, Ad_2, device_ip[1], data_path))
            thread2.setDaemon(True)
            # 启动线程
            thread1.start()
            thread2.start()

            # 设置事件，确保两个线程开始执行
            sync_event.set()

            # 等待线程结束
            thread1.join()
            thread2.join()

        gather_path = get_final_two_path(data_path) # 获得最新两个文件的文件名
        print('file_name: ',gather_path)

        if device_ip[0][-3:] in gather_path[-1]:
            data1 = pd.read_csv(gather_path[-2], header=None).iloc[:, [9, 12]]
            data0 = pd.read_csv(gather_path[-1], header=None).iloc[:, [9, 12]]
        else:
            data0 = pd.read_csv(gather_path[-2], header=None).iloc[:, [9, 12]]
            data1 = pd.read_csv(gather_path[-1], header=None).iloc[:, [9, 12]]


        time_start_0 = data0.iloc[0,0]
        time_start_1 = data1.iloc[0,0]
        print(time_start_0, time_start_1)
        num_gap = int(abs(time_start_0-time_start_1)/1250000)  # 仅适用于800hz，并且ptpen设置1和2
        print('num_gap: ', num_gap)
        if time_start_0 > time_start_1:
            data0 = data0.iloc[:-num_gap, 1]
            data1 = data1.iloc[num_gap:, 1]
        elif time_start_0 < time_start_1:
            data1 = data1.iloc[:-num_gap, 1]
            data0 = data0.iloc[num_gap:, 1]
        else:
            data0 = data0.iloc[:,1]
            data1 = data1.iloc[:,1]

        
        # 创建当前时间命名的文件夹
        current_time = datetime.fromtimestamp(time.time(), tz=timezone.utc).strftime('%Y_%m_%d_%H_%M_%S')
        folder_path = os.path.join(data_path, str(info1))
        folder_path = os.path.join(folder_path, str(info2))
        folder_path = os.path.join(folder_path, current_time)

        # 确保目标文件夹存在，如果不存在则创建
        os.makedirs(folder_path, exist_ok=True)

        # 保存两个 DataFrame 到 CSV 文件
        def process_row(row):
            # 使用 eval() 解析字符串中的 Python 表达式，并转换为 NumPy 数组
            row_array = pd.Series(eval(row))
            return row_array

        dfs_0 = []
        dfs_1 = []

        for i in data0.values:
            dfs_0.append(process_row(i))
            
        for j in data1.values:
            dfs_1.append(process_row(j))
            
        dfs_0 = pd.concat(dfs_0, axis=1).T
        dfs_1 = pd.concat(dfs_1, axis=1).T
        dfs_0.to_csv(os.path.join(folder_path, '0.csv'), index=False, header=False)
        dfs_1.to_csv(os.path.join(folder_path, 'datalog.csv'), index=False, header=False)
        return folder_path, (num_gap < 50)

def send_signal(sync_event, Ad, target_ip, target_port):
    sync_event.wait()
    send_start_scan_command(Ad, target_ip, target_port)

def send_start_scan_command(Ad, device_ip, initial_path):
    Ad.initialize(device_ip, 503)
    Ad.W('B', 1)
    print("Sent command to start scanning.")
    x = device_ip[-3:]+str(datetime.fromtimestamp(time.time(), tz=timezone.utc).strftime('%Y_%m_%d_%H_%M_%S'))+'.csv'
    os.makedirs(initial_path, exist_ok=True)
    path = os.path.join(initial_path, x)
    Ad.R(348, parse_binary_packet, True, file_path=path)

def get_final_two_path(folder_path):
    import os

    # 获取文件夹内所有文件的路径
    files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]

    # 按修改时间对文件进行排序
    sorted_files = sorted(files, key=os.path.getmtime, reverse=True)

    # 获取最后两个文件名
    last_two_files = sorted_files[:2]
    return last_two_files

def get_final_one_path(folder_path):
    import os

    # 获取文件夹内所有文件的路径
    files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]

    # 按修改时间对文件进行排序
    sorted_files = sorted(files, key=os.path.getmtime, reverse=True)

    # 获取最后两个文件名
    last_one_files = sorted_files[:1]
    return last_one_files

def computeWindVelocity(folder_path):
    # 读取CSV文件
    file_path =folder_path
    data = pd.read_csv(file_path)

    # 提取第13列中的数据，并将字符串形式的元组转换为元组
    m_data = data.iloc[:, 12].apply(lambda x: eval(x))

    # 计算每一行的风速
    wind_velocities = []
    for row in m_data:
        pressure = row[62] - row[63]
        wind_velocity = np.sqrt(2 * abs(pressure) / 1.204)
        wind_velocities.append(wind_velocity)

    # 计算800个风速的平均值
    scan_wind_velocity = np.mean(wind_velocities[:800])
    return scan_wind_velocity


import pandas as pd

def DRLstate_WindPressureScan(folder_path):
    # 读取CSV文件
    file_path = folder_path
    data = pd.read_csv(file_path)

    # 提取第13列中的数据，并将字符串形式的元组转换为元组
    m_data = data.iloc[:, 12].apply(lambda x: eval(x))

    # 分别计算第1列到第23列数字在800行采样中的平均值
    state_pressure = []
    for i in range(23):
        column_pressure = [row[i] for row in m_data[:800]]
        column_avg = sum(column_pressure) / len(column_pressure)
        state_pressure.append(column_avg)

    # 函数最后返回这个列表state_pressure
    return state_pressure



def computeWindVelocity2(folder_path):
    # 读取CSV文件
    file_path = folder_path
    data = pd.read_csv(file_path)

    # 提取第13列中的数据，并将字符串形式的元组转换为元组
    m_data = data.iloc[:, 12].apply(lambda x: eval(x))

    # 分别计算第63个和第64个数字在800行采样中的平均值
    first_values = [row[62] for row in m_data[:800]]
    second_values = [row[63] for row in m_data[:800]]

    avg_first_value = np.mean(first_values)
    avg_second_value = np.mean(second_values)

    # print(avg_first_value)
    # print(avg_second_value)

    # 计算压力差
    pressure_diff = avg_first_value - avg_second_value

    # 用伯努利原理计算风速
    wind_velocity = np.sqrt(2 * abs(pressure_diff) / 1.204)
    wind_velocity_revise =wind_velocity-0.1
    return wind_velocity_revise




if __name__ == '__main__':
        scanWindVelocity=MPS4264('191.30.90.241')
        data_path = r'D:\Research\PHDProject\Code\Code_running\PHD_Bridge_DRL\syntheticJet_DRL\example\test'
        scanWindVelocity.UDP_transfer_data('191.30.90.241', data_path)
        pathfile=get_final_one_path(r'/2025-1-success-backup/example/test')
        scanWindVelocity=computeWindVelocity2(pathfile[0])
        print(scanWindVelocity)
        state_pressure=DRLstate_WindPressureScan(pathfile[0])
        print(state_pressure)
        # print(pathfile)
        # print(type(pathfile))









