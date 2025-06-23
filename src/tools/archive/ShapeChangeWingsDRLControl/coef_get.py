import calculate_cp as cc
import numpy as np
import time
import pyautogui as ui 
import os
import shutil
from datetime import datetime
import pandas as pd


def para_get():
    print('SCAN START!')
    get_data()
    time.sleep(10)
    get_merged()
    time.sleep(0.8)
    print('SCAN OVER!')

# 获取测压信息，getcoef为整合函数
def get_coef(angle):
    print('SCAN START!')
    get_data()
    time.sleep(10)
    get_merged()
    time.sleep(0.8)
    print('SCAN OVER!')
    cd,cl,cp = cc.cal_coef(angle)
    return cd,cl,cp


# 清空测压文件
def remove_data1():
    # 定义文件夹路径
    source_folder = 'data'  # 已存在的测压文件夹
    # 获取当前日期和时间
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    # 创建目标文件夹路径
    destination_folder = f'trash/data_{current_time}'  # 目标文件夹
    # 创建新文件夹
    os.makedirs(destination_folder, exist_ok=True)
    # 获取source_folder中的所有文件
    files = os.listdir(source_folder)
    # 移动文件到新文件夹
    for file in files:
        source_file = os.path.join(source_folder, file)
        destination_file = os.path.join(destination_folder, file)
        shutil.move(source_file, destination_file)

def remove_data2(angle,order=0):
    # 定义文件夹路径
    source_folder = 'data'  # 已存在的测压文件夹
    # 获取当前日期和时间
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    # 创建目标文件夹路径,order=1时触发reset文件夹
    destination_folder = f'backup/{angle}/{current_time}RESET' if order == 1 else f'backup/{angle}/{current_time}'
    # 创建新文件夹
    os.makedirs(destination_folder, exist_ok=True)
    # 获取source_folder中的所有文件
    files = os.listdir(source_folder)
    # 移动文件到新文件夹
    for file in files:
        source_file = os.path.join(source_folder, file)
        destination_file = os.path.join(destination_folder, file)
        shutil.move(source_file, destination_file)


# 点击屏幕，控制软件开始测压
def get_data():
    # 旧阀MPS获取鼠标当前位置
    ui.FAILSAFE = False
    ui.click(86, 46, button='left')
    ui.click(103, 67, button='left')
# 旧阀测压结束，开始Merge文件
def get_merged():
    # 旧阀MPS获取鼠标当前位置
    ui.FAILSAFE = False
    ui.click(25, 45, button='left')
    ui.click(53, 65, button='left')
    time.sleep(1)
    ui.click(993, 700, button='left')
    

# def get_data():
#     # 新阀CHELL获取鼠标当前位置
#     ui.FAILSAFE = False
#     ui.click(95, 378, button='left')

def get_rezero():
    print('REZERO!')
    ui.FAILSAFE = False
    ui.click(99, 254, button='left')
    time.sleep(1)
    ui.click(99, 254, button='left')
    ui.click(99, 254, button='left')
    ui.click(99, 254, button='left')
    ui.click(99, 254, button='left')

# 设置0-5-10-15-30-45度下CD CL CP的参考值
def get_refer(angle):
    # 读取 CSV 文件
    df = pd.read_csv(f'REFER/R3/refer{angle}X.csv',nrows=5, header=None)
    # 提取5行数据（索引为5）
    mean_values = df.mean().values
    # 赋值
    cd_refer = round(mean_values[0], 3)
    cl_refer = round(mean_values[1], 3)
    cp_refer = [round(val, 3) for val in mean_values[2:]]
    print(cd_refer, cl_refer)
    return cd_refer, cl_refer, cp_refer


if __name__ == "__main__":
    # time.sleep(2)
    # get_data()
    # time.sleep(20)
    # get_merged()
    # print('ok')
    get_refer(10)