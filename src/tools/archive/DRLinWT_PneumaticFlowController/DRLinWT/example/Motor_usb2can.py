import ctypes
from ctypes import *
import time
# 加载DLL
nimotion_can_dll = ctypes.WinDLL(r'C:\Users\HIT\Desktop\新建文件夹 (2)\NiMotionUSBCAN.dll')
STATUS_OK = 1
VCI_USBCAN2 = 3
class VCI_INIT_CONFIG(Structure):  
    _fields_ = [("AccCode", c_uint),
                ("AccMask", c_uint),
                ("Reserved", c_uint),
                ("Filter", c_ubyte),
                ("Timing0", c_ubyte),
                ("Timing1", c_ubyte),
                ("Mode", c_ubyte)
                ]  
    
class VCI_CAN_OBJ(Structure):  
    _fields_ = [("ID", c_uint),
                ("TimeStamp", c_uint),
                ("TimeFlag", c_ubyte),
                ("SendType", c_ubyte),
                ("RemoteFlag", c_ubyte),
                ("ExternFlag", c_ubyte),
                ("DataLen", c_ubyte),
                ("Data", c_ubyte*8),
                ("Reserved", c_ubyte*3)
                ] 
    
ret = nimotion_can_dll.NiM_OpenDevice(3, 0)
if ret == STATUS_OK:
    print('调用 NiM_OpenDevice成功\r\n')
if ret != STATUS_OK:
    print('调用 NiM_OpenDevice出错\r\n')

vci_initconfig = VCI_INIT_CONFIG(0x80000000, 0xFFFFFFFF, 0,
                                1, 0x00, 0x14, 0)#波特率1000k，正常模式

ret = nimotion_can_dll.NiM_InitCAN(3, 0, 0, byref(vci_initconfig))
if ret == STATUS_OK:
    print('调用 NiM_OpenDevice成功\r\n')
if ret != STATUS_OK:
    print('调用 NiM_OpenDevice出错\r\n')


ret = nimotion_can_dll.NiM_StartCAN(3, 0, 0)
if ret == STATUS_OK:
    print('调用 NiM_StartCAN1成功\r\n')
if ret != STATUS_OK:
    print('调用 NiM_StartCAN1出错\r\n')


def send_sdo(a,b,c,d,e,f,g,h):
    #通道1发送数据
    ubyte_array = c_ubyte*8
    x = ubyte_array(a,b,c,d,e,f,g,h)
    ubyte_3array = c_ubyte*3
    y = ubyte_3array(0,0,0)
    vci_can_obj = VCI_CAN_OBJ(0x602, 0, 0, 0, 0, 0,  8, x, y)
    
    ret = nimotion_can_dll.NiM_Transmit(3, 0, 0, byref(vci_can_obj), 1)

    import ctypes
    class VCI_CAN_OBJ_ARRAY(Structure):
        _fields_ = [('SIZE', ctypes.c_uint16), ('STRUCT_ARRAY', ctypes.POINTER(VCI_CAN_OBJ))]

        def __init__(self,num_of_structs):
                                                                    #这个括号不能少
            self.STRUCT_ARRAY = ctypes.cast((VCI_CAN_OBJ * num_of_structs)(),ctypes.POINTER(VCI_CAN_OBJ))#结构体数组
            self.SIZE = num_of_structs#结构体长度
            self.ADDR = self.STRUCT_ARRAY[0]#结构体数组地址  byref()转c地址
        
    rx_vci_can_obj = VCI_CAN_OBJ_ARRAY(2500)#结构体数组

    ret = nimotion_can_dll.NiM_Receive(VCI_USBCAN2, 0, 0, byref(rx_vci_can_obj.ADDR), 2500, 0)
    print(ret)
    while ret <= 0:#如果没有接收到数据，一直循环查询接收。
            ret = nimotion_can_dll.NiM_Receive(VCI_USBCAN2, 0, 0, byref(rx_vci_can_obj.ADDR), 2500, 0)
            
    if ret > 0:#接收到一帧数据
        id = hex(vci_can_obj.ID)
        vci_can_obj = list(vci_can_obj.Data)
        vci_can_obj = [hex(i) for i in vci_can_obj]
        print(id,vci_can_obj)
        rx_id = hex(rx_vci_can_obj.ADDR.ID)
        rx_vci_can_obj = list(rx_vci_can_obj.ADDR.Data)
        rx_vci_can_obj = [hex(i) for i in rx_vci_can_obj]
        print(rx_id,rx_vci_can_obj)
        return rx_vci_can_obj

def bytestohexstring(data):
    temp = []
    for i in data:
        temp.append('0x%02X'%i)
    return temp



def set_velocity(v):
    v = hex(v)
    v= v[2:].rjust(4,'0')
    v = bytestohexstring(bytes.fromhex(v))
    send_sdo(0x22,0x02,0x20,0x01,0x00,0x00,0x00,0x00)
    send_sdo(0x22,0x60,0x60,0x00,0x02,0x00,0x00,0x00)
    send_sdo(0x22,0x42,0x60,0x00,int(v[1],base = 16),int(v[0],base = 16),0x00,0x00)
    send_sdo(0x22,0xff,0x60,0x00,int(v[1],base = 16),int(v[0],base = 16),0x00,0x00)
    send_sdo(0x22,0x48,0x60,0x01,0x08,0x3e,0x00,0x00)
    send_sdo(0x22,0x49,0x60,0x02,0x02,0x00,0x00,0x00)
    send_sdo(0x22,0x40,0x60,0x00,0x06,0x00,0x00,0x00)
    send_sdo(0x22,0x40,0x60,0x00,0x07,0x00,0x00,0x00)
    send_sdo(0x22,0x40,0x60,0x00,0x7f,0x00,0x00,0x00)

def stop():
    send_sdo(0x22,0x40,0x60,0x00,0x00,0x00,0x00,0x00)

def change_velocity(v):
    n = hex(int(v))
    n= n[2:].rjust(4,'0')
    n = bytestohexstring(bytes.fromhex(n))
    send_sdo(0x22,0x42,0x60,0x00,int(n[1],base = 16),int(n[0],base = 16),0x00,0x00)
    if get_velocity() == 0:
        set_velocity(v)

def get_velocity():
    v = send_sdo(0x40,0x6c,0x60,0x00,0x00,0x00,0x00,0x00) 
    v = v[7][2:]+v[6][2:]+v[5][2:]+v[4][2:]
    v = int(v,base=16)
    # print(v)
    return v

def close():
    nimotion_can_dll.VCI_CloseDevice(VCI_USBCAN2, 0) 
    
if __name__ == '__main__':
    # change_velocity(2000)
    # # # time.sleep(3)
    # # # get_velocity(200)
    stop()
    # set_velocity(1000)
    # get_velocity()
    pass







