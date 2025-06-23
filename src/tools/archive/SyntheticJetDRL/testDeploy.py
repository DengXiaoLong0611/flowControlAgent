import gym
import numpy as np

from stable_baselines3 import SAC
import torch

from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.noise import NormalActionNoise, OrnsteinUhlenbeckActionNoise
from Env.flowEnvTransient1ActionVoltage_Predictive import myEnv_flow
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize


num = 100

env = DummyVecEnv([lambda: myEnv_flow()])
# env = VecNormalize(env, norm_obs=True, norm_reward=False,clip_obs=10.)
# env = VecNormalize.load(r'logs_norm\rl_model_norm_vecnormalize_{}_steps.pkl'.format(num),env)
model = SAC.load(r"D:\Research\PHDProject\Code\Code_running\大风洞的合成射流DRL训练\Year2025\2-dutyratio20250525\run\logs_norm\rl_model_norm_14000_steps.zip".format(num),env = env)

obs = env.reset()
while True:
    action, _states = model.predict(obs, deterministic=True)
    obs, reward, done, info = env.step(action)

    if done:
        obs = env.reset()

