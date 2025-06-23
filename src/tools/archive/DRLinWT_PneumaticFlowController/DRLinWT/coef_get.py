import pandas as pd
import numpy as np
import os

import time
from communication_protocol.FTP_server import Create_FTP_Server
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from get_data_udp import get_data
import scipy


status = '前吸'
def count_files_in_folder(folder_path):
    # 获取文件夹内所有文件和子文件夹的列表
    entries = os.scandir(folder_path)

    # 过滤掉子文件夹，只保留文件
    files = [entry.name for entry in entries if entry.is_file()]

    # 返回文件数量
    return len(files)

def files_in_folder(folder_path):
    # 获取文件夹内所有文件和子文件夹的列表
    entries = os.scandir(folder_path)

    # 过滤掉子文件夹，只保留文件
    files = [entry.name for entry in entries if entry.is_file()]

    # 返回文件数量
    return files

def are_all_files_not_readonly(folder_path):
    try:
        # 使用 os.listdir 获取文件夹内所有文件和子文件夹的列表
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        # 检查所有文件是否都不是只读
        return all(os.access(file, os.R_OK) for file in files)
    except FileNotFoundError:
        # 处理文件夹不存在的情况
        return False
    

def get_path():
    import os

    # 指定文件夹路径
    folder_path = 'disk1'  # 替换为你的文件夹路径

    # 获取文件夹内所有文件的路径
    files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]

    # 按修改时间对文件进行排序
    sorted_files = sorted(files, key=os.path.getmtime, reverse=True)

    # 获取最后两个文件名
    last_two_files = sorted_files[:2]
    return last_two_files


def get_coef(wind_velocity, action, postion):
    initial_path = f'data_{postion}'
    os.makedirs(initial_path, exist_ok=True)
    reget = False
    while not reget:
        path, reget = get_data(initial_path, wind_velocity, action)
    print(path)
    path_184 = os.path.join(path, '184.csv')
    path_241 = os.path.join(path, '241.csv')
    data184 = pd.read_csv(path_184, index_col=False, header=None)
    data241 = pd.read_csv(path_241, index_col=False, header=None)

    x =  np.array(data184.iloc[:, -3:])
    x = np.mean(x, axis=0)
    y = np.sqrt(2*abs(x[-2]-x[-1])/1.1846)
    print('Wind Velocity: ', y)
    print("total pressure: ", x[-1])
    print("static pressure: ", x[-2])
    
    pu2 = 0.5*1.1846*y*y
    dfA_subset = data184.iloc[:,:12] - x[-2]
    dfB_subset = data241.iloc[:,:13] - x[-2]
    dfC_subset = data241.iloc[:,32:44] - x[-2]
    dfD_subset = data184.iloc[:,45:58] - x[-2]
    
    
    xlsx = pd.concat([dfA_subset, dfC_subset, dfB_subset, dfD_subset], axis=1, ignore_index=True) # ACBD

    # xlsx = kalman_filter(xlsx, 50, 50)
    # xlsx = scipy.signal.savgol_filter(xlsx, 21, 2, axis = 0, mode = 'mirror')
    # xlsx = np.array(xlsx)
    
    # length = range(len(xlsx))
    # plt.plot(length, xlsx[:,0], linestyle='-', color='b', label = 'no_control', linewidth = 0.5)
    # plt.plot(length, xlsx1[:,0], linestyle='-', color='r', label = 'control', linewidth = 0.5)
    # plt.show()
    
    xlsx = pd.DataFrame(xlsx)
    xlsx_hole = pd.concat([dfA_subset.iloc[:,6:], dfB_subset.iloc[:,7:], dfC_subset.iloc[:,6:], dfD_subset.iloc[:,7:]], axis=1, ignore_index=True)
    xlsx_nohole = pd.concat([dfA_subset.iloc[:,0:6], dfB_subset.iloc[:,0:7], dfC_subset.iloc[:,0:6], dfD_subset.iloc[:,0:7]], axis=1, ignore_index=True)

    xlsx_path = os.path.join(initial_path, 'xlsx')
    xlsx_path = os.path.join(xlsx_path, f"{(int(y))}+" + f'{action}'+ f'+{time.time()}')
    os.makedirs(xlsx_path, exist_ok=True)
    xlsx_path = os.path.join(xlsx_path, 'result.csv')
    
    figure_path = os.path.join(initial_path, 'figure')
    os.makedirs(figure_path, exist_ok=True)
    figure_path = os.path.join(figure_path, f"{int(y)}+" + f'{action}'+ f'+{time.time()}'+ ' cd'+'.png')
    
    xlsx.to_csv(xlsx_path, mode='w', header=False, index=False)
    a = xlsx_hole.mean()
    b = xlsx_nohole.mean()
    column_means_hole = xlsx_hole.mean()/pu2
    column_means_nohole = xlsx_nohole.mean()/pu2
    plt.plot(column_means_hole.index, column_means_hole.values, marker='o', linestyle='-', color='b')
    plt.plot(column_means_nohole.index, column_means_nohole.values, marker='o', linestyle='-', color='r')
    plt.ylim(-3,1.5)
    plt.savefig(figure_path)
    plt.close()

    #AC面
    A_force = np.array([])
    C_force = np.array([])
    AC_force = np.array([])
    for i in range(0,xlsx.shape[0]):
        # area = float(xlsx.iloc[0,i])
        A_np_data = np.array(xlsx.iloc[i,0:12]).astype(np.float32)
        C_np_data = np.array(xlsx.iloc[i,12:24]).astype(np.float32)
        A_mean = np.mean(A_np_data)
        C_mean = np.mean(C_np_data)
        A_force = np.append(A_force, A_mean)
        C_force = np.append(C_force, C_mean)
        AC_force = np.append(AC_force, C_mean-A_mean)

    #BD面
    B_force = np.array([])
    D_force = np.array([])
    BD_force = np.array([])
    for i in range(0,xlsx.shape[0]):
        # area = float(xlsx.iloc[0,i])
        # B_np_data = np.array(xlsx.iloc[i,24:37]).astype(np.float32)
        # D_np_data = np.array(xlsx.iloc[i,37:50]).astype(np.float32)
        B_np_data = np.array(xlsx.iloc[i,30:37]).astype(np.float32)
        D_np_data = np.array(xlsx.iloc[i,43:50]).astype(np.float32)
        B_mean = np.mean(B_np_data)
        D_mean = np.mean(D_np_data)
        B_force = np.append(B_force, B_mean)
        D_force = np.append(D_force, D_mean)
        BD_force = np.append(BD_force, D_mean-B_mean)
        
    figure_path_1 = os.path.join(initial_path, 'figure')
    os.makedirs(figure_path_1, exist_ok=True)
    figure_path_1 = os.path.join(figure_path_1, f"{int(y)}+" + f'{action}'+ f'+{time.time()}'+ ' cl'+'.png')
    
    # cov = []
    # for i in range(len(BD_force)):
    #     cov.append(np.cov(B_force[:i]/pu2, D_force[:i]/pu2, rowvar=False)[0,1])
    # plt.plot(range(len(cov)), cov, linestyle='-', color='black', linewidth = 0.1)
    plt.plot(range(len(BD_force)), BD_force/pu2, linestyle='-', color='blue', linewidth = 0.1)
    # plt.plot(range(len(BD_force)), -1*B_force/pu2, linestyle='-', color='blue', linewidth = 0.1)
    # plt.plot(range(len(BD_force)), D_force/pu2, linestyle='-', color='red', linewidth = 0.1)
    plt.ylim(-2,2)
    plt.savefig(figure_path_1)
    plt.close()
    A_force = A_force/pu2
    B_force = B_force/pu2
    C_force = C_force/pu2
    D_force = D_force/pu2
    AC_force = AC_force/pu2
    BD_force = BD_force/pu2
    # combined_array = np.column_stack((A_force, B_force, C_force, D_force, AC_force, BD_force))
    # np.savetxt((os.path.splitext(path[-1])[0] + '.txt'), combined_array, fmt='%-8.3f', delimiter=',', header='Col1,Col2,Col3,Col4,Col5,Col6', comments='')
    # plt.plot(np.arange(len(BD_force)),BD_force)
    # plt.show()
    print(np.abs(np.mean((AC_force))), np.std(BD_force), np.mean(np.abs(BD_force)), np.mean(BD_force), np.sqrt(np.mean(np.square(BD_force))))
    return [np.abs(np.mean((AC_force))), np.std(BD_force), np.mean(np.abs(BD_force)), np.mean(BD_force), np.sqrt(np.mean(np.square(BD_force)))]

