import serial
import time
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
from communication_protocol.Adapter import AdapterFactory
from utils import WriteFloat, ReadFloat

logger = modbus_tk.utils.create_logger("console")

class flow_controller():

    def __init__(self, port, baudrate):
        self.Ad = AdapterFactory().create_adapter('modbus', logger = logger)
        self.Ad.initialize(port, baudrate, bytesize=8, parity='N', stopbits=1, xonxoff=0)

    def set_flow_rate(self, n, x):
        # self.Ad.W(n, cst.WRITE_MULTIPLE_REGISTERS, 106,output_value=WriteFloat(x))
        self.Ad.W(n, 106, wdata=x)

    def modify_address(self, n,x):
        # self.Ad.W(n, cst.WRITE_MULTIPLE_REGISTERS, 120,output_value=WriteFloat(x))
        self.Ad.W(n, 120,wdata=x)
        
    def modify_model(self, n,x):
        self.Ad.W(n, 116,wdata=x)

    def read_cvalue(self, n):
        return self.Ad.R(n, 28, 2)
    
    def read_ivalue(self, n):
        return self.Ad.R(n, 16, 2)























