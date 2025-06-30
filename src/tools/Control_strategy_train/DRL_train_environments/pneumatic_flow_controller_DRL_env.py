import gym
import numpy as np
from gym import spaces
from tools.flow_control.pneumatic_flow_controller import PneumaticFlowController

class WindTunnelEnv(gym.Env):
    """
    气管式吹吸气流量控制的DRL环境
    状态空间、动作空间、奖励函数可根据实验需求自定义
    """
    def __init__(self, port='COM3', baudrate=9600):
        super().__init__()
        self.controller = PneumaticFlowController(port, baudrate)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
        self.observation_space = spaces.Box(low=np.array([0.0, 0.0, 0.0]), high=np.array([20.0, 2.0, 2.0]), shape=(3,), dtype=np.float32)
        self.state = np.array([1, 1, 1], dtype=np.float32)
        self.t = 0

    def step(self, action):
        self.t += 1
        # 这里假设action[0]为目标流量
        self.controller.set_flow_rate(device_id=1, value=float(action[0]))
        # 采集新状态（可根据实际采集方式修改）
        s_ = np.array([1, 1, 1], dtype=np.float32)  # TODO: 采集真实状态
        reward = 0  # TODO: 设计奖励函数
        done = self.t >= 300
        info = {}
        self.state = s_
        return s_, float(reward), done, info

    def reset(self):
        self.t = 0
        self.state = np.array([1, 1, 1], dtype=np.float32)
        return self.state

    def close(self):
        self.controller.close() 