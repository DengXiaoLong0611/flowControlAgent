import gym
import numpy as np
from gym import spaces
from tools.flow_control.shape_change_wing_controller import ShapeChangeWingController

class ShapeChangeWingEnv(gym.Env):
    """
    可形变翼板控制的DRL环境
    状态空间、动作空间、奖励函数可根据实验需求自定义
    """
    def __init__(self, port='COM17', baudrate=115200):
        super().__init__()
        self.controller = ShapeChangeWingController(port, baudrate)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
        self.observation_space = spaces.Box(low=np.array([0.0, 0.0, 0.0, 0.0]), high=np.array([1.0, 1.0, 1.0, 1.0]), shape=(4,), dtype=np.float32)
        self.state = np.array([0, 0, 0, 0], dtype=np.float32)
        self.t = 0

    def step(self, action):
        self.t += 1
        # 这里假设action为4个翼板目标位置
        self.controller.set_fin_position(action)
        # 采集新状态（可根据实际采集方式修改）
        s_ = np.array([0, 0, 0, 0], dtype=np.float32)  # TODO: 采集真实状态
        reward = 0  # TODO: 设计奖励函数
        done = self.t >= 100
        info = {}
        self.state = s_
        return s_, float(reward), done, info

    def reset(self):
        self.t = 0
        self.state = np.array([0, 0, 0, 0], dtype=np.float32)
        self.controller.reset_position()
        return self.state

    def close(self):
        pass 