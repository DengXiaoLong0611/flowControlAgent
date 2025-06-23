import serial
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import telnetlib
from utils import ReadFloat, WriteFloat
import socket
import struct
from typing import Any, Callable, Dict, List, Optional, Union
import pandas as pd


class AdapterFactory:
    def __init__(self):
        pass

    def get_adapter(self, **kwargs):
        if self.protocol_type in ('modbus' , 'MODBUS'):
            return ModbusAdapter(**kwargs)
        elif self.protocol_type in ('serial' , 'SERIAL'):
            return SerialAdapter(**kwargs)
        elif self.protocol_type in ('telnet' , 'TELNET'):
            return TelnetAdapter(**kwargs)
        elif self.protocol_type in ('tcp' , 'TCP'):
            return TCPAdapter(**kwargs)
        elif self.protocol_type in ('udp' , 'UDP'):
            return UDPAdapter(**kwargs)
        else:
            raise ValueError(f"Unsupported protocol type: {self.protocol_type}")
        

    def create_adapter(self, protocol_type, **kwargs):
        self.protocol_type = protocol_type
        return self.get_adapter(**kwargs)
    
    
class SerialAdapter(serial.Serial):

    def initialize(self, port = None, baudrate = None, timeout = 5, config = None, **kwargs):
        if config:
            port = config['port']
            baudrate = config['baudrate']   
            timeout = config['timeout'] 
            print('Config from config file!')

        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=timeout, **kwargs)
        except serial.SerialException as e:
            print(f"Error opening the serial port: {e}")
        
    def W(self, command):
        bytes_data = command.encode('utf-8')
        bytes_written = self.serial_port.write(bytes_data)
        if bytes_written != len(bytes_data):
            print("Not all data written to serial port.")

    def R(self):
        data =[]
        while True:
            line = self.serial_port.readline()  # 读取一行数据
            if line:  # 如果读到数据
                line_decode = line.decode().strip()
                data.append(line_decode)
                print("Received:", line_decode)  # 打印接收到的数据
            else:
                print("No new data received. Exiting due to timeout.")
                break  # 如果超时没有读到数据，则退出循环
        return data

class ModbusAdapter():
    def __init__(self, logger = True) -> None:
        if logger == True:
            self.logger = modbus_tk.utils.create_logger("console")
        else:
            self.logger = logger

    def initialize(self, port = None, baudrate = None, timeout = 5, config = None, **kwargs):
        if config:
            port = config['port']
            baudrate = config['baudrate']   
            timeout = config['timeout'] 
            print('Config from config file!')

        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=timeout, **kwargs)
        except serial.SerialException as e:
            print(f"Error opening the serial port: {e}")

    def W(self, address, start_register, wdata):
        try:
            master = modbus_rtu.RtuMaster(self.serial_port)
            master.set_timeout(1.0)
            master.set_verbose(True)
            self.logger.info("connected")   
        except modbus_tk.modbus.ModbusError as exc:
            self.logger.error("%s- Code=%d", exc, exc.get_exception_code())
        
        try:
            convert_wdata = WriteFloat(wdata)
            result = master.execute(address, cst.WRITE_MULTIPLE_REGISTERS, start_register, output_value=[convert_wdata[0], convert_wdata[1]])
        except modbus_tk.modbus.ModbusError as exc:
            self.logger.error("%s- Code=%d", exc, exc.get_exception_code())
        
        master.close()
        return result
    
    def R(self, address, start_register, num_register):
        try:
            master = modbus_rtu.RtuMaster(self.serial_port)
            master.set_timeout(1.0)
            master.set_verbose(True)
            self.logger.info("connected")   
        except modbus_tk.modbus.ModbusError as exc:
            self.logger.error("%s- Code=%d", exc, exc.get_exception_code())
        
        try:
            data = ReadFloat(master.execute(address, cst.READ_HOLDING_REGISTERS, start_register, num_register))
            print('get_data: ',data)
        except modbus_tk.modbus.ModbusError as exc:
            self.logger.error("%s- Code=%d", exc, exc.get_exception_code())
        
        master.close()
        return data

