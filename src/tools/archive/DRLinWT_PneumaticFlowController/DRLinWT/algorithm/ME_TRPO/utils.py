import os
import torch


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