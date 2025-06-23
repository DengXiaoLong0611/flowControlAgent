import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys

# sys.path.append(r"C:\Users\HIT\Documents\Arduino\python_module")
# import WT_2_mode_byHH as Mode
# Mode.Activate_system()
# Mode.Constant_forAll(0)

# import pyautogui
# # 获取当前鼠标位置
# time.sleep(4)
# x, y = pyautogui.position()
# print(f"当前鼠标位置: ({x}, {y})")

# import control as con
# con.reset_fin()
# print('ok') 

# time.sleep(5)
# ext=np.array([10,10,10,10])
# con.ctrl_fin(ext)
# print('222')
# time.sleep(10)
# con.reset_fin()
# print('333')


# 读取CSV文件
df = pd.read_csv('data.csv')

# 提取指定列
data_column = df['reward']  # 替换为实际的列名

# 计算滑动平均值
window_size = 10
moving_average = data_column.rolling(window=window_size).mean()

# 移除前(window_size - 1)个NaN值
moving_average = moving_average.dropna().reset_index(drop=True)

# 绘制图形
plt.style.use('seaborn-darkgrid')

plt.plot(moving_average, label=f'Moving Average (window={window_size})', color='blue')

plt.title('Moving Average of Column Data')
plt.xlabel('Index')
plt.ylabel('Average Value')
plt.legend()
plt.show()