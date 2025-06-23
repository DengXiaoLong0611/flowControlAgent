import gym
import numpy as np
from stable_baselines3 import SAC
import torch
from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback
from stable_baselines3.common.noise import NormalActionNoise, OrnsteinUhlenbeckActionNoise
from flow_env import myEnv_flow
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
import time
import pickle
import random
import sys
import os
from stable_baselines3.sac.LRB import LabeledReplayBuffer
import os
from stable_baselines3.common.callbacks import BaseCallback

class LabeledReplayBufferCallback(BaseCallback):
    def __init__(self, labeled_replay_buffer, wind_angle, save_interval=1, save_dir="./logs_norm", disable_sb3_buffer=True):
        """
        `LabeledReplayBuffer` 的回调：
        - 每个 step 结束后，将数据存入 `LabeledReplayBuffer`
        - 禁用 SB3 的 `ReplayBuffer` 存储
        - 确保 `model.replay_buffer` 被替换
        - 定期保存经验池
        """
        super().__init__()
        self.labeled_replay_buffer = labeled_replay_buffer
        self.wind_angle = wind_angle
        self.save_interval = save_interval
        self.save_dir = save_dir
        self.disable_sb3_buffer = disable_sb3_buffer  # 是否禁用 SB3 的 buffer 存储
        os.makedirs(self.save_dir, exist_ok=True)

    def _on_step(self) -> bool:
        """每个 step 结束后，将数据存入 `LabeledReplayBuffer`，但禁用 SB3 默认的 `ReplayBuffer`"""

        # ✅ 确保 SB3 的默认缓冲池不会存数据
        if self.disable_sb3_buffer and not isinstance(self.model.replay_buffer, LabeledReplayBuffer):
            self.model.replay_buffer.add = lambda *args, **kwargs: None  # 只禁用 SB3 的 buffer
            print("sb3缓冲池已禁用")

        # ✅ 获取当前观察状态（obs）
        current_obs = self.model._last_obs  

        # ✅ 获取 `next_obs`
        if "terminal_observation" in self.locals:
            next_obs = self.locals["terminal_observation"] if self.locals["dones"] else self.locals["new_obs"]
        else:
            next_obs = self.locals["new_obs"]

        sample = (
            current_obs,                # ✅ 当前观察状态 obs
            self.locals["actions"],      # 动作 action
            self.locals["rewards"],      # 奖励 reward
            next_obs,                    # ✅ 下一状态 next_obs
            self.locals["dones"],        # 是否结束 done
        )

        # ✅ 只向 `LabeledReplayBuffer` 存数据
        self.labeled_replay_buffer.add(sample, self.wind_angle)

        # ✅ 确保 `model.replay_buffer` 被替换为 `LabeledReplayBuffer`
        if not isinstance(self.model.replay_buffer, LabeledReplayBuffer):
            self.model.replay_buffer = self.labeled_replay_buffer
            self.model.wind_angle = self.wind_angle  

        # ✅ 每 `save_interval` 步自动保存缓冲池
        if self.num_timesteps % self.save_interval == 0:
            save_path = os.path.join(self.save_dir, f"labeled_replay_buffer_{self.num_timesteps}.pkl")
            self.labeled_replay_buffer.save(save_path)
            print("已保存标签缓冲池")

        return True  # 继续训练


checkpoint_callback = CheckpointCallback(
    save_freq=1,
    save_path="./logs_norm/",
    name_prefix="rl_model_norm",
    save_replay_buffer=True,
    save_vecnormalize=True,
  )


run = 'train'


# **训练模式**
if run == 'train':
    wind_angle = 0
    step_count = 0  
    replay_buffer = LabeledReplayBuffer(max_size=100000)
    env = DummyVecEnv([lambda: myEnv_flow()])

    # 定义训练参数
    policy_kwargs = dict(activation_fn=torch.nn.ReLU, net_arch=dict(pi=[256, 256, 128], qf=[256, 256, 128]))
    train_freq = 3  
    learning_starts = 3  
    batch_size = 3  
    learning_rate = 5e-4  
    model = SAC("MlpPolicy",
                env=env,
                verbose=1,
                policy_kwargs=policy_kwargs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                buffer_size=100000,
                learning_starts=learning_starts,
                train_freq=train_freq,  
                seed=0,
                ent_coef='auto_0.5',
                target_entropy=-4.0,
                gradient_steps=10,
               )
    print(model.actor)
    print(model.critic)
    # # 手动初始化 _logger 和其他必要属性
    Replaycallback = LabeledReplayBufferCallback(labeled_replay_buffer=replay_buffer, wind_angle=wind_angle)
    callback=[checkpoint_callback,Replaycallback]

    model.learn(total_timesteps=10000, log_interval=1, callback=callback)

