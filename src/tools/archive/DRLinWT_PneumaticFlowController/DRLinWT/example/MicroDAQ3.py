import pandas as pd
import numpy as np
import os
import time
from communication_protocol.Adapter import AdapterFactory
from other.data_saving import is_string_or_list_of_strings
from datetime import datetime, timezone
from utils import parse_binary_packet
import threading

class MicroDAQ3():

    def __init__(self) -> None:
        pass
    def UDP_transfer_data(self, device_ip, data_path):
        Ad = AdapterFactory('UDP')
        initial_path = data_path
        os.makedirs(initial_path, exist_ok=True)
        if not is_string_or_list_of_strings(device_ip):
            print('The data type should be a string or a list of strings!')
        elif isinstance(device_ip, str):
            send_start_scan_command(Ad, device_ip, 503)
        elif ((len(device_ip) == 1) and isinstance(device_ip[0], str)):
            send_start_scan_command(Ad, device_ip[0], 503)
        else:
            sync_event = threading.Event()
            threads = []
            for ip in device_ip:
                t = threading.Thread(target=send_signal, args=(sync_event, Ad, ip, initial_path))
                t.start()
                threads.append(t)
                time.sleep(0.1)
            sync_event.set()
            for t in threads:
                t.join()

    def TCP_send_command(self, device_ip, command):
        Ad = AdapterFactory('TCP')
        if not is_string_or_list_of_strings(device_ip):
            print('The data type should be a string or a list of strings!')
        elif isinstance(device_ip, str):
            Ad.initialize(device_ip, 23)
            Ad.W(command)
        elif ((len(device_ip) == 1) and isinstance(device_ip[0], str)):
            Ad.initialize(device_ip[0], 23)
            Ad.W(command)
        else:
            for ip in device_ip:
                Ad.initialize(ip, 23)
                Ad.W(command)


def send_signal(sync_event, Ad, target_ip, target_port):
    sync_event.wait()
    send_start_scan_command(Ad, target_ip, target_port)

def send_start_scan_command(Ad, device_ip, initial_path):
    Ad.initialize(device_ip, 101)
    Ad.W('B', 1)
    print("Sent command to start scanning.")
    x = str(datetime.fromtimestamp(time.time(), tz=timezone.utc).strftime('%Y_%m_%d_%H_%M_%S'))+'.csv'
    path = os.path.join(initial_path, x)
    path = os.path.join(path, f'{device_ip}.csv')
    Ad.R(348, parse_binary_packet, True, file_path=path)












