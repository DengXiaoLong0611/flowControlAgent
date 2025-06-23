import os
import torch
import struct

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

def ReadFloat(*args,reverse=False):
    for n,m in args:
        n,m = '%04x'%n,'%04x'%m
    if reverse:
        v = n + m
    else:
        v = m + n
    y_bytes = bytes.fromhex(v)
    y = struct.unpack('!f',y_bytes)[0]
    y = round(y,6)
    return y

def WriteFloat(value,reverse=False):
    y_bytes = struct.pack('!f',value)
    # y_hex = bytes.hex(y_bytes)
    y_hex = ''.join(['%02x' % i for i in y_bytes])
    n,m = y_hex[:-4],y_hex[-4:]
    n,m = int(n,16),int(m,16)
    if reverse:
        v = [n,m]
    else:
        v = [m,n]
    return v

def ReadDint(*args,reverse=False):
    for n,m in args:
        n,m = '%04x'%n,'%04x'%m
    if reverse:
        v = n + m
    else:
        v = m + n
    y_bytes = bytes.fromhex(v)
    y = struct.unpack('!i',y_bytes)[0]
    return y

def WriteDint(value,reverse=False):
    y_bytes = struct.pack('!i',value)
    # y_hex = bytes.hex(y_bytes)
    y_hex = ''.join(['%02x' % i for i in y_bytes])
    n,m = y_hex[:-4],y_hex[-4:]
    n,m = int(n,16),int(m,16)
    if reverse:
        v = [n,m]
    else:
        v = [m,n]
    return v

def parse_binary_packet(data):
    # 定义数据包的格式
    # 大端序，4字节整数，4字节浮点数，以及数组
    packet_format = 'I I I I I I I f I I I 8f 64f I I I I'
    
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
    print(data_dict)
    
    return data_dict


# 假设数据是通过 struct.pack('Iff', 42, 3.14, 2.718) 打包的
# 格式字符串 'Iff' 表示一个无符号整数和两个浮点数

def read_dat(file_path, num_bytes):
    with open('disk1\SCAN20150101_000118.DAT', 'rb') as file:
        binary_data = file.read()
        # print(parse_binary_packet(binary_data))
        # print(binary_data.decode())
    # 解包二进制数据
    # unpacked_data = struct.unpack('Iff', binary_data)

    # 打印解包后的数据
    chunk_size = 348
    start_index = 0
    data = []
    while start_index < len(binary_data):
        end_index = start_index + chunk_size
        data_chunk = binary_data[start_index:end_index]

        # 调用处理函数
        result = parse_binary_packet(data_chunk)

        # 处理结果，可以根据需要进行操作
        print(result)
        data.appned(result)

        # 更新起始索引
        start_index = end_index

        return data

    