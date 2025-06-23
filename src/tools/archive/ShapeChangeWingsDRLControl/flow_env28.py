import gym
import numpy as np
import pandas as pd
import time
from gym import spaces
import coef_get as cg
import control as con
import sys


# 控制风洞
def change_WT(pwm):
    sys.path.append(r"C:\Users\HIT\Documents\Arduino\python_module")
    import WT_2_mode_byHH as Mode
    Mode.Activate_system()
    Mode.Constant_forAll(pwm)
    time.sleep(15)

# 储存数据
def save_data(data):
    # 定义表头
    header=['step','angle','action_1','action_2','action_3','action_4',
          'coef_cd', 'coef_cl', 'reward', 'reward1', 'reward2'] + [f'state_{i+1}' for i in range(28)]
    # 将数据转换为 DataFrame
    df = pd.DataFrame([data], columns=header)  # 用列表包裹数据以确保是二维数组，并设置表头
    # 定义 CSV 文件名
    csv_file = 'data.csv'
    # 追加数据到 CSV 文件，header 设为 True 如果文件不存在
    df.to_csv(csv_file, mode='a', index=False, header=not pd.io.common.file_exists(csv_file))


class myEnv_flow(gym.Env):
    def __init__(self,model):
        # 定义参数,导入模型用来查看模型一些参数比如ent coef
        self.model = model
        self.action_space = spaces.Box(low=0.0, high=20.0, shape=(4,),dtype=np.float32) # 动作空间,四个翼板伸长
        self.observation_space = spaces.Box(low=-4, high=1, shape=(28,), dtype=np.float32) # 28个点的cp
        self.t = 0
        self.ext = 0
        self.wind_angle = 0
        # 设置随机参数，此处未定义种子，全靠随机
        self.np_random = None
        self.seed()


    def reset(self,):
        print('RESET START!')
        self.init_time= time.time()
        self.t = 0
        # RESET翼板，设置当前风向角
        con.reset_fin()
        self.wind_angle = 30
        # 获取当前角度的参考cd cl cp
        self.cd,self.cl,self.coef = cg.get_refer(self.wind_angle)
        # 把cp参考值赋予初始state
        self.s = self.coef

        cd,cl,coef=cg.get_coef(self.wind_angle)
        print('angle:',self.wind_angle,' ' ,cd,' ' ,cl )
        cg.remove_data1()
        print('RESET OVER')
        time.sleep(3)

        # # 循环关闭风洞并调零测压阀直到测试值与参考值差异不大
        # while True:
        #     change_WT(0)
        #     cg.get_rezero()
        #     change_WT(1500)
        #     cd,cl,coef=cg.get_coef(self.wind_angle)
        #     print('angle:',self.wind_angle,' ' ,cd,' ' ,cl )
        #     # 把错误的垃圾数据丢弃至trash
        #     if abs(cd-self.cd)<=0.025 and abs(cl-self.cl)<=0.025:
        #         print('OK')
        #         # 把正确的数据移动至backup
        #         cg.remove_data2(self.wind_angle,1)
        #         break
        #     cg.remove_data1()
        return self.s

    def step(self,action):
        now_time = time.time()
        print(now_time-self.init_time,'STEP START!')
        self.init_time = now_time
        self.t += 1
       
        # 循环关闭风洞并调零测压阀直到测试值与参考值差异不大
        # if self.t == 1:
        #     while True:
        #         change_WT(0)
        #         cg.get_rezero()
        #         change_WT(1500)
        #         cd,cl,coef=cg.get_coef(self.wind_angle)
        #         print('angle:',self.wind_angle,' ' ,cd,' ' ,cl )
        #         # 把错误的垃圾数据丢弃至trash
        #         if abs(cd-self.cd)<=0.025 and abs(cl-self.cl)<=0.04:
        #             print('OK')
        #             # 把正确的数据移动至backup
        #             cg.remove_data2(self.wind_angle,1)
        #             break
        #         cg.remove_data1()

        # 调用onestep计算状态
        netx_state,reward,done,info = self.one_step(action)  
        self.s = netx_state

        # 此处要reset翼板
        con.reset_fin()
        time.sleep(8)

        # 清除测压文件
        cg.remove_data2(self.wind_angle)
        print('STEP OVER!')

        if self.t == 50:
            done = True
        return self.s,float(reward),done,info

    def one_step(self,action):

        # 写入动作数据并执行
        self.ext = action
        con.ctrl_fin(self.ext)
        time.sleep(10)
    
        # 调用测压阀读取并计算coef
        coef_cd,coef_cl,coef_cp = cg.get_coef(self.wind_angle)

        # 传入新状态值
        netx_state = coef_cp

        # reward是与初始系数之差，保留5位小数self.cd,self.cl,self.coef
        reward1 =  round((self.cd - coef_cd)/self.cd, 5)
        reward2 =  round((self.cl - coef_cl)/self.cl, 5)
        reward = round(reward1 + reward2 , 5)
    
        # 将所有数据组合成一行并保存
        data_all = [self.t, self.wind_angle, *self.ext, coef_cd, coef_cl, reward, reward1, reward2, *coef_cp]
        save_data(data_all)

        # 打印step提示
        print('step: ',self.t,' ','action: ',np.round(self.ext,3),' ' ,'coef: ',coef_cd,' ',coef_cl,' ','reward: ',reward,' d1:',reward1,' d2:',reward2)
        # print(entropy)

        info = {}
        done = False
        return netx_state,reward,done,info
    
    # 定义随机种子
    def seed(self, seed=None):
        self.np_random, seed = gym.utils.seeding.np_random()
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