from .wind_pressure_scanner import WindAndPressureScanner

class WindFieldVelocitySensor:
    """
    Wind field velocity sensor tool (Pitot tube principle)
    Only exposes wind velocity measurement related interface
    """
    def __init__(self, device_ip, data_path):
        self._scanner = WindAndPressureScanner(device_ip, data_path)
    def trigger(self):
        """Trigger acquisition"""
        self._scanner.trigger_udp_acquisition()
    def get_wind_velocity(self):
        """Get latest wind velocity"""
        return self._scanner.get_latest_wind_velocity()

# Example usage
if __name__ == '__main__':
    sensor = WindFieldVelocitySensor('191.30.90.241', './test_data')
    sensor.trigger()
    wind = sensor.get_wind_velocity()
    print(f"Wind velocity: {wind}") 