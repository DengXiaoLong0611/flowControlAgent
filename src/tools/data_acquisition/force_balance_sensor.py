import time
import pandas as pd
import socket

class ForceBalanceSensor:
    """
    三分力天平数据采集与处理工具类
    支持采集触发、三分力数据读取
    """
    def __init__(self, data_file_path: str):
        self.data_file_path = data_file_path

    def trigger_acquisition(self, wait_time: float = 2.7, udp_host: str = 'localhost', udp_port: int = 12345):
        """
        触发LabVIEW进行三分力天平数据采集
        :param wait_time: 采集后等待时间（秒）
        :param udp_host: UDP主机
        :param udp_port: UDP端口
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(b'001', (udp_host, udp_port))
        finally:
            sock.close()
        print(f"已发送三分力天平采集触发信号，等待{wait_time}秒...")
        time.sleep(wait_time)

    def get_latest_force(self) -> dict:
        """
        读取最新三分力（Fx, Fy, Fz）数据
        :return: {'Fx': float, 'Fy': float, 'Fz': float}
        """
        df = pd.read_csv(self.data_file_path)
        # 假设CSV文件有'Fx', 'Fy', 'Fz'三列，取最后一行数据
        fx = df['Fx'].iloc[-1]
        fy = df['Fy'].iloc[-1]
        fz = df['Fz'].iloc[-1]
        print(f"Fx: {fx}, Fy: {fy}, Fz: {fz}")
        return {'Fx': fx, 'Fy': fy, 'Fz': fz}

# 示例用法
if __name__ == '__main__':
    sensor = ForceBalanceSensor(r'C:/data/force_data.csv')
    sensor.trigger_acquisition()
    force = sensor.get_latest_force()
    print(f"Latest force: {force}") 