import os
import time

import pyautogui
import shutil
import socket

def runClickOld():
    #这是之前测力天平的代码，现在不用了
    # 坐标依据实际情况调整
    pyautogui.click(x=710, y=848)
    x, y = pyautogui.position()
    print(f"当前鼠标坐标为：{x}, {y}")

def udp_client():
    # 创建UDP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 定义要发送的消息和目标地址
    message = b'001'
    server_address = ('localhost', 12345)

    try:
        # 发送数据包
        sock.sendto(message, server_address)
    finally:
        sock.close()

def runClick():
    udp_client()
    print(f"已发送点击信号")


def clickAndCreateData():
    runClick()

    # 停一下 等待让数据完成采集，这里停止的描述与让激光位移计采集的时间相关
    time.sleep(2.7)
    #print('runclick运行完毕,数据已经出现,现在去检查数据记录他测量到的位移rms，我在这里会暂停程序1分钟给您争取时间')
    #time.sleep(60)
   #print('检查完了，现在进入读取数据的环节')

    # # 拷贝 文件到预定目录 拷贝的路径src_file  拷贝道的路径dst_dir
    # src_file = r'C:\Users\admin\Desktop\dxlWindTunnel\Force\xiaoye-Multiple Transducers Folder V2\savedata\20230720-datalog.csv'
    # dst_dir = r'C:\qianghuafile\res'
    # ###当前时间
    # timestamp = int(time.time())
    # dst_file = f"file_{timestamp}.csv"
    # shutil.copy2(src_file, os.path.join(dst_dir, dst_file))

if __name__ == '__main__':
    runClick()
