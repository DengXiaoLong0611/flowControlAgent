import pandas as pd
import numpy as np
import os
import math


# 合并测压文件
def combine():
    # 找到最新的文件夹
    data_folder = 'data'
    subfolders = [f.path for f in os.scandir(data_folder) if f.is_dir()]
    latest_folder = subfolders[0]
    csv_file_path = os.path.join(latest_folder, 'Merged.csv')
    data = pd.read_csv(csv_file_path, skiprows=6, header=None)
    col_range_1 = list(range(2, 58))  # 第3列到第58列（列索引从0开始）
    col_range_2 = list(range(66, 96))  # 第67列到第96列
    df_1 = data.iloc[:, col_range_1]
    df_2 = data.iloc[:, col_range_2]
    # filename_1 = f'data/data1.csv'
    # filename_2 = f'data/data2.csv'
    # df_1 = pd.read_csv(filename_1, skiprows=0, usecols=range(0, 56))
    # df_2 = pd.read_csv(filename_2, skiprows=0, usecols=range(0, 30))
    merged_df = pd.concat([df_1, df_2], axis=1)  # 按行拼接
    return merged_df

# 计算风速风压
def cal_cpv(data):
    still_pres = data.iloc[:, -2] # 算静压
    dyn_pres = (data.iloc[:, -1] - data.iloc[:, -2]).abs()  # 算动压
    merged_df = data.iloc[:, :].subtract(still_pres, axis=0)  # 减去静压
    result_cp = merged_df.iloc[:, :-2].div(dyn_pres, axis=0)  # 除以动压求cp
    result_cp = result_cp.to_numpy() # 转化成数组
    return result_cp

def cal_cp(data):
    cp_m=np.mean(data, axis=0)
    cp_m=cp_m.reshape(3,28)
    cp_m=np.mean(cp_m, axis=0)
    cp_m=np.round(cp_m,3)
    return cp_m

# 计算风力系数
def cal_coef(angle):
    data = combine()
    cp = cal_cpv(data)
    cp_mean=cal_cp(cp)
    if angle > 10:
        coefy = np.array([0,0,0,0,0,0,0,14,13.5,13,13,13,13.5,14,0,0,0,0,0,0,0,-14,-13.5,-13,-13,-13,-13.5,-14])
        coefx = np.array([14,13.5,13,13,13,13.5,14,0,0,0,0,0,0,0,-14,-13.5,-13,-13,-13,-13.5,-14,0,0,0,0,0,0,0])
    if angle == 10:
        coefy = np.array([0,0,0,0,0,0,0,15,13.5,13,13,13,13.5,15,0,0,0,0,0,0,0,-15,-13.5,-13,-13,-13,-13.5,-15])
        coefx = np.array([15,13.5,13,13,13,13.5,15,0,0,0,0,0,0,0,-15,-13.5,-13,-13,-13,-13.5,-15,0,0,0,0,0,0,0])
    if angle < 10:
        coefy = np.array([0,0,0,0,0,0,0,17,13.5,13,13,13,13.5,17,0,0,0,0,0,0,0,-17,-13.5,-13,-13,-13,-13.5,-17])
        coefx = np.array([17,13.5,13,13,13,13.5,17,0,0,0,0,0,0,0,-17,-13.5,-13,-13,-13,-13.5,-17,0,0,0,0,0,0,0])
    angle_w = math.radians(angle)
    wind_sin = math.sin(angle_w)
    wind_cos = math.cos(angle_w)
    result_cl = np.array([])
    result_cd = np.array([])
    row_vectors = [np.reshape(row, (1, -1)) for row in cp]
    for row_vector in row_vectors:
        row_vector = row_vector.reshape(3, 28)
        row_vector = np.mean(row_vector, axis=0)
        result_fx = np.dot(row_vector, coefx)
        result_fy = np.dot(row_vector, coefy)

        cl = (result_fx * wind_cos + result_fy * wind_sin) / 100
        cd = (- result_fx * wind_sin + result_fy * wind_cos) / 100
        result_cl = np.append(result_cl, cl)
        result_cd = np.append(result_cd, cd)
    cd_mean = np.mean(result_cd)
    cl_rms = np.sqrt(np.mean(result_cl ** 2))
    cd_mean = round(cd_mean,3)
    cl_rms = round(cl_rms,3)

    return cd_mean, cl_rms, cp_mean

def para(i):
    angle_0=i
    cd,cl,cp = cal_coef(angle_0)
    print(cd,cl)
    data_row = [cd, cl, *cp]
    df = pd.DataFrame([data_row])
    df.to_csv(f'REFER/R3/refer{i}X.csv', mode='a', index=False, header=False)

if __name__ == "__main__":
    angle_0=45
    cd,cl,cp = cal_coef(angle_0)
    print(cd,cl)
    data_row = [cd, cl, *cp]
    df = pd.DataFrame([data_row])
    df.to_csv(f'REFER/R3/refer{angle_0}X.csv', mode='a', index=False, header=False)
    