class TelnetAdapter(telnetlib.Telnet):

    def initialize(self, ip_address = None, port = None, timeout = 5, config = None, **kwargs):
        if config:
            # 如果传入了config字典，则从中读取配置参数
            self.ip_address = config['ip_address']
            self.port = config['port']
            self.time_out = config['time_out '] 
            print('Config from config file!')   
        else:
            self.ip_address = ip_address
            self.port = port
            self.time_out = timeout  

    def W(self, command):
        with telnetlib.Telnet(self.ip_address, self.port, timeout = self.time_out) as tn:
            tn.write(command.encode('ascii') + b"\n")
            response = tn.read_until(b"$ ", timeout=5)  # 这里的 "$ " 是设备的提示符，可能需要适应设备
            return response.decode('ascii')
                                                            
    def R(self):
        with telnetlib.Telnet(self.ip_address, self.port, timeout = self.time_out) as tn:
            # 读取 Telnet 服务端口的数据
            telnet_data = tn.read_all().decode('ascii')
            return telnet_data

class TCPAdapter(socket.socket):

    def initialize(self, ip_address = None, port = None, timeout = 5, config = None, **kwargs):
        if config:
            ip_address = config['ip_address']
            port = config['port']  
            timeout = config['timeout'] 
            print('Config from config file!')

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(timeout)
        self.client_socket.connect((ip_address, port))

    def W(self, type, data):
        # 发送启动扫描的命令（发送1）
        command_data = struct.pack(type, data)
        self.client_socket.sendall(command_data)

    def R(self, frame_bytes, data_processing:Callable, save:bool, file_path:str, names = None, key = False):
        # data_processing可以参照utils中的parse_binary_packet
        if save:
            dfs = []
        while True:
            try:
                data_chunk = self.client_socket.recv(frame_bytes)
            except socket.timeout:
                print("Timeout occurred")
                pass

            try:
                if key == False:
                    data_chunk = data_processing(data_chunk)
                else:
                    data_chunk = data_processing(data_chunk)[key]
            except Exception as e:
                print(f"An unexpected error occurred: {type(e).__name__}")
                break
            dfs.append(pd.Series(data_chunk))
        if save:
            df = pd.concat(dfs, axis=1).T
            df.to_csv(file_path, mode='a', header=False, index=False)

        return dfs

class CANAdapter_usb2can():
    "Please use dll"
    pass

class NIDAQ():
    pass

class UDPAdapter(socket.socket):

    def initialize(self, ip_address = None, port = None, timeout = 5, config = None):
        if config:
            ip_address = config['ip_address']
            port = config['port']  
            timeout = config['timeout'] 
            print('Config from config file!')

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(timeout)
        self.client_socket.connect((ip_address, port))

    def W(self, type, data):
        # 发送启动扫描的命令（发送1）
        command_data = struct.pack(type, data)
        self.client_socket.sendall(command_data)

    def R(self, frame_bytes, data_processing:Callable, save:bool, file_path:str, names = None, key = False):
        # data_processing可以参照utils中的parse_binary_packet
        if save:
            dfs = []
        while True:
            try:
                data_chunk = self.client_socket.recv(frame_bytes)
            except socket.timeout:
                # print("Timeout occurred")
                pass

            try:
                if key == False:
                    data_chunk = data_processing(data_chunk)
                else:
                    data_chunk = data_processing(data_chunk)[key]
            except Exception as e:
                # print(f"An unexpected error occurred: {type(e).__name__}")
                break
            if save:
                dfs.append(pd.Series(data_chunk))
        if save:
            df = pd.concat(dfs, axis=1).T
            df.to_csv(file_path, mode='a', header=False, index=False)

        return dfs