# **继续训练模式**
if run == 'continue_train':
    step_count = 5
    load_model_path = f'logs_norm/rl_model_{step_count}.zip'
    load_buffer_path = f'logs_norm/labeled_replay_buffer_{step_count}.pkl'

    wind_angle = 0
    env = DummyVecEnv([lambda: myEnv_flow()])

    # 定义训练参数
    policy_kwargs = dict(activation_fn=torch.nn.ReLU, net_arch=dict(pi=[256, 256, 128], qf=[256, 256, 128]))
    train_freq = 3  
    learning_starts = 3  
    batch_size = 3  
    learning_rate = 5e-4  
    model = SAC("MlpPolicy",
                env=env,
                verbose=1,
                policy_kwargs=policy_kwargs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                buffer_size=100000,
                learning_starts=learning_starts,
                train_freq=train_freq,  
                seed=0,
                ent_coef='auto_0.5',
                target_entropy=-4.0,
                gradient_steps=10,
               )
    
    replay_buffer = LabeledReplayBuffer(max_size=100000)
    replay_buffer.load(load_buffer_path)
    Replaycallback = LabeledReplayBufferCallback(labeled_replay_buffer=replay_buffer, wind_angle=wind_angle)
    callback=[checkpoint_callback,Replaycallback]

    print(model.actor)
    print(model.critic) 
    print(model.batch_size)
    print(model.replay_buffer.size())
    print(model.learning_rate)
    print(model._n_updates)
    model.learn(total_timesteps=10000, log_interval=1, callback=callback, reset_num_timesteps= False)


# def add_samples_and_compare(buffer_path, wind_angle, sample, num_additions):
#     """ 加载经验池，添加指定次数的新数据，并对比更新前后的数据总量 """
#     # 加载经验池
#     replay_buffer = LabeledReplayBuffer(max_size=100000)
#     replay_buffer.load(buffer_path)
    
#     # 记录更新前的样本数量
#     initial_count = len(replay_buffer.data.get(wind_angle, []))
    
#     # 追加 num_additions 次新数据
#     for _ in range(num_additions):
#         replay_buffer.add(sample, wind_angle)

#     # 记录更新后的样本数量
#     updated_count = len(replay_buffer.data.get(wind_angle, []))

#     # 生成更新后的经验池文件名
#     updated_buffer_path = buffer_path.replace(".pkl", "_updated.pkl")
#     # 保存更新后的经验池
#     replay_buffer.save(updated_buffer_path)

#     # 打印对比信息
#     print(f"风向角 {wind_angle} 更新前样本数: {initial_count}")
#     print(f"风向角 {wind_angle} 更新后样本数: {updated_count}")
#     print(f"成功向风向角 {wind_angle} 添加 {num_additions} 条数据，并保存到 {updated_buffer_path}")

# # 设置文件路径
# buffer_path = "logs_norm/replay_buffer_5steps.pkl"

# # 目标风向角
# wind_angle = 5

# # 创建符合格式的数据
# obs = np.array([[0.1, 2.0, 1.2]], dtype=np.float32)  # (1, 3) 形状
# action = np.array([[3.0, 5.5, 0.2, 11.0]], dtype=np.float32)  # (1, 4) 形状
# reward = np.array([-0.08], dtype=np.float32)  # (1,) 形状
# next_obs = np.array([[0.1, 2.1, 1.25]], dtype=np.float32)  # (1, 3) 形状
# done = np.array([False])  # (1,) 形状
# sample = (obs, action, reward, next_obs, done)

# # 执行添加并对比
# num_additions = 5  # 例如，添加n次
# add_samples_and_compare(buffer_path, wind_angle, sample, num_additions)
    
# # 1. 加载经验池
# buffer_path = "logs_norm/replay_buffer_240steps.pkl"  # 经验池文件路径
# replay_buffer = LabeledReplayBuffer(max_size=100000)
# replay_buffer.load(buffer_path)

# # 2. 打印经验池信息
# print("经验池内容概览：")
# print(f"存储的风向角: {list(replay_buffer.data.keys())}")  # 打印已有的风向角标签
# for angle in replay_buffer.data:
#     print(f"风向角 {angle}: 共有 {len(replay_buffer.data[angle])} 条数据")
#     if len(replay_buffer.data[angle]) > 0:
#         print("示例数据:", replay_buffer.data[angle][:2])  # 仅打印前2个样本，避免输出过多
