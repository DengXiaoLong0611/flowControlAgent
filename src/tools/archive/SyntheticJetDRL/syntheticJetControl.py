# 修改合成射流的电压和频率作为action动作值


import time

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


# 修改后的set_signal_generator函数，去除合成射流开关
def set_signal_generator(voltage, modulation_frequency):
    carrier_frequency = 500  # 载波频率Hz，对合成射流压电片的驱动频率
    modulation_depth = 100  # 调制深度 %
    modulation_signal_type = 'SIN'  # 调制信号类型

    # 设置正弦波输出
    signal_generator.write(':SOUR1:FUNC SIN')
    signal_generator.write(f':SOUR1:FREQ {carrier_frequency}Hz')
    signal_generator.write(f':SOUR1:VOLT {voltage}VPP')
    signal_generator.write(':SOUR1:VOLT:OFFS 0V')

    # 配置AM调制
    signal_generator.write(':SOUR1:AM:STAT ON')  # 打开AM调制
    signal_generator.write(':SOUR1:AM:SOUR INT')  # 使用内部调制源
    signal_generator.write(f':SOUR1:AM:DEPT {modulation_depth}')  # 设置调制深度
    signal_generator.write(f':SOUR1:AM:INT:FUNC {modulation_signal_type}')  # 设置调制信号类型
    signal_generator.write(f':SOUR1:AM:INT:FREQ {modulation_frequency}Hz')  # 设置调制频率

    signal_generator.write(':OUTP1 ON')

    # 保留两位小数
    voltage = round(voltage, 2)
    modulation_frequency = round(modulation_frequency, 2)

    print(f"当前设定合成射流电压: {voltage}VPP")
    print(f"当前设定调制频率: {modulation_frequency}Hz")

def close_signal_generator():
    signal_generator.write(':OUTP1 OFF')
    signal_generator.close()



if __name__ == '__main__':
    # 仅在直接运行该脚本时执行以下代码
    print(signal_generator.query('*IDN?'))
    set_signal_generator(20, 6)
    time.sleep(3)
    close_signal_generator()