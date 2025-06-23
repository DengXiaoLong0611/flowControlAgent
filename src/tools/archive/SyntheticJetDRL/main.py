import gym
import numpy as np
import torch
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.noise import NormalActionNoise, OrnsteinUhlenbeckActionNoise

from Env.flowEnvTransient1ActionVoltage_Predictive import myEnv_flow
from stable_baselines3.common.vec_env\
import DummyVecEnv, VecNormalize
import time


run = 'eval'
# 注意train_load时更改文件目录

if run == 'train':
  # Save a checkpoint every 1000 steps
  checkpoint_callback = CheckpointCallback(
    save_freq=100,
    save_path="logs_norm/",
    name_prefix="rl_model_norm",
    save_replay_buffer=True,
    save_vecnormalize=True,
  )

  env = DummyVecEnv([lambda: myEnv_flow()])
  # env = VecNormalize(env, norm_obs=False, norm_reward=True,clip_obs=10.)
    # env = VecNormalize.load(r'rl_model_norm_vecnormalize_880_steps.pkl',env)
    # env.norm_obs = False
    # env.norm_reward = True
    # env.training = True
  n_actions = env.action_space.shape[-1]

  policy_kwargs = dict(activation_fn=torch.nn.ReLU,
                      net_arch=dict(pi=[256,256], qf=[256,256]))
  action_noise = NormalActionNoise(mean=np.zeros(n_actions), sigma=0.1 * np.ones(n_actions))
  model = SAC("MlpPolicy", 
              env, 
              verbose=1,
              policy_kwargs = policy_kwargs,
              batch_size=512,
              learning_rate=0.001,
              buffer_size=100000,
              learning_starts=16,
              train_freq = (1,'step'),
              seed = 0,
              ent_coef='auto_0.5',
              target_entropy=-1.0,
              gradient_steps= 10
              )

  print(model.actor)
  print(model.critic) 
  model.learn(total_timesteps=10000, log_interval=1,callback=checkpoint_callback)

  model.save("sac_pendulum")


if run == 'train_load':
  print(time.time(),'!!!!!!!!!!!!!!!!!!!!')
  # Save a checkpoint every 1000 steps
  checkpoint_callback = CheckpointCallback(
    save_freq=200,
    save_path="logs_norm/",
    name_prefix="rl_model_norm",
    save_replay_buffer=True,
    save_vecnormalize=True,
  )

  env = DummyVecEnv([lambda: myEnv_flow()])
  # env = VecNormalize.load(r'rl_model_norm_vecnormalize_880_steps.pkl',env)
  # env.norm_obs = False
  # env.norm_reward = True
  # env.training = True

  n_actions = env.action_space.shape[-1]   #如果你现在的动作有两个参数（例如，频率和电压），那么env.action_space.shape[-datalog]应该返回2，这意味着n_actions将是2，所以你不需要改变这里的设置。然而，你需要确保你的环境类（在你的代码中是myEnv_flow）正确地定义了动作空间，以反映出动作有两个参数。
  policy_kwargs = dict(activation_fn=torch.nn.ReLU,
                      net_arch=dict(pi=[256,256], qf=[256,256]))
  action_noise = NormalActionNoise(mean=np.zeros(n_actions), sigma=0.1 * np.ones(n_actions))

  model = SAC.load(
      r'logs_norm/rl_model_norm_12400_steps.zip',
      env = env,
      learning_rate = 0.001,
      action_noise = None,
      batch_size = 512,
      learning_starts = 0,
      ent_coef = 'auto_0.2',
      target_entropy = -1.0,
      gradient_steps=10,
      train_freq = (1,'step'),
      )

  # model.set_parameters(r'logs_norm_5\rl_model_norm_200_steps.zip')
  model.load_replay_buffer(r'D:\Research\PHDProject\Code\Code_running\大风洞的合成射流DRL训练\Year2025\2-dutyratio20250402\2025-2-dutyratio-test-coding\logs_norm\rl_model_norm_replay_buffer_12400_steps.pkl')


  print(model.actor)
  print(model.critic) 
  print(model.batch_size)
  print(model.replay_buffer.size())
  print(model.learning_rate)
  print(model._n_updates)

  model.learn(total_timesteps=50000, log_interval=1,callback=checkpoint_callback,reset_num_timesteps= False)

  model.save("sac_pendulum")

if run =='eval':
  
  env = DummyVecEnv([lambda: myEnv_flow()])
  # env = VecNormalize(env, norm_obs=True, norm_reward=False,clip_obs=10.)
  # env = VecNormalize.load(r'trainedFirmSave/logs_norm-20230806-suck20sAction10msWind/logs_norm/rl_model_norm_replay_buffer_660_steps.pkl',env)
  model = SAC.load(r"D:\Research\PHDProject\Code\Code_running\大风洞的合成射流DRL训练\Year2025\2-dutyratio20250525\run\logs_norm\rl_model_norm_14000_steps.zip",env = env)
  t1 = time.time()
  obs = env.reset()
  while True:
      t2 = time.time()
      print(t2-t1,'tttttttttt')
      action, _states = model.predict(obs, deterministic=True)
      obs, reward, done, info = env.step(action)

      if done:
        t3 = time.time()
        print(t3-t1,'tttttttttt')
        obs = env.reset()