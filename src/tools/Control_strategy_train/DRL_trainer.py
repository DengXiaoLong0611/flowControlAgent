import os
import time
import torch
import numpy as np
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.noise import NormalActionNoise
from stable_baselines3.common.vec_env import DummyVecEnv

"""
DRLTrainer
=========

深度强化学习（DRL）流动控制策略训练工具类。

- 支持SAC等基于stable-baselines3的DRL算法训练、断点续训、评估。
- 训练环境需实现Gym接口（如myEnv_flow），通过env_fn参数传入。
- 适用于流动控制、实验物理等多种场景。

依赖：
    - stable-baselines3
    - torch
    - numpy
    - gym
    - 你的自定义环境文件（如flowEnvTransient1ActionVoltage_Predictive.py）

典型用法：
    from tools.Control_strategy_training.DRL_trainer import DRLTrainer
    from Env.flowEnvTransient1ActionVoltage_Predictive import myEnv_flow
    trainer = DRLTrainer(env_fn=myEnv_flow)
    trainer.train(total_timesteps=10000)
    # trainer.load_and_continue_train('logs_norm/rl_model_norm_12400_steps.zip', total_timesteps=50000, replay_buffer_path='logs_norm/rl_model_norm_replay_buffer_12400_steps.pkl')
    # trainer.evaluate('logs_norm/rl_model_norm_12400_steps.zip')
"""

class DRLTrainer:
    """
    DRL深度强化学习流动控制策略训练工具类
    支持训练、断点续训、评估等功能
    """
    def __init__(self, env_fn, log_dir="logs_norm", policy_kwargs=None, batch_size=512, learning_rate=0.001, buffer_size=100000):
        self.env = DummyVecEnv([env_fn])
        self.log_dir = log_dir
        self.policy_kwargs = policy_kwargs or dict(activation_fn=torch.nn.ReLU, net_arch=dict(pi=[256,256], qf=[256,256]))
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.buffer_size = buffer_size
        self.model = None

    def train(self, total_timesteps=10000, checkpoint_freq=100, save_name="rl_model_norm"):
        checkpoint_callback = CheckpointCallback(
            save_freq=checkpoint_freq,
            save_path=self.log_dir,
            name_prefix=save_name,
            save_replay_buffer=True,
            save_vecnormalize=True,
        )
        n_actions = self.env.action_space.shape[-1]
        action_noise = NormalActionNoise(mean=np.zeros(n_actions), sigma=0.1 * np.ones(n_actions))
        self.model = SAC(
            "MlpPolicy",
            self.env,
            verbose=1,
            policy_kwargs=self.policy_kwargs,
            batch_size=self.batch_size,
            learning_rate=self.learning_rate,
            buffer_size=self.buffer_size,
            learning_starts=16,
            train_freq=(1, 'step'),
            seed=0,
            ent_coef='auto_0.5',
            target_entropy=-1.0,
            gradient_steps=10,
            action_noise=action_noise
        )
        print(self.model.actor)
        print(self.model.critic)
        self.model.learn(total_timesteps=total_timesteps, log_interval=1, callback=checkpoint_callback)
        self.model.save(os.path.join(self.log_dir, "drl_trained_model"))

    def load_and_continue_train(self, model_path, total_timesteps=50000, checkpoint_freq=200, save_name="rl_model_norm", replay_buffer_path=None):
        checkpoint_callback = CheckpointCallback(
            save_freq=checkpoint_freq,
            save_path=self.log_dir,
            name_prefix=save_name,
            save_replay_buffer=True,
            save_vecnormalize=True,
        )
        n_actions = self.env.action_space.shape[-1]
        self.model = SAC.load(
            model_path,
            env=self.env,
            learning_rate=self.learning_rate,
            batch_size=self.batch_size,
            learning_starts=0,
            ent_coef='auto_0.2',
            target_entropy=-1.0,
            gradient_steps=10,
            train_freq=(1, 'step'),
        )
        if replay_buffer_path:
            self.model.load_replay_buffer(replay_buffer_path)
        print(self.model.actor)
        print(self.model.critic)
        print(self.model.batch_size)
        print(self.model.replay_buffer.size())
        print(self.model.learning_rate)
        print(self.model._n_updates)
        self.model.learn(total_timesteps=total_timesteps, log_interval=1, callback=checkpoint_callback, reset_num_timesteps=False)
        self.model.save(os.path.join(self.log_dir, "drl_trained_model"))

    def evaluate(self, model_path, n_eval_episodes=10):
        self.model = SAC.load(model_path, env=self.env)
        rewards = []
        for ep in range(n_eval_episodes):
            obs = self.env.reset()
            done = False
            ep_reward = 0
            while not done:
                action, _states = self.model.predict(obs, deterministic=True)
                obs, reward, done, info = self.env.step(action)
                ep_reward += reward[0] if isinstance(reward, np.ndarray) else reward
            rewards.append(ep_reward)
            print(f"Episode {ep+1}: Reward = {ep_reward}")
        print(f"Average Reward over {n_eval_episodes} episodes: {np.mean(rewards)}")

# Example usage
if __name__ == '__main__':
    from Env.flowEnvTransient1ActionVoltage_Predictive import myEnv_flow
    trainer = DRLTrainer(env_fn=myEnv_flow)
    trainer.train(total_timesteps=10000)
    # trainer.load_and_continue_train('logs_norm/rl_model_norm_12400_steps.zip', total_timesteps=50000, replay_buffer_path='logs_norm/rl_model_norm_replay_buffer_12400_steps.pkl')
    # trainer.evaluate('logs_norm/rl_model_norm_12400_steps.zip') 