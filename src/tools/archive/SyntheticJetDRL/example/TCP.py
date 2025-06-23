import telnetlib

def set_port(ip_address, port, time_out=5):
    client_socket = telnetlib.Telnet(ip_address, port, timeout = time_out)
    return client_socket

def send_data(ip_address, port, command, time_out=5):
    with telnetlib.Telnet(ip_address, port, timeout = time_out) as tn:
        tn.write(command.encode('ascii') + b"\n")
        response = tn.read_until(b"$ ", timeout=5)  # 这里的 "$ " 是设备的提示符，可能需要适应设备
        return response.decode('ascii')
                                                        
def receive_data(ip_address, port,time_out=5):
    with telnetlib.Telnet(ip_address, port, timeout = time_out) as tn:
        # 读取 Telnet 服务端口的数据
        telnet_data = tn.read_all().decode('ascii')
        return telnet_data
    
if __name__=='__main__':

    # 你的设备的 IP 地址
    device_ip2 = '191.30.90.241'  # 你的设备的实际 IP 地址

    # 发送 Telnet 命令并接收响应
    telnet_command_to_send = 'CALZ'
    telnet_response2 = send_data(device_ip2, 23, telnet_command_to_send)

    print('Received response:', telnet_response2)
