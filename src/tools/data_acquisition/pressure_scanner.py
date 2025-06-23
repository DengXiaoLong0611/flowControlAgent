from .wind_pressure_scanner import WindAndPressureScanner

class PressureScanner:
    """
    压力扫描阀工具类
    只暴露压力分布测量相关接口
    """
    def __init__(self, device_ip, data_path):
        self._scanner = WindAndPressureScanner(device_ip, data_path)
    def trigger(self):
        """触发采集"""
        self._scanner.trigger_udp_acquisition()
    def get_pressure_distribution(self):
        """获取最新压力分布"""
        return self._scanner.get_latest_pressure_distribution()

# 示例用法
if __name__ == '__main__':
    scanner = PressureScanner('191.30.90.241', './test_data')
    scanner.trigger()
    pressures = scanner.get_pressure_distribution()
    print(f"Pressure distribution: {pressures}") 