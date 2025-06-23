import os
import torch
import struct
import pandas as pd
import numpy as np
def get_last_filepath(folder_path):
    # 获取文件夹中所有文件
    all_files = os.listdir(folder_path)

    # 如果文件夹为空，返回 None
    if not all_files:
        return None

    # 对文件按照修改时间进行排序
    all_files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)))

    # 获取最后一个文件的相对路径
    last_filename = all_files[-1]
    last_filepath = os.path.join(folder_path, last_filename)
    return last_filepath

# 获取当前模型的参数
def get_model_parameters(model):
    parameters = []
    for param in model.parameters():
        parameters.append(param.clone())
    return parameters

# 计算参数之间的绝对差异
def compute_parameter_difference(params1, params2):
    diff = []
    for p1, p2 in zip(params1, params2):
        diff.append(torch.abs(p1 - p2))
    return diff


import struct

def ReadFloat(data, reverse=True):
    if len(data) == 2:
        format_char = '!f'  # 单精度浮点数格式
    elif len(data) == 4:
        format_char = '!d'  # 双精度浮点数格式
    else:
        raise ValueError("The length of data must be 2 or 4.")

    if reverse:
        data = data[::-1]

    # 将寄存器值转换回十六进制字符串，然后转换为字节
    y_hex = ''.join(['%04x' % reg for reg in data])
    y_bytes = bytes.fromhex(y_hex)

    # 解包字节为浮点数
    value = struct.unpack(format_char, y_bytes)[0]

    return value

def WriteFloat(value, num_registers=2, reverse=True):
    if num_registers == 2:
        y_bytes = struct.pack('!f', value)  # 打包浮点数为4字节
    elif num_registers == 4:
        y_bytes = struct.pack('!d', value)  # 打包浮点数为4字节
    else:
        raise ValueError("num_registers must be 2 or 4.")
    y_hex = ''.join(['%02x' % i for i in y_bytes])  # 将字节转换为十六进制字符串

    # 检查寄存器数量是否合适
    if num_registers * 4 < len(y_hex):
        raise ValueError("Not enough registers to store the float value")

    # 分割十六进制字符串以适应寄存器数量
    regs = [int(y_hex[i:i+4], 16) for i in range(0, len(y_hex), 4)]

    if reverse:
        regs = regs[::-1]

    return regs[:num_registers]

def ReadInt(registers, num_registers=1, reverse=True, signed=False):
    if num_registers == 1:
        format_char = '!h' if signed else '!H'  # 16-bit
    elif num_registers == 2:
        format_char = '!i' if signed else '!I'  # 32-bit
    else:
        raise ValueError("num_registers must be datalog or 2.")

    if reverse:
        registers = registers[::-1]

    # 将寄存器值转换回十六进制字符串，然后转换为字节
    y_hex = ''.join(['%04x' % reg for reg in registers])
    y_bytes = bytes.fromhex(y_hex)

    # 解包字节为整数
    value = struct.unpack(format_char, y_bytes)[0]

    return value

def WriteInt(value, num_registers=1, reverse=True):
    if num_registers == 1:
        format_char = '!H' if value >= 0 else '!h'  # Unsigned or signed 16-bit
    elif num_registers == 2:
        format_char = '!I' if value >= 0 else '!i'  # Unsigned or signed 32-bit
    else:
        raise ValueError("num_registers must be datalog or 2.")

    # 打包整数为字节
    y_bytes = struct.pack(format_char, value)
    y_hex = ''.join(['%02x' % i for i in y_bytes])  # 将字节转换为十六进制字符串

    # 分割十六进制字符串以适应寄存器数量
    regs = [int(y_hex[i:i+4], 16) for i in range(0, len(y_hex), 4)]

    if reverse:
        regs = regs[::-1]

    return regs

def parse_binary_packet(data):
    # 定义数据包的格式
    # 大端序，4字节整数，4字节浮点数，以及数组
    packet_format = 'I I I I f I I f I I I 8f 64f I I I I'
    
    # 解包数据
    unpacked_data = struct.unpack(packet_format, data)
    # print(unpacked_data)
    # 创建一个字典来存储解析的数据，以便更易于访问
    data_dict = {
        'packet_type': unpacked_data[0],
        'packet_size': unpacked_data[1],
        'frame_number': unpacked_data[2],
        'scan_type': unpacked_data[3],
        'frame_rate': unpacked_data[4],
        'valve_status': unpacked_data[5],
        'units_index': unpacked_data[6],
        'units_conversion_factor': unpacked_data[7],
        'ptp_scan_start_time_sec': unpacked_data[8],
        'ptp_scan_start_time_ns': unpacked_data[9],
        'external_trigger_time': unpacked_data[10],
        'temperatures': unpacked_data[11:19],  # 8 floats
        'pressures': unpacked_data[19:83],     # 64 floats or integers
        'frame_time_s': unpacked_data[83],
        'frame_time_ns': unpacked_data[84],
        'external_trigger_time_s': unpacked_data[85],
        'external_trigger_time_ns': unpacked_data[86]
    }   
    # print(data_dict)
    
    return data_dict


# 假设数据是通过 struct.pack('Iff', 42, 3.14, 2.718) 打包的
# 格式字符串 'Iff' 表示一个无符号整数和两个浮点数

def read_dat(file_path, num_bytes, key = False):
    with open(file_path, 'rb') as file:
        binary_data = file.read()
        # print(parse_binary_packet(binary_data))
        # print(binary_data.decode())
    # 解包二进制数据
    # unpacked_data = struct.unpack('Iff', binary_data)

    # 打印解包后的数据
    chunk_size = num_bytes
    start_index = 0
    # df = pd.DataFrame()
    dfs = []
    while start_index < len(binary_data):
        end_index = start_index + chunk_size
        data_chunk = binary_data[start_index:end_index]

        # 调用处理函数
        result = parse_binary_packet(data_chunk)

        # 处理结果，可以根据需要进行操作
        # print(result)
        if key == False:
            dfs.append(pd.Series(result))
        else:
            dfs.append(pd.Series(result[key]))
        # 更新起始索引
        start_index = end_index
    df = pd.concat(dfs, axis=1).T
    df.to_csv((os.path.join("disk1\csv", f"{os.path.splitext(os.path.basename(file_path))[0]}.csv")), mode='a', header=False, index=False)
    return df



if __name__=='__main__':
    value = 30
    registers = WriteFloat(value, num_registers=4)
    print(registers)
