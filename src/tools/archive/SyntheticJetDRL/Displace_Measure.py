
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.optimize as optimize
from scipy.signal import savgol_filter


pi = np.pi

def plot_sampled_data(filename):
    rms_value, sampled_data = read_csv_get_RMS_TimeHisDisp(filename)
    plt.plot(range(len(sampled_data)), sampled_data)
    plt.xlabel('Index')
    plt.ylabel('Sampled Data')
    plt.title('Plot of Sampled Data')
    plt.show()


def read_csv_file_timeformat(filename):
    data = pd.read_csv(filename,usecols=['Time', 'LaserPlacement1', 'LaserPlacement2', 'LaserPlacementAverage'])
    Time_values = data.iloc[1:150, 0].values
    # 将字符串转换为浮点数
    Time_values = Time_values.astype(float)
    LaserPlacement1_values = data.iloc[1:150, 1].values
    LaserPlacement2_values = data.iloc[1:150, 2].values
    LaserPlacementAverage_values = data.iloc[1:150, 3].values

    return Time_values, LaserPlacement1_values,LaserPlacement2_values,LaserPlacementAverage_values
def read_csv_file_GetDispRMS(filename): # 调用函数读取CSV文件

    rmsTabledata = pd.read_csv(filename, usecols = ['Time', 'LaserPlacement1', 'LaserPlacement2', 'LaserPlacementAverage'])
    LaserPlacement1_rms = rmsTabledata.iloc[0, 1]
    LaserPlacement2_rms = rmsTabledata.iloc[0, 2]
    LaserPlacementAverage_rms = rmsTabledata.iloc[0, 3]

    return LaserPlacement1_rms,LaserPlacement2_rms,LaserPlacementAverage_rms

def read_csv_get_RMS_TimeHisDisp(filename):
    # 读取CSV文件
    timehistorydata = pd.read_csv(filename, usecols=['Time', 'Laser1234Ave'])

    # 获取RMS行的Laser1234Ave值
    rms_value = timehistorydata.loc[timehistorydata['Time'] == 'RMS', 'Laser1234Ave'].values[0]

    # 获取最后5秒的Laser1234Ave数据
    last_5_seconds_data = timehistorydata['Laser1234Ave'].values[-2500:]

    # 生成300个在0到2500之间的均匀分布的索引
    indices = np.linspace(0, 2500, 300, endpoint=False).astype(int)

    # 使用这些索引来选择数据
    sampled_data = last_5_seconds_data[indices]

    return rms_value, sampled_data
import pandas as pd
import numpy as np

def read_csv_get_RMS_TimeHisDisp_1s(filename):
    # 读取CSV文件
    timehistorydata = pd.read_csv(filename, usecols=['Time', 'Laser1234Ave'])

    # 获取RMS行的Laser1234Ave值
    rms_value = timehistorydata.loc[timehistorydata['Time'] == 'RMS', 'Laser1234Ave'].values[0]

    # 获取最后0.99秒的Laser1234Ave数据
    # 假设采样率为2500个数据点对应5秒，即500个数据点对应1秒
    # 因此0.99秒对应495个数据点
    last_0_99seconds_data = timehistorydata['Laser1234Ave'].values[-495:]

    # 生成10个在0到495之间的均匀分布的索引
    indices = np.linspace(0, 495, 10, endpoint=False).astype(int)

    # 使用这些索引来选择数据
    sampled_data = last_0_99seconds_data[indices]

    return rms_value, sampled_data


# 调用函数读取CSV文件
#拟合正弦函数代码
def fitsinFunction():
    Time, Placement1, Placement2, PlacementAve = read_csv_file_timeformat('datacopy5.csv')
    Placement1_rms, Placement2_rms, PlacementAve_rms = read_csv_file_GetDispRMS('datacopy5.csv')

    # 使用Savitzky-Golay滤波器对曲线进行光顺处理
    PlacementAve = savgol_filter(PlacementAve, 20, 3)

    fig, ax = plt.subplots()
    ax.plot(Time, PlacementAve, 'b--')
    ax.plot(Time, PlacementAve, 'r--')

    # plt.show()

    # fig, ax = plt.subplots()
    # ax.plot(x, y, 'b--')

    def target_func(x, a0, a1, a2, a3):
        return a0 * np.sin(a1 * x + a2) + a3

    # 拟合sin曲线
    fs = np.fft.fftfreq(len(Time), Time[1] - Time[0])
    Y = abs(np.fft.fft(Time))
    freq = abs(fs[np.argmax(Y[1:]) + 1])
    a0 = max(PlacementAve) - min(PlacementAve)
    a1 = 2 * pi * freq
    a2 = 0
    a3 = np.mean(PlacementAve)
    p0 = [a0, a1, a2, a3]
    para, _ = optimize.curve_fit(target_func, Time, PlacementAve, p0=p0)
    print(para)
    PlacementAve_fit = [target_func(a, *para) for a in Time]
    ax.plot(Time, PlacementAve_fit, 'g')
    fita0 = para[0]
    fita1 = para[1]
    fita2 = para[2]
    fita3 = para[3]
    print("fita0=" + str(fita0))
    print("fita1=" + str(fita1))
    print("fita2=" + str(fita2))
    print("fita3=" + str(fita3))

    return fita0,fita1,fita2,fita3  #拟合正弦

#a1,b1,c1=read_csv_file_rms(r"C:\data\data.csv")

if __name__ == '__main__':
    print("这是主程序的逻辑代码部分")
    # fitsinFunction()
    filename=r'C:\data\data.csv'
    a,b=read_csv_get_RMS_TimeHisDisp(filename)
    print(a)
    print(b)
    plot_sampled_data('C:\data\data.csv')