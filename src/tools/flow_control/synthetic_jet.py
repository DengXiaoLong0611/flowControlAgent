import time
from typing import List, Optional

try:
    import pyvisa
except ImportError:
    pyvisa = None

class SyntheticJetController:
    """
    合成射流信号发生器控制工具类
    支持设置电压、调制频率、开关、批量应用等功能
    """
    def __init__(self, resource_name: Optional[str] = None):
        if pyvisa is None:
            raise ImportError("pyvisa 库未安装，无法控制信号发生器。")
        self.rm = pyvisa.ResourceManager()
        resources = self.rm.list_resources()
        if resource_name is None:
            if not resources:
                raise RuntimeError("未检测到任何VISA设备。请检查连接。")
            resource_name = resources[0]
        self.signal_generator = self.rm.open_resource(resource_name)
        # 查询并打印设备信息（可选）
        print(f"信号发生器信息: {self.signal_generator.query('*IDN?')}")

    def set(self, voltage: float, modulation_frequency: float, carrier_frequency: float = 500, modulation_depth: float = 100, modulation_signal_type: str = 'SIN'):
        """
        当触发这个函数的时候
        计数器=0
        计数器+=1


        设置合成射流信号发生器参数
        :param voltage: 电压(VPP)
        :param modulation_frequency: 调制频率(Hz)
        :param carrier_frequency: 载波频率(Hz)
        :param modulation_depth: 调制深度(%)
        :param modulation_signal_type: 调制信号类型
        """
        sg = self.signal_generator
        sg.write(':SOUR1:FUNC SIN')
        sg.write(f':SOUR1:FREQ {carrier_frequency}Hz')
        sg.write(f':SOUR1:VOLT {voltage}VPP')
        sg.write(':SOUR1:VOLT:OFFS 0V')
        sg.write(':SOUR1:AM:STAT ON')
        sg.write(':SOUR1:AM:SOUR INT')
        sg.write(f':SOUR1:AM:DEPT {modulation_depth}')
        sg.write(f':SOUR1:AM:INT:FUNC {modulation_signal_type}')
        sg.write(f':SOUR1:AM:INT:FREQ {modulation_frequency}Hz')
        sg.write(':OUTP1 ON')
        print(f"当前设定合成射流电压: {round(voltage,2)}VPP")
        print(f"当前设定调制频率: {round(modulation_frequency,2)}Hz")

    def close(self):
        """关闭信号发生器输出并断开连接"""
        self.signal_generator.write(':OUTP1 OFF')
        self.signal_generator.close()
        print("信号发生器已关闭")

    def apply_voltage_sequence(self, voltage_sequence: List[float], interval: float = 8.0, modulation_frequency: float = 3.0):
        """
        按序列批量设置电压，常用于测试或部署
        :param voltage_sequence: 电压序列
        :param interval: 每次设置间隔（秒）
        :param modulation_frequency: 调制频率（Hz）
        """
        for voltage in voltage_sequence:
            self.set(voltage, modulation_frequency)
            print(f"Applied voltage: {voltage}V")
            time.sleep(interval)

# 示例用法
if __name__ == '__main__':
    controller = SyntheticJetController()
    controller.set(20, 6)
    time.sleep(3)
    controller.close() 