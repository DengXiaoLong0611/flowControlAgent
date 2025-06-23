import gym
import numpy as np
from gym import spaces
import torch
from other.data_saving import data_save
from example.MPS4264 import MPS4264
from example.flow_controller import flow_controller



class wind_tunnel_env(gym.Env):
    def __init__(self):
        self.training_num = 1
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,),dtype=np.float32) # 动作空间
        self.observation_space = spaces.Box(low=np.array([0.0, 0.0, 0.0]), high=np.array([20.0, 2.0, 2.0]), shape=(3,),dtype=np.float32) # 状态空间
        self.t = 0 

    def step(self,action):
        self.t += 1

        done = False

        # take action
        # ...

        # get new state
        # ...

        s_ = np.array([1,1,1],dtype=np.float32)

        reward = 0

        # save data
        header = ['step', 'state', 'action', 'next_state', 'reward']
        values = [1, 2, 3, 4, 5]
        data_save(header, values, 'trajectory.csv')

        info = {}

        if self.t == 300:
            done = True

        self.state = s_
        return s_,float(reward),done,info

    def reset(self,):
        self.t = 0
        self.state = np.array([1, 1, 1],dtype=np.float32)

        return self.state

