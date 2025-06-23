# 修改合成射流的电压和频率作为action动作值

import pyvisa
import time
import pandas as pd
import pyvisa

# 初始化VISA资源管理器
rm = pyvisa.ResourceManager()

# 列出所有资源
resources = rm.list_resources()

# 打印所有资源名称
for resource in resources:
    print(resource)

resource_name = 'USB0::0x1AB1::0x0643::DG8A251401257::INSTR'
signal_generator = rm.open_resource(resource_name)

# 查询并打印设备信息（仅用于调试）
print(signal_generator.query('*IDN?'))

# action, _states = model.predict(obs, deterministic=True)
# set_signal_generator(*action)

def set_signal_generator(voltage, modulation_frequency):

    carrier_frequency = 500  # 载波频率Hz，对合成射流压电片的驱动频率
    modulation_depth = 100  # 调制深度 %
    modulation_signal_type = 'SIN'  # 调制信号类型

    # 设置正弦波输出
    signal_generator.write(':SOUR1:FUNC SIN')
    signal_generator.write(f':SOUR1:FREQ {carrier_frequency}Hz')
    signal_generator.write(f':SOUR1:VOLT {voltage}VPP')
    signal_generator.write(':SOUR1:VOLT:OFFS 0V')  #这段代码signal_generator.write(':SOUR1:VOLT:OFFS 0V')是用来设置信号发生器的偏移电压的。在这里，偏移电压被设置为0伏特。这意味着生成的信号将在0伏特的基线上进行振荡，即信号的正半周期和负半周期将在0伏特的基线上等距离分布。

    # 配置AM调制
    signal_generator.write(':SOUR1:AM:STAT ON')  # 打开AM调制
    signal_generator.write(':SOUR1:AM:SOUR INT')  # 使用内部调制源
    signal_generator.write(f':SOUR1:AM:DEPT {modulation_depth}')  # 设置调制深度
    signal_generator.write(f':SOUR1:AM:INT:FUNC {modulation_signal_type}')  # 设置调制信号类型
    signal_generator.write(f':SOUR1:AM:INT:FREQ {modulation_frequency}Hz')  # 设置调制频率

    signal_generator.write(':OUTP1 ON')

    #保留两位小数
    voltage = round(voltage, 2)
    modulation_frequency = round(modulation_frequency, 2)

    print(f"当前设定合成射流电压: {voltage}VPP")
    print(f"当前设定调制频率: {modulation_frequency}Hz")

def close_signal_generator():
    signal_generator.write(':OUTP1 OFF')
    signal_generator.close()

# Adding the logic to update the voltage every x seconds
def apply_voltage_sequence(voltage_sequence, interval=8):
    for voltage in voltage_sequence:
        set_signal_generator(voltage, modulation_frequency=3)  # Assuming modulation_frequency is fixed at 3
        print(f"Applied voltage: {voltage}V")
        time.sleep(interval)

def load_voltage_sequence_from_csv(file_path):
    # Load the CSV file
    traj_data = pd.read_csv(file_path)

    # Extract SJ_v column values (assuming 'SJ_v' as the identifier for the voltage)
    voltage_sequence = traj_data[traj_data['Unnamed: 0'] == 'SJ_v'].iloc[0, 1:].astype(float).tolist()

    return voltage_sequence


if __name__ == '__main__':
    # 仅在直接运行该脚本时执行以下代码
    # print(signal_generator.query('*IDN?'))
    # set_signal_generator(19.54, 3)
    # time.sleep(3)
    # close_signal_generator()


    voltage_sequence=load_voltage_sequence_from_csv(r'D:\Research\Papers\1_paperwork\PHD_7thPaper_空气动力学报_基于深度强化学习的桥梁涡激振动流动控制\PlotCode\data\DRLtransientNo1Fix3FreqVoltage0-20VWind720RPMNoEnergyTerm\testDeploy\1500step\traj.csv')
    # Extracted SJ_v values from the traj.csv file
    # voltage_sequence = [9.172, 6.547, 6.295, 8.928, 10.722]  # Placeholder for the extracted SJ_v values
    apply_voltage_sequence(voltage_sequence)
    close_signal_generator()
