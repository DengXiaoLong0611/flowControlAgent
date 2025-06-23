import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import math
import openpyxl

'角度（0-90，15间隔）、风速（没想好，预计五个风速）、伸出长度（0-20，2为间隔，后续处理成无量纲数L/D）'
# MPS15度用15
# coefy = np.array([0,0,0,0,0,0,0,15,13.5,13,13,13,13.5,15,0,0,0,0,0,0,0,-15,-13.5,-13,-13,-13,-13.5,-15])
# coefx = np.array([15,13.5,13,13,13,13.5,15,0,0,0,0,0,0,0,-15,-13.5,-13,-13,-13,-13.5,-15,0,0,0,0,0,0,0])
# coefy = np.array([0,0,0,0,0,0,0,17,13.5,13,13,13,13.5,17,0,0,0,0,0,0,0,-17,-13.5,-13,-13,-13,-13.5,-17])
# coefx = np.array([17,13.5,13,13,13,13.5,17,0,0,0,0,0,0,0,-17,-13.5,-13,-13,-13,-13.5,-17,0,0,0,0,0,0,0])
# coefy = np.array([0,0,0,0,0,0,0,16,13.5,13,13,13,13.5,16,0,0,0,0,0,0,0,-16,-13.5,-13,-13,-13,-13.5,-16])
# coefx = np.array([16,13.5,13,13,13,13.5,16,0,0,0,0,0,0,0,-16,-13.5,-13,-13,-13,-13.5,-16,0,0,0,0,0,0,0])
wind_angle = 0
if wind_angle > 10:
    coefy = np.array([0,0,0,0,0,0,0,14,13.5,13,13,13,13.5,14,0,0,0,0,0,0,0,-14,-13.5,-13,-13,-13,-13.5,-14])
    coefx = np.array([14,13.5,13,13,13,13.5,14,0,0,0,0,0,0,0,-14,-13.5,-13,-13,-13,-13.5,-14,0,0,0,0,0,0,0])
if wind_angle == 10:
    coefy = np.array([0,0,0,0,0,0,0,15,13.5,13,13,13,13.5,15,0,0,0,0,0,0,0,-15,-13.5,-13,-13,-13,-13.5,-15])
    coefx = np.array([15,13.5,13,13,13,13.5,15,0,0,0,0,0,0,0,-15,-13.5,-13,-13,-13,-13.5,-15,0,0,0,0,0,0,0])
if wind_angle < 10:
    coefy = np.array([0,0,0,0,0,0,0,17,13.5,13,13,13,13.5,17,0,0,0,0,0,0,0,-17,-13.5,-13,-13,-13,-13.5,-17])
    coefx = np.array([17,13.5,13,13,13,13.5,17,0,0,0,0,0,0,0,-17,-13.5,-13,-13,-13,-13.5,-17,0,0,0,0,0,0,0])

def combine():
    data_folder = 'data'
    subfolders = [f.path for f in os.scandir(data_folder) if f.is_dir()]
    latest_folder = subfolders[0]
    csv_file_path = os.path.join(latest_folder, 'Merged.csv')
    data = pd.read_csv(csv_file_path, skiprows=6, header=None)
    col_range_1 = list(range(2, 58))  # 第3列到第58列（列索引从0开始）
    col_range_2 = list(range(66, 96))  # 第67列到第96列
    df_1 = data.iloc[:, col_range_1]
    df_2 = data.iloc[:, col_range_2]
    merged_df = pd.concat([df_1, df_2], axis=1)

def calculate_cp():
    # filename_1 = f'data/data1.csv'
    # filename_2 = f'data/data2.csv'
    # df_1 = pd.read_csv(filename_1, skiprows=0, usecols=range(0, 56))
    # df_2 = pd.read_csv(filename_2, skiprows=0, usecols=range(0, 30))
    data_folder = 'data'
    subfolders = [f.path for f in os.scandir(data_folder) if f.is_dir()]
    latest_folder = subfolders[0]
    csv_file_path = os.path.join(latest_folder, 'Merged.csv')
    data = pd.read_csv(csv_file_path, skiprows=6, header=None)
    col_range_1 = list(range(2, 58))  # 第3列到第58列（列索引从0开始）
    col_range_2 = list(range(66, 96))  # 第67列到第96列
    df_1 = data.iloc[:, col_range_1]
    df_2 = data.iloc[:, col_range_2]
    
    merged_df = pd.concat([df_1, df_2], axis=1)
    still_pres = merged_df.iloc[:, -2]
    dyn_pres = (merged_df.iloc[:, -1] - merged_df.iloc[:, -2]).abs()  # 算动压
    merged_df = merged_df.iloc[:, :].subtract(still_pres, axis=0)  # 减去静压
    result_cp = merged_df.iloc[:, :-2].div(dyn_pres, axis=0)  # 求cp
    result_cp = result_cp.to_numpy()
    return result_cp

def draw_cp(data,case_name):
    cp = np.mean(data, axis=0)
    cp = cp.reshape(3,28)
    plt.figure(figsize=(28, 3), dpi=120)
    index_labels = np.arange(1, 4)#3行
    column_labels = np.arange(1, 29)#28列
    sns.heatmap(cp, cmap='jet', annot=True, fmt='.2f', vmin=-1.5, vmax=1.5, cbar=False, xticklabels=False,
                            yticklabels=False, linewidths=.5, linecolor='black')
    # 调整分割线
    cut_lines = np.arange(0.5, 28, 7)
    for m in cut_lines:
        plt.axvline(x=m - 0.5, color='k', linestyle='--', linewidth=1.5)
    '保存图片'
    folder_path = f'testpic/'
    os.makedirs(folder_path, exist_ok=True)
    pic_name = f'testpic/{case_name}.png'
    plt.savefig(pic_name,bbox_inches='tight',pad_inches=0.0)
    plt.close()

def calculate_f(data,angle):
    angle_w = math.radians(angle)
    wind_sin = math.sin(angle_w)
    wind_cos = math.cos(angle_w)
    result_cl = np.array([])
    result_cd = np.array([])
    row_vectors = [np.reshape(row, (1, -1)) for row in data]

    for row_vector in row_vectors:
        row_vector = row_vector.reshape(3, 28)
        row_vector = np.mean(row_vector, axis=0)
        result_fx = np.dot(row_vector, coefx)
        result_fy = np.dot(row_vector, coefy)

        cl = (result_fx * wind_cos + result_fy * wind_sin) / 100 
        cd = ( -result_fx * wind_sin + result_fy * wind_cos) / 100 
        result_cl = np.append(result_cl, cl)
        result_cd = np.append(result_cd, cd)

    cd_mean = np.mean(result_cd)
    cl_rms = np.sqrt(np.mean(result_cl ** 2))
    cl_mean = np.mean(result_cl)
    return cd_mean,cl_rms,cl_mean


#计算素体数据
case = f'case0t0'
result0_cp = calculate_cp()
draw_cp(result0_cp,case)
result_cd,result_cl,mcl=calculate_f(result0_cp,wind_angle)
print(result_cd,result_cl,mcl)
