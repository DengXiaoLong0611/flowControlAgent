import gym
import numpy as np
import pandas as pd
import time
from gym import spaces
import coef_get as cg
import control as con
import sys
import torch
import random

# 储存数据
def save_data(data):
    # 定义表头
    header=['step','angle','cd','cl','action_1','action_2','action_3','action_4',
          'coef_cd', 'coef_cl', 'reward', 'reward1', 'reward2'] + [f'cp_{i+1}' for i in range(28)]
    # 将数据转换为 DataFrame
    df = pd.DataFrame([data], columns=header)  # 用列表包裹数据以确保是二维数组，并设置表头
    # 定义 CSV 文件名
    csv_file = 'eval.csv'
    # 追加数据到 CSV 文件，header 设为 True 如果文件不存在
    df.to_csv(csv_file, mode='a', index=False, header=not pd.io.common.file_exists(csv_file))

def get_avg_coef(wind_angle):
    coef_list = []
    for _ in range(7):
        cd, cl, coef = cg.get_coef(wind_angle)  # coef 是一个 28维数组
        print(cd,'  ',cl)
        coef_list.append((cd, cl, np.array(coef)))  # 确保 coef 是 numpy array
        cg.remove_data1()
        time.sleep(0.5)
    # 去掉 cd + cl 最大和最小项
    coef_list.sort(key=lambda x: x[0] + x[1])
    filtered = coef_list[1:-1]
    # 分别取出 cd, cl 和 coef 列表
    cds = [x[0] for x in filtered]
    cls = [x[1] for x in filtered]
    coefs = [x[2] for x in filtered]  # 这是多个 28维数组
    avg_cd = round(sum(cds) / len(cds), 3)
    avg_cl = round(sum(cls) / len(cls), 3)
    avg_coef = np.round(np.mean(coefs, axis=0), 3)  # 对28维向量按维度求平均
    return avg_cd, avg_cl, avg_coef


class myEnv_flow(gym.Env):
    def __init__(self,):
        # 定义参数,导入模型用来查看模型一些参数比如ent coef
        self.action_space = spaces.Box(low=0.0, high=20.0, shape=(4,),dtype=np.float32) # 动作空间,四个翼板伸长
        self.observation_space = spaces.Box(low=np.array([0, 0, 0]), high=np.array([4.5, 4, 4]), shape=(3,), dtype=np.float32) # 28个点的cp
        self.t = 0
        self.ext = 0
        self.config_1 = 3
        self.wind_angles = [0,2.5,5,7.5,10,12.5,15,20,25,30,35,40,45]
        # self.wind_angles = [0,5,10,15,30,45]
        # self.wind_angles = [3,13,18,22,37]
        self.wind_angle_index = 0
        # 设置随机参数，此处未定义种子，全靠随机
        self.np_random = None
        self.seed()


    def reset(self,):
        print('RESET START!')
        self.init_time= time.time()
        self.t = 0
        print('RESETing')
        # 单独训练
        # self.wind_angle = 15
        # con.ctrl_fin([0,0,0,0])
        # time.sleep(8)
        # self.r_cd, self.r_cl, self.r_coef = cg.get_refer(self.wind_angle)
        # coef_1,coef_2,coef_3 = cg.get_coef(self.wind_angle)
        # print(coef_1,'  ',coef_2)
        # 综合训练
        self.wind_angle = self.wind_angles[self.wind_angle_index]
        # 更新索引，使得下次 reset 时使用下一个风向角
        self.wind_angle_index = (self.wind_angle_index + 1) % len(self.wind_angles)
        con.ctrl_fin([0,0,0,0])
        time.sleep(8)
        con.ctrl_angle([self.wind_angle,0,0,0])
        time.sleep(10)
        self.r_cd, self.r_cl, self.r_coef = get_avg_coef(self.wind_angle)
        # 把cp参考值赋予初始state
        self.s = [self.wind_angle/10, self.r_cd,self.r_cl]
        print('angle:',self.wind_angle,' ' ,self.r_cd,' ' ,self.r_cl )    
        cg.remove_data1()
        print('RESET OVER')
        return self.s

    def step(self,action):
        now_time = time.time()
        print(now_time-self.init_time,'STEP START!')
        self.init_time = now_time
        self.t += 1
        netx_state,reward,done,info = self.one_step(action)  
        self.s = netx_state

        # 清除测压文件
        cg.remove_data2(self.wind_angle)
        print('STEP OVER!')

        if self.t == self.config_1:
            done = True
        return self.s,float(reward),done,info

    def one_step(self,action):
        # 写入动作数据并执行
        self.ext = action
        con.ctrl_fin(self.ext)
        print('FIN MOVING!')
        time.sleep(8)
    
        # 调用测压阀读取并计算coef
        coef_cd,coef_cl,coef_cp = cg.get_coef(self.wind_angle)

        # 传入新状态值
        netx_state = [self.wind_angle/10,coef_cd,coef_cl]

        # reward是与初始系数之差，保留5位小数self.cd,self.cl,self.coef
        reward1 =  round((self.r_cd - coef_cd)/self.r_cd, 5)
        reward2 =  round((self.r_cl - coef_cl)/self.r_cl, 5)
        reward = round(reward1 + reward2, 5) 
    
        # 将所有数据组合成一行并保存
        data_all = [self.t, *self.s, *self.ext, coef_cd, coef_cl, reward, reward1, reward2, *coef_cp]
        save_data(data_all)

        # 打印step提示
        print('step: ',self.t,' ','action: ',np.round(self.ext,3),' ' ,'coef: ',coef_cd,' ',coef_cl,' ','reward: ',reward,' d1:',reward1,' d2:',reward2)

        info = {}
        done = False
        return netx_state,reward,done,info
    
    # 定义随机种子
    def seed(self, seed=None):
        self.np_random, seed = gym.utils.seeding.np_random(seed)
        # 确保 seed 在合法范围内
        seed = int(seed) % (2**32)
        np.random.seed(seed)
        random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # 如果使用 GPU
        return [seed]
    



# class MLP(FitModule):
#     def __init__(self, n_feats, n_classes, hidden_size=256):
#         super(MLP, self).__init__()
#         self.fc1 = nn.Linear(n_feats, hidden_size)
#         self.fc2 = nn.Linear(hidden_size, hidden_size)
#         self.fc3 = nn.Linear(hidden_size, n_classes)
#
#     def forward(self, x):
#         x = self.fc1(x)
#         x = F.relu(x)
#         x = self.fc2(x)
#         x = F.relu(x)
#         x = self.fc3(x)
#         return x