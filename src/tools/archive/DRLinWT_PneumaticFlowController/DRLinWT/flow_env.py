import gym as gym
import numpy as np
import pandas as pd
import time
from gym import spaces
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from communication_protocol.FTP_server import Create_FTP_Server
from MPS4264 import MPS4264
from example.flow_controller import flow_controller
from matplotlib import pyplot as plt


ips = ['191.30.90.242', '191.30.90.241']
def get_file_path(folder_path):
    import os
    import glob

    # 使用glob获取所有文件
    files = glob.glob(os.path.join(folder_path, '*'))

    # 按文件名排序
    sorted_files = sorted(files)

    # 获取最后一个文件
    if sorted_files:
        last_file = sorted_files[-1]
        print(f"The last file in the folder is: {last_file}")
    else:
        print("The folder is empty.")

    return last_file


class myEnv_flow(gym.Env):
    def __init__(self):
        self.num_envs = 1
        self.training_num = 1
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,),dtype=np.float32) # 动作空间
        self.observation_space = spaces.Box(low=-1.0, high=5.0, shape=(1,),dtype=np.float32) # 动作空间
        # self.observation_space = spaces.Box(low=np.array([0.0, 0.0, 0.0]), high=np.array([5.0, 5.0, 5.0]),dtype=np.float32) # 状态空间
        # self.observation_space = spaces.Box(low=np.array([0.0]), high=np.array([5.0]),dtype=np.float32) # 状态空间
        self.t = 0
        try:
            self.traj = pd.read_csv('traj.csv')
        except:
            self.traj = pd.DataFrame()

        self.air_density = 1.18
        self.MPS = MPS4264(ips)
        self.flow_controller_1 = flow_controller('COM5', 9600)
        self.flow_controller_2 = flow_controller('COM7', 9600)
    
    def step(self,action):
        self.t += 1

        s_,reward,done,info = self.one_step(action)  # 33.7s

        if self.t == 150:
            done = True

        self.state = s_
        return s_, float(reward), done, info

    def reset(self,):
        self.init_time = time.time()
        # print(self.init_time,'!!!!!!!!!!!!!!!!!!!!')
        self.t = 0
        initial_path = r'pressure_data'
        self.flow = 0.0
        self.flow_controller_1.set_flow_rate(2, self.flow)
        self.flow_controller_2.set_flow_rate(1, self.flow)
        time.sleep(10)
        instant_flow = np.mean([self.flow_controller_1.read_ivalue(2), self.flow_controller_2.read_ivalue(1)])
        data0, data1, _ = self.MPS.Double_UDP_transfer_data(self.MPS.device_ip, r'pressure_data', info1=0, info2= 0)
        # path_0 = os.path.join(folder_path, '0.csv')
        # path_1 = os.path.join(folder_path, '1.csv')
        # data0 = pd.read_csv(path_0, index_col=False, header=None)
        # data1 = pd.read_csv(path_1, index_col=False, header=None)

        x =  np.array(data0.iloc[:, -3:])
        x = np.mean(x, axis=0)
        wind_velocity = np.sqrt(2*abs(x[-2]-x[-1])/1.1846)
        print('Wind Velocity: ', wind_velocity)
        print("total pressure: ", x[-1])
        print("static pressure: ", x[-2])
        self.init_coefs = calculate_coef(data0, data1, x[-2], wind_velocity, self.flow, initial_path)
        self.state = np.array([wind_velocity/10.0],dtype=np.float32)
        # self.state = np.array([wind_velocity/10.0, self.init_coefs[0], self.init_coefs[1]],dtype=np.float32)
        print('step: ',self.t,' action: ',self.flow,' instant_flow: ','0.0',' state: ',self.state,' reward: ','0')
        reward = 0
        with open('results.txt','a') as f:
            f.write('step: ' + str(self.t) +' wind_velocity: '+ str(round(wind_velocity,4)) + ' action: ' + str(round(self.flow,4)) + ' instant_flow: ' + str(round(instant_flow,4)) + ' coef: ' + str(round(self.init_coefs[0], 4))+ ' ' + str(round(self.init_coefs[1], 4)) + ' reward: ' + str(reward)+ '\n')

        info = {}
        self.last_flow = 0
        return self.state

    def one_step(self,action):
        
        initial_path = r'pressure_data'
        self.flow = (action + 1)/2 * 70
        self.flow = np.clip(self.flow,0,70)
        difference = self.flow - self.last_flow
        
        # if self.last_flow <= self.flow:  # 升
        #     pre_target_flow = np.clip(self.last_flow + (difference)+5, 10, 100)
        #     self.flow_controller_1.set_flow_rate(2, pre_target_flow)
        #     self.flow_controller_2.set_flow_rate(1, pre_target_flow)
        #     instant_flow = np.mean([self.flow_controller_1.read_ivalue(2), self.flow_controller_2.read_ivalue(1)])
        #     time.sleep(0.3)
        #     while abs(self.flow - instant_flow) > 3:
        #         # time.sleep(0.1)
        #         instant_flow = np.mean([self.flow_controller_1.read_ivalue(2), self.flow_controller_2.read_ivalue(1)])
        #         print(self.flow, instant_flow)
        #     time.sleep(0.3)
        #     self.flow_controller_1.set_flow_rate(2, self.flow)
        #     self.flow_controller_2.set_flow_rate(1, self.flow)
        #     time.sleep(0.3)
        # else:  # 降
        #     pre_target_flow = np.clip(self.last_flow + (difference)-5,10,100)
        #     self.flow_controller_1.set_flow_rate(2, pre_target_flow)
        #     self.flow_controller_2.set_flow_rate(1, pre_target_flow)
        #     instant_flow = np.mean([self.flow_controller_1.read_ivalue(2), self.flow_controller_2.read_ivalue(1)])
        #     time.sleep(0.1)
        #     while abs(self.flow - instant_flow) > 3:
        #         # time.sleep(0.1)
        #         instant_flow = np.mean([self.flow_controller_1.read_ivalue(2), self.flow_controller_2.read_ivalue(1)])
        #         print(self.flow, instant_flow)
        #     time.sleep(0.3)
        #     self.flow_controller_1.set_flow_rate(2, self.flow)
        #     self.flow_controller_2.set_flow_rate(1, self.flow)
        #     time.sleep(0.3)       
        
        # self.flow_controller_1.set_flow_rate(2, self.flow)
        # self.flow_controller_2.set_flow_rate(1, self.flow)
        # time.sleep(10)
        instant_flow = np.mean([self.flow_controller_1.read_ivalue(2), self.flow_controller_2.read_ivalue(1)])
        # print(self.last_flow, pre_target_flow, self.flow, difference, extend_factor, instant_flow)
        data0, data1, _ = self.MPS.Double_UDP_transfer_data(self.MPS.device_ip, r'pressure_data', info1=0, info2= 0)

        x =  np.array(data0.iloc[:, -3:])
        x = np.mean(x, axis=0)
        wind_velocity = np.sqrt(2*abs(x[-2]-x[-1])/1.1846)
        print('Wind Velocity: ', wind_velocity)
        print("total pressure: ", x[-1])
        print("static pressure: ", x[-2])
        coefs = calculate_coef(data0, data1, x[-2], wind_velocity, self.flow, initial_path)
        coefs = np.around(coefs, decimals=3)
        s_ = np.array([wind_velocity/10.0],dtype=np.float32)

        # reward
        self.init_coefs = np.array([2.1,1.1])
        normal_a = self.flow/70
        normal_v = wind_velocity/10
        Cd_Cl = ((self.init_coefs[0] - coefs[0]) + (self.init_coefs[1] - coefs[1])) - normal_a**(5*normal_v) 
        reward = Cd_Cl

        #显示和保存数据
        print('step: ',self.t,' action: ',self.flow,' instant_flow: ',instant_flow,' state: ',s_,' reward: ','0')
        with open('results.txt','a') as f:
            f.write('step: ' + str(self.t) +' wind_velocity: '+ str(round(wind_velocity, 4)) + ' action: ' + str(round(self.flow.item(), 4)) + ' instant_flow: ' + str(round(instant_flow.item(),4)) + ' coef: ' + str(coefs[0])+ ' ' + str(coefs[1]) + ' reward: ' + str(reward[0]) + '\n')


        traj_dic = {'step':self.t,'state':self.state,'action':self.flow[0],'reward':reward,'instant_flow':instant_flow,'state_next':s_,'coef':coefs,'reward1':reward}
        traj_dic = pd.Series(traj_dic)
        self.traj = pd.concat([self.traj,traj_dic],axis = 1)
        self.traj.to_csv('traj_tes.csv')


        info = {}
        self.state = s_
        self.last_flow = self.flow
        return s_,reward,False,info

