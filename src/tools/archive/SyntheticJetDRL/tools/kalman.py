import numpy as np
from filterpy.kalman import KalmanFilter
import pandas as pd
import matplotlib.pyplot as plt

def kalman_filter(data, dim_x, dim_z):
    my_filter = KalmanFilter(dim_x=dim_x, dim_z=dim_x)

    my_filter.x = np.zeros((dim_x, 1))       # initial state (location and velocity)

    my_filter.F = np.eye(dim_x)       # state transition matrix

    my_filter.H = np.eye(dim_x)    # Measurement function
    my_filter.P *= 1.                 # covariance matrix
    my_filter.R *= 0.001                  # state uncertainty
    my_filter.Q *= 0.0001             # process uncertainty
    # Q表示对模型的信任程度，R表示对量测的信任程度，卡尔曼滤波是在模型和量测之间进行均衡。
    # 如果Q为零，那么我们只相信预测值；Q值越大我们对于预测的信任度就越低，而对测量值的信任度就变高；
    # 自我总结：Q值越打，会更加保留原本数据中的总体变化趋势，而R值越小，会更加保留围绕这个总体大趋势下的小趋势
    # Q为预测误差，R为测量误差
    i = 0
    kalman_data = []
    while True:
        my_filter.predict()
        my_filter.update(data[i,:])

        # do something with the output
        x = my_filter.x
        kalman_data.append(x.reshape(1,dim_z).squeeze())
        if (i+1) == len(data):
            break
        i += 1

    # 绘图
    # length = range(len(data))
    # plt.plot(length, data, linestyle='-', color='b', label = 'no_control', linewidth = 0.5)
    # plt.plot(length, kalman_data, linestyle='-', color='r', label = 'control', linewidth = 0.5)
    # plt.show()
    
    return np.array(kalman_data)


if __name__=='__main__':

    header = ['position', 'wind_v', 'action', 'Mean_Cd', 'Std_Cl', 'Mean_abs_Cl', 'Mean_Cl']
    # Load DataFrame from the CSV file and remove rows where 'position' is NaN
    df = pd.read_csv('output.csv', names = header)
    df = df.dropna(subset=['Std_Cl'])
    data = np.array(pd.concat((df['Std_Cl'], df['Std_Cl']), axis=1))
    # print(data)
    # print(data[1813])
    # data = data[:100]
    a = kalman_filter(data, 2, 2)
    print(a)