if __name__=='__main__':

    from NEW.flow_control import write_flow
    import threading
    hz = 5  # 5,8,10
    postion = 'back_blow'
    csv_file_path = 'output.csv'
    header = ['postion', 'wind_v', 'action', 'Mean_Cd', 'Std_Cl', 'Mean_abs_Cl', 'Mean_Cl']
    # 创建一个空的 DataFrame 只包含列标签
    df = pd.DataFrame(columns=header)
    # 将 DataFrame 写入 CSV 文件 
    # df.to_csv(csv_file_path, index=False, mode='a')
    for flow in range(20,30,10):
        # write_flow(flow)  
        time.sleep(10)
        flow=100000
        print('action: ', flow)
        for i in range(3):
            x = get_coef(hz, flow, postion)
            print(x)
            print('------------------------------')
            output_string = f"'position': '{postion}', 'wind_v': '{hz}', 'action': '{flow}', 'Mean_Cd': {x[0]}, 'Std_Cl': {x[1]}, 'Mean_abs_Cl': {x[2]}, 'Mean_Cl': {x[3]}"

            with open('result.txt','a') as f:
                f.write(output_string + '\n')

            # 追加一行数据
            new_data_row = {'postion': [postion], 'wind_v': [hz], 'action': [flow], 'Mean_Cd': [x[0]], 'Std_Cl': [x[1]], 'Mean_abs_Cl': [x[2]], 'Mean_Cl': [x[3]]}

            # 将新行追加到 DataFrame
            df = pd.concat([df, pd.DataFrame(new_data_row)], ignore_index=True)
            # df = pd.concat([df, pd.DataFrame(new_data_row)], ignore_index=True)

            # 将更新后的 DataFrame 写回 CSV 文件
            df.to_csv('output.csv', index=False, mode='a')

    # flow = 0
    # x = get_coef(8, flow)
    # print(x)