# class dynamics_model_Net(nn.Module):
#     def __init__(self, input_size, hidden_sizes, output_size, dropout_prob=0.5):
#         super(dynamics_model_Net, self).__init__()
#         self.fc_layers = nn.ModuleList()  # 用于存储隐藏层

#         # 创建隐藏层，并在每个隐藏层后添加BatchNorm和Dropout
#         for hidden_size in hidden_sizes:
#             self.fc_layers.append(nn.Linear(input_size, hidden_size))
#             # self.fc_layers.append(nn.BatchNorm1d(hidden_size))  # 添加BatchNorm层
#             self.fc_layers.append(nn.ReLU())  # 添加激活函数
#             # self.fc_layers.append(nn.Dropout(p=dropout_prob))  # 添加Dropout层
#             input_size = hidden_size

#         self.output_layer = nn.Linear(input_size, output_size)  # 输出与指定的输出维度相同

#     def forward(self, x):
#         for layer in self.fc_layers:
#             x = layer(x)
#         output = self.output_layer(x)
#         return output

# class DModel(myEnv_flow):
#     def __init__(self, nets, hidden_layers_size, is_test, render_mode = None, goal_velocity=0):
#         super().__init__(render_mode, goal_velocity)
#         self.ME = dynamics_model_Net(self.action_space.shape[0]+self.observation_space.shape[0], hidden_layers_size, self.observation_space.shape[0]).to(device)
#         self.nets = nets
#         self.t = 0
#         self.is_test = is_test

