__credits__ = ["Carlos Luis"]

from os import path
from typing import Optional

import numpy as np
import torch
import gymnasium as gym
from gym import spaces
from gym.envs.classic_control import utils
from gym.envs.classic_control.pendulum import PendulumEnv
from gym.error import DependencyNotInstalled
import math
import numpy
import pickle
DEFAULT_X = np.pi
DEFAULT_Y = 1.0

# 状态用self.state表示
class SM_Env_Wrapper(gym.Wrapper):

    def __init__(self,env:gym.Env,a,b,c,d):
        super().__init__()

    def step(self, a):

        observation, reward, terminated, truncated, info = super().step()

        with open('model.pickle','rb') as f:  
            SM = pickle.load(f)  #将模型存储在变量clf_load中  

        a = np.array([a]).reshape((self.action_space.shape[0],))

        input = np.concatenate([observation,a]).reshape(-1,(self.action_space.shape[0]+self.observation_space.shape[0]))

        self.s = SM.predict(input).reshape(self.observation_space.shape[0],)

        #reward
        reward = self.param_a + self.param_b + self.param_c + self.param_d

        # # 强制步数阻断，推荐在注册页面设置

        return self.state, reward, terminated, truncated, {}

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):
        super().reset(seed=seed)
        