import gym
import numpy as np
import pandas as pd
import time
from gym import spaces
import coef_get as cg
import control as con
import sys
import calculate_cp as cc
import os
import shutil

def clear_directory(directory_path):
    # 检查目录是否存在
    if not os.path.exists(directory_path):
        print(f"目录 {directory_path} 不存在！")
        return
    
    # 遍历目录中的所有内容并删除
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.remove(item_path)  # 删除文件或符号链接
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # 删除文件夹及其内容
            print(f"已删除: {item_path}")
        except Exception as e:
            print(f"无法删除 {item_path}: {e}")


angle = 45
for i in range(2,21,2):
    con.ctrl_fin([i, 0, 0, 0])
    time.sleep(6)
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')

con.ctrl_fin([0, 0, 0, 0])
time.sleep(8)

for i in range(2,21,2):
    con.ctrl_fin([0, i, 0, 0])
    time.sleep(6)
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')

con.ctrl_fin([0, 0, 0, 0])
time.sleep(8)

for i in range(2,21,2):
    con.ctrl_fin([0, 0, i, 0])
    time.sleep(6)
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')

con.ctrl_fin([0, 0, 0, 0])
time.sleep(8)

for i in range(2,21,2):
    con.ctrl_fin([0, 0, 0, i])
    time.sleep(6)
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')
    cg.para_get()
    cc.para(angle)
    clear_directory('data')