#     def step(self,action):
        
#         if self.is_test == False:
#             random_integer = np.random.randint(0, len(self.nets))
#         else:
#             random_integer = self.is_test
#         # print(random_integer)
#         self.t += 1
#         # print(self.t)
#         # force = min(max(action[0], self.min_action), self.max_action)
#         input = np.concatenate([self.state,action]).reshape(-1,(self.action_space.shape[0]+self.observation_space.shape[0]))
#         # input = (input - self.mean) / (self.std+1e-12)
#         input = (input - np.concatenate((self.observation_space.low,self.action_space.low))) / (np.concatenate((self.observation_space.high,self.action_space.high))-np.concatenate((self.observation_space.low,self.action_space.low)))
#         self.ME.load_state_dict(self.nets[random_integer])
#         self.ME.eval()
#         output = self.ME(torch.tensor(input,dtype=torch.float32).to('cuda')).cpu().detach().numpy().reshape(self.observation_space.shape[0],)
#         output = output * (self.observation_space.high - self.observation_space.low) + self.observation_space.low
#         self.state = output

#         reward = 0

#         truncated = False
#         terminated = False
#         info = {}

#         return self.state,reward,truncated, terminated,info
#     def reset(self, *, seed = None, options = None):
#         self.state = super().reset(seed=seed, options=options)
#         self.t = 0
#         return self.state
    

def calculate_coef(data0, data1,static_pressure, wind_velocity, action, initial_path):
        
        pu2 = 0.5*1.1846*wind_velocity*wind_velocity
        dfA_subset = data0.iloc[:,:12] - static_pressure
        dfB_subset = data1.iloc[:,:13] - static_pressure
        dfC_subset = data1.iloc[:,32:44] - static_pressure
        dfD_subset = data0.iloc[:,45:58] - static_pressure
        
        xlsx = pd.concat([dfA_subset, dfC_subset, dfB_subset, dfD_subset], axis=1, ignore_index=True) # ACBD
        xlsx = pd.DataFrame(xlsx)

        #AC面
        A_force = np.array([])
        C_force = np.array([])
        AC_force = np.array([])
        for i in range(0,xlsx.shape[0]):
            # area = float(xlsx.iloc[0,i])
            A_np_data = np.array(xlsx.iloc[i,0:12]).astype(np.float32)
            C_np_data = np.array(xlsx.iloc[i,12:24]).astype(np.float32)
            A_mean = np.mean(A_np_data)
            C_mean = np.mean(C_np_data)
            A_force = np.append(A_force, A_mean)
            C_force = np.append(C_force, C_mean)
            AC_force = np.append(AC_force, C_mean-A_mean)

        #BD面
        B_force = np.array([])
        D_force = np.array([])
        BD_force = np.array([])
        for i in range(0,xlsx.shape[0]):
            # area = float(xlsx.iloc[0,i])
            # B_np_data = np.array(xlsx.iloc[i,24:37]).astype(np.float32)
            # D_np_data = np.array(xlsx.iloc[i,37:50]).astype(np.float32)
            B_np_data = np.array(xlsx.iloc[i,30:37]).astype(np.float32)
            D_np_data = np.array(xlsx.iloc[i,43:50]).astype(np.float32)
            B_mean = np.mean(B_np_data)
            D_mean = np.mean(D_np_data)
            B_force = np.append(B_force, B_mean)
            D_force = np.append(D_force, D_mean)
            BD_force = np.append(BD_force, D_mean-B_mean)
            
        A_force = A_force/pu2
        B_force = B_force/pu2
        C_force = C_force/pu2
        D_force = D_force/pu2
        AC_force = AC_force/pu2
        BD_force = BD_force/pu2

        print(np.abs(np.mean((AC_force))), np.std(BD_force), np.mean(np.abs(BD_force)), np.mean(BD_force), np.sqrt(np.mean(np.square(BD_force))))
        return [np.abs(np.mean((AC_force))), np.std(BD_force), np.mean(np.abs(BD_force)), np.mean(BD_force), np.sqrt(np.mean(np.square(BD_force)))]



















