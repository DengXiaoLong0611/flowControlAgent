import serial
import time
import pandas as pd
from typing import Optional

class WindFieldController:
    """
    风场发生器/可编程风扇阵列控制工具类
    支持全场、单行、单列、单风扇、Excel批量风场设定等
    """
    def __init__(self, upper_port: str, middle_port: str, lower_port: str, baudrate: int = 115200, timeout: float = 0.1):
        self.ser_upper = serial.Serial(upper_port, baudrate, timeout=timeout)
        self.ser_middle = serial.Serial(middle_port, baudrate, timeout=timeout)
        self.ser_lower = serial.Serial(lower_port, baudrate, timeout=timeout)
        time.sleep(1)

    def send_signal(self, board: str, command: str):
        send_str = command + '\n'
        if board == "upper":
            self.ser_upper.write(send_str.encode())
        if board == "middle":
            self.ser_middle.write(send_str.encode())
        elif board == "lower":
            self.ser_lower.write(send_str.encode())
        elif board == "both":
            self.ser_upper.write(send_str.encode())
            self.ser_middle.write(send_str.encode())
            self.ser_lower.write(send_str.encode())
        print(f"Sent: {send_str.strip()}")

    def feedback(self, serial_port, timeout: float):
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = serial_port.readline().decode().strip()
            if response:
                print(f"Received: {response}")
                start_time = time.time()
        print(f"Timeout: No response received within {timeout} seconds.")

    def control_all(self, pwm: int, time_series_option: bool = False, interval: Optional[int] = None):
        if time_series_option:
            if interval is None:
                raise ValueError("Interval must be provided when time_series_option is True")
            command = f"TS-start:{interval},{pwm}"
        else:
            command = f"All:{pwm}"
        self.send_signal("both", command)
        self.feedback(self.ser_upper, 5)

    def control_row(self, row_index: int, pwm: int):
        if row_index < 8:
            board = "upper"
            which_ser = self.ser_upper
        elif 8 <= row_index < 16:
            board = "middle"
            which_ser = self.ser_middle
        elif 16 <= row_index < 24:
            board = "lower"
            which_ser = self.ser_lower
        row_index = row_index % 8
        command = f"Row:{row_index},{pwm}"
        self.send_signal(board, command)
        self.feedback(which_ser, 3)

    def control_column(self, col_index: int, pwm: int):
        command = f"Column:{col_index},{pwm}"
        self.send_signal("both", command)
        self.feedback(self.ser_upper, 3)

    def control_single_fan(self, row_index: int, col_index: int, pwm: int):
        if row_index < 8:
            board = "upper"
            which_ser = self.ser_upper
        elif 8 <= row_index < 16:
            board = "middle"
            which_ser = self.ser_middle
        elif 16 <= row_index < 24:
            board = "lower"
            which_ser = self.ser_lower
        row_index = row_index % 8
        command = f"Single:{row_index},{col_index},{pwm}"
        self.send_signal(board, command)
        self.feedback(which_ser, 3)

    def control_terrain(self, excel_path: str):
        data = pd.read_excel(excel_path, header=0)
        pwm_data = data.iloc[:, 2].to_numpy()
        for i, pwm in enumerate(pwm_data):
            row_index = 24 - i - 1
            self.control_row(row_index, pwm)
            time.sleep(0.2)
        print("Terrain setting done.")

    def control_spanwise(self, excel_path: str):
        data = pd.read_excel(excel_path, header=0)
        pwm_data = data.iloc[:, 2].to_numpy()
        for i, pwm in enumerate(pwm_data):
            self.control_column(i, pwm)
            time.sleep(0.2)
        print("Spanwise setting done.")

    def control_timeserie(self, excel_path: str, interval: float):
        data = pd.read_excel(excel_path, header=0)
        pwm_data = data.iloc[:, 1].to_numpy()
        for index, pwm in enumerate(pwm_data):
            self.control_all(pwm)
            time.sleep(interval)
        print("Time series setting done.")

    def close(self):
        self.ser_upper.close()
        self.ser_middle.close()
        self.ser_lower.close()

# Example usage
if __name__ == '__main__':
    controller = WindFieldController('COM18', 'COM19', 'COM21')
    controller.control_timeserie('WT_1_control_V2.2-linearUp-500to1080rpm.xlsx', interval=1)
    controller.close() 