"""
PneumaticFlowController
======================

气管式吹吸气流量控制工具类。
- 支持通过Modbus协议设置流量、修改地址/模式、读取流量值等。
- 适用于风洞实验、主动流动控制等场景。

依赖：
    - modbus_tk
    - serial
    - AdapterFactory（通信协议适配器）

用法示例：
    from tools.flow_control.pneumatic_flow_controller import PneumaticFlowController
    controller = PneumaticFlowController(port='COM3', baudrate=9600)
    controller.set_flow_rate(device_id=1, value=2.5)
    flow = controller.read_cvalue(device_id=1)
    print(f"Current flow: {flow}")
    controller.close()
"""

from communication_protocol.Adapter import AdapterFactory
import modbus_tk.utils

class PneumaticFlowController:
    """
    气管式吹吸气流量控制工具类
    """
    def __init__(self, port: str, baudrate: int = 9600):
        """
        初始化流量控制器
        :param port: 串口号（如'COM3'）
        :param baudrate: 波特率，默认9600
        """
        logger = modbus_tk.utils.create_logger("console")
        self.adapter = AdapterFactory().create_adapter('modbus', logger=logger)
        self.adapter.initialize(port, baudrate, bytesize=8, parity='N', stopbits=1, xonxoff=0)

    def set_flow_rate(self, device_id: int, value: float):
        """
        设置指定设备的流量值
        :param device_id: Modbus设备地址
        :param value: 目标流量值
        """
        self.adapter.W(device_id, 106, wdata=value)

    def modify_address(self, device_id: int, new_addr: int):
        """
        修改设备Modbus地址
        :param device_id: 当前设备地址
        :param new_addr: 新地址
        """
        self.adapter.W(device_id, 120, wdata=new_addr)

    def modify_model(self, device_id: int, model: int):
        """
        修改设备工作模式
        :param device_id: 设备地址
        :param model: 模式编号
        """
        self.adapter.W(device_id, 116, wdata=model)

    def read_cvalue(self, device_id: int):
        """
        读取当前流量值
        :param device_id: 设备地址
        :return: 当前流量
        """
        return self.adapter.R(device_id, 28, 2)

    def read_ivalue(self, device_id: int):
        """
        读取瞬时流量值
        :param device_id: 设备地址
        :return: 瞬时流量
        """
        return self.adapter.R(device_id, 16, 2)

    def close(self):
        """
        关闭连接（如有需要）
        """
        # 若AdapterFactory有close方法可补充
        pass

# Example usage
if __name__ == '__main__':
    controller = PneumaticFlowController(port='COM3', baudrate=9600)
    controller.set_flow_rate(device_id=1, value=2.5)
    flow = controller.read_cvalue(device_id=1)
    print(f"Current flow: {flow}") 