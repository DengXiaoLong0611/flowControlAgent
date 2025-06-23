import serial
import time
import pandas as pd

# 设置串口参数，替换为你的Arduino设备对应的串口
ser_upper = serial.Serial('COM18', 115200, timeout=0.1)
ser_middle = serial.Serial('COM19', 115200, timeout=0.1)
ser_lower = serial.Serial('COM21', 115200, timeout=0.1)
time.sleep(1)



def send_signal(board: str, command: str):
    """
    向指定的板子发送信号，并附加换行符。
    :param board: 选择 "upper" 或 "middle" 或 "lower" 或 "both"
    :param command: 命令字符串
    """
    send_str = command + '\n'
    if board == "upper":
        ser_upper.write(send_str.encode())
    if board == "middle":
        ser_middle.write(send_str.encode()) 
    elif board == "lower":
        ser_lower.write(send_str.encode())
    elif board == "both":
        ser_upper.write(send_str.encode())
        ser_middle.write(send_str.encode()) 
        ser_lower.write(send_str.encode())
    print(f"Sent: {send_str.strip()}")


def feedback(serial_port, timeout: float):
    """
    从指定的串口读取反馈信息，直到超时。
    :param serial_port: 串口对象
    :param timeout: 超时时间（秒）
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = serial_port.readline().decode().strip()
        if response:
            print(f"Received: {response}")
            start_time = time.time()  # 重置计时器
    print(f"Timeout: No response received within {timeout} seconds.")


def control_all(pwm: int, time_series_option: bool = False, interval: int = None):
    """
    向所有板子发送控制信号。
    :param pwm: PWM 值
    :param time_series_option: 是否启用时间序列模式
    :param interval: 时间序列模式的时间间隔（秒）
    """
    if time_series_option:
        if interval is None:
            raise ValueError("Interval must be provided when time_series_option is True")
        command = f"TS-start:{interval},{pwm}"
    else:
        command = f"All:{pwm}"
    send_signal("both", command)
    feedback(ser_upper, 5)


def control_row(row_index: int, pwm: int):
    """
    控制指定行的 PWM 设置。
    :param row_index: 行索引(0-23)
    :param pwm: PWM 值
    """
    if row_index < 8:
        board = "upper"
        which_ser = ser_upper
    elif  8 <= row_index < 16 :
        board = "middle"
        which_ser = ser_middle
    elif  16 <= row_index < 24 :
        board = "lower"
        which_ser = ser_lower
    row_index = row_index % 8  # 调整行索引
    # 发信号并读取反馈
    command = f"Row:{row_index},{pwm}"
    send_signal(board, command)
    feedback(which_ser, 3)


def control_column(col_index: int, pwm: int):
    """
    控制指定列的 PWM 设置。
    :param col_index: 列索引(0-31)
    :param pwm: PWM 值
    """
    command = f"Column:{col_index},{pwm}"
    send_signal("both", command)
    feedback(ser_upper, 3)


def control_single_fan(row_index: int, col_index: int, pwm: int):
    """
    控制单个风扇。
    :param row_index: 行索引(0-23)
    :param col_index: 列索引(0-31)
    :param pwm: PWM 值
    """
    if row_index < 8:
        board = "upper"
        which_ser = ser_upper
    elif  8 <= row_index < 16 :
        board = "middle"
        which_ser = ser_middle
    elif  16 <= row_index < 24 :
        board = "lower"
        which_ser = ser_lower
    row_index = row_index % 8  # 调整行索引
    # 发信号并读取反馈
    command = f"Single:{row_index},{col_index},{pwm}"
    send_signal(board, command)
    feedback(which_ser, 3)



def control_terrain(path: str):
    """
    根据 Excel 文件设置梯度风。
    :param path: Excel 文件路径
    """
    data = pd.read_excel(path, header=0)
    pwm_data = data.iloc[:, 2].to_numpy()
    for i, pwm in enumerate(pwm_data):
        row_index = 24 - i - 1
        control_row(row_index, pwm)
        time.sleep(0.2)  # 延时避免冲突
    print("Terrain setting done.")


def control_spanwise(path: str):
    """
    根据 Excel 文件设置展向风。
    :param path: Excel 文件路径
    """
    data = pd.read_excel(path, header=0)
    pwm_data = data.iloc[:, 2].to_numpy()
    for i, pwm in enumerate(pwm_data):
        control_column(i, pwm)
        time.sleep(0.2)  # 延时避免冲突
    print("Spanwise setting done.")


def control_timeserie(path: str, interval: float):
    """
    根据 Excel 文件设置全场时程风。
    :param path: Excel 文件路径
    :param interval: 每个时程信号的间隔(s)
    """
    data = pd.read_excel(path, header=0)
    pwm_data = data.iloc[:, 1].to_numpy()
    while True:
        for index, pwm in enumerate(pwm_data):
            control_all(pwm)
            time.sleep(interval)  # 延时避免冲突
    print("Time seires done.")


'''
Notice: 设置指令字符串，并通过串口传输，控制风扇
        指令格式为 "command:param1,param2,param3........", command代表指令，param代表该指令模式下对应参数，指令与参数间通过字符":"分隔，参数之间通过字符"，"分隔
        示例：预设指令 All ，代表设置全体风扇，参数为PWM值，如设置全体风扇1000PWM，可设定指令为 "All:1000"
        
        命令集： All:pwm
                TS-start:end_pwm,interval
                Row:row_index,pwm
                Column:col_index,pwm
                Single:row_index,col_index,pwm
'''


# 示例调用
control_timeserie('WT_1_control_V2.2-linearUp-500to1080rpm.xlsx', interval=1)
# control_terrain(r'E:\HIT_LW\LW-0.6H-YY.xlsx')
# control_all(0)
# control_row(17,1000)
# control_column(7,2000)
# control_single_fan(8, 8, 1000)



