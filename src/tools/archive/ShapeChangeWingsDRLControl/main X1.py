import gym
import numpy as np
from stable_baselines3 import SAC
import torch
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback
from stable_baselines3.common.noise import NormalActionNoise, OrnsteinUhlenbeckActionNoise
from flow_env import myEnv_flow
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
import time






run = 'continue_train'
# 注意继续训练时更改文件目录，更改numstep，找到目录下最新的step，改成对应的值
num_steps =1920
load_model_path = 'logs_norm/rl_model_norm_{}_steps.zip'.format(num_steps)
load_buffer_path = 'logs_norm/rl_model_norm_replay_buffer_{}_steps.pkl'.format(num_steps)
# load_normalize_env_path = 'logs_norm/rl_model_norm_vecnormalize_{}_steps.pkl'.format(num_steps)








if run == 'train':
  # 设置20步一个训练保存点
  checkpoint_callback = CheckpointCallback(
    save_freq=20,
    save_path="./logs_norm/",
    name_prefix="rl_model_norm",
    save_replay_buffer=True,
    save_vecnormalize=True,
  )
  callback=[checkpoint_callback]
  env = DummyVecEnv([lambda: myEnv_flow()])
  # 指定策略网络的结构和激活函数。在这里，"pi"表示策略网络（actor），"qf"表示Q值网络（critic），分别使用两层每层256个单元的全连接层，并使用ReLU激活函数。
  policy_kwargs = dict(activation_fn=torch.nn.ReLU,net_arch=dict(pi=[256,256,256], qf=[256,256,256]))
  # 模型参数，可适当修改经验池，学习率等
  model = SAC("MlpPolicy", 
              env=env, 
              verbose=1,
              policy_kwargs = policy_kwargs,
              batch_size=256,
              learning_rate=0.001,
              buffer_size=100000,
              learning_starts=64,
              train_freq = (1,'step'),
              seed = 0,
              ent_coef=0.5,
              target_entropy=-4.0,
              gradient_steps= 10,
              tau=0.01
              )

  print(model.actor)
  print(model.critic) 
  model.learn(total_timesteps=10000, log_interval=1,callback=callback)

  model.save("SAC_fin")


if run == 'continue_train':
  print(time.time(),'CONTINUE!!!!!!!!!!!!!!!!!!!!')
  checkpoint_callback = CheckpointCallback(
    save_freq=10,
    save_path="./logs_norm/",
    name_prefix="rl_model_norm",
    save_replay_buffer=True,
    save_vecnormalize=True,
  )

  # 修改熵系数，在继续训练开始时修改为较大的熵系数，增大探索性，200步后开始训练
  class DynamicEntCoefCallback(BaseCallback):
    def __init__(self, verbose=1):
        super(DynamicEntCoefCallback, self).__init__(verbose)

    def _on_step(self) -> bool:
        if self.num_timesteps == 101:  # 只在新工况开始时手动增大熵，然后会自动调整
          new_ent_coef = 0.5 # 调大确保探索性
          #  修改 log_ent_coef
          with torch.no_grad():
              self.model.log_ent_coef.copy_(torch.log(torch.tensor(new_ent_coef)))
          # 打印修改后的值
          print(f"Step: {self.num_timesteps}, 新的熵系数: {new_ent_coef}")
        return True
    
  entropy_callback = DynamicEntCoefCallback()
  callback=[checkpoint_callback,entropy_callback]
  
  policy_kwargs = dict(activation_fn=torch.nn.ReLU,net_arch=dict(pi=[256,256,256], qf=[256,256,256]))
  # 从目录中加载训练过的模型，可适当修改经验池，学习率等
  model = SAC.load(load_model_path,
                   env=None,
                   learning_rate=0.001,
                   action_noise=None,
                   batch_size=1600,
                   learning_starts = 0,
                   ent_coef='auto',
                   target_entropy=-4,
                   gradient_steps=10,
                   train_freq=(1, 'step'),
                   tau=0.01
                   )
  
  env = DummyVecEnv([lambda: myEnv_flow(model=model)])
  model.set_env(env)
  # 读取经验缓冲池，帮助策略训练
  model.load_replay_buffer(load_buffer_path)

  print(model.actor)
  print(model.critic) 
  print(model.batch_size)
  print(model.replay_buffer.size())
  print(model.learning_rate)
  print(model._n_updates)

  model.learn(total_timesteps=10000, log_interval=1, callback=callback, reset_num_timesteps= False)
  model.save("SAC_fin")

if run =='eval':
  
  for model_number in range(900, 1581, 100):
      model_path=f"logs_norm/rl_model_norm_{model_number}_steps.zip"
      model = SAC.load(model_path,env = None)
      env = DummyVecEnv([lambda: myEnv_flow(model=model)])
      model.set_env(env)
      t1 = time.time()
      obs = env.reset()
      i=0
      # 循环控制评估10步
      while True:
          i=i+1
          t2 = time.time()
          print(t2-t1,'tttttttttt')
          action, _states = model.predict(obs, deterministic=True)
          obs, reward, done, info = env.step(action)
          t3 = time.time()
          print(t3-t1,'tttttttttt')
          if i==5:
            break
  