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
import pickle

# run ='train'
# run ='continue_train'
# run ='update'
run='eval'
# run='merge'
# run='newinject'
# 注意继续训练时更改文件目录，更改numstep，找到目录下最新的step，改成对应的值
num_steps = 600
load_model_path = 'logs_norm/rl_model_norm_{}_steps.zip'.format(num_steps)
load_buffer_path = 'logs_norm/rl_model_norm_replay_buffer_{}_steps.pkl'.format(num_steps)
# load_normalize_env_path = 'logs_norm/rl_model_norm_vecnormalize_{}_steps.pkl'.format(num_steps)




if run == 'train':
    # 设置10步一个训练保存点
    checkpoint_callback = CheckpointCallback(
        save_freq=20,
        save_path="./logs_norm/",
        name_prefix="rl_model_norm",
        save_replay_buffer=True,
        save_vecnormalize=True,  # 保存VecNormalize设置
    )
    callback = [checkpoint_callback]

    # 创建环境
    env = DummyVecEnv([lambda: myEnv_flow()])
    # 指定策略网络的结构和激活函数
    policy_kwargs = dict(activation_fn=torch.nn.ReLU,net_arch=dict(pi=[256, 256, 256], qf=[256, 256, 256]))

    # 模型参数
    model = SAC("MlpPolicy", 
                env=env, 
                verbose=1,
                policy_kwargs=policy_kwargs,
                batch_size=1536,
                learning_rate=0.001,
                buffer_size=100000,
                learning_starts=0,
                train_freq=(1, 'step'),
                seed=0,
                ent_coef='auto_0.5',
                target_entropy=-5.0,
                gradient_steps=10
                )
    
    #加载 replay buffer综合训练，记得修改buffer采样
    replay_buffer_path = "logs_norm/merged_replay_buffer.pkl"  # 你的缓冲池文件路径
    with open(replay_buffer_path, "rb") as f:
        model.replay_buffer = pickle.load(f)

    print(model.actor)
    print(model.critic)
    
    # 训练模型
    model.learn(total_timesteps=10000, log_interval=1, callback=callback)

    # 保存模型和VecNormalize
    model.save("SAC_fin")

if run == 'continue_train':
  checkpoint_callback = CheckpointCallback(
    save_freq=20,
    save_path="./logs_norm/",
    name_prefix="rl_model_norm",
    save_replay_buffer=True,
    save_vecnormalize=True,
  )
  callback=[checkpoint_callback]

  env = DummyVecEnv([lambda: myEnv_flow()])
  policy_kwargs = dict(activation_fn=torch.nn.ReLU,net_arch=dict(pi=[256, 256, 256], qf=[256, 256, 256]))
  # 从目录中加载训练过的模型，可适当修改经验池，学习率等
  model = SAC.load(load_model_path,
                   env=env,
                   learning_rate=0.001,
                   action_noise=None,
                   batch_size=1536,
                   learning_starts = 0,
                   ent_coef='auto',
                   target_entropy=-8.0, 
                   gradient_steps=10,
                   train_freq=(5, 'step'),
                   )
  
  # 读取经验缓冲池，帮助策略训练
  model.load_replay_buffer(load_buffer_path)

  print(model.actor)
  print(model.critic) 
  print(model.batch_size)
  print(model.replay_buffer.size())
  print(model.learning_rate)
  print(model._n_updates)
  print(model.gradient_steps)
  model.learn(total_timesteps=10000, log_interval=1, callback=callback, reset_num_timesteps= False)
  model.save("SAC_fin")

if run == 'eval':
  model_path=f"logs_norm/rl_model_norm_1200_steps.zip"
  env = DummyVecEnv([lambda: myEnv_flow()])
  model = SAC.load(model_path,env = env)
  t1 = time.time()
  obs = env.reset()
  j=0
  # 循环控制评估10步
  while True:
    j=j+1
    t2 = time.time()
    print('当前已耗费时间',t2-t1)
    action, _states = model.predict(obs, deterministic=True)
    obs, reward, done, info = env.step(action)
    t3 = time.time()
    print('当前STEP耗费时间',t3-t2)
    if j==39:
      break

if run == 'update':
    def load_replay_buffer(file_path):
        """加载指定的 ReplayBuffer"""
        with open(file_path, "rb") as f:
            return pickle.load(f)

    def save_replay_buffer(replay_buffer, file_path):
        """保存 ReplayBuffer"""
        updated_path = file_path.replace(".pkl", "_updated.pkl")  # 生成新文件名
        with open(updated_path, "wb") as f:
            pickle.dump(replay_buffer, f)
        print(f"✅ ReplayBuffer 已成功保存到: {updated_path}")

    def print_latest_samples(replay_buffer, num_samples=3):
        """打印 ReplayBuffer 中最新的 num_samples 组数据"""
        max_index = min(num_samples, replay_buffer.size())  # 确保不会超出缓冲池数据
        print(f"\n📌 当前 ReplayBuffer 存储数量: {replay_buffer.size()}")
        print(f"📌 当前存储位置: {replay_buffer.pos}")
        print(f"📌 是否已满: {replay_buffer.full}")

        start_index = max(replay_buffer.pos - max_index, 0)  # 计算最新数据的起始索引
        for i in range(start_index, replay_buffer.pos):
            print(f"\n🟢 样本索引 {i}:")
            print(f"🔹 状态 (obs): \n{replay_buffer.observations[i]}")
            print(f"🔸 动作 (action): \n{replay_buffer.actions[i]}")
            print(f"⭐ 奖励 (reward): \n{replay_buffer.rewards[i]}")
            print(f"⛔ 是否终止 (done): \n{replay_buffer.dones[i]}")
            print(f"➡️  下一个状态 (next_obs): \n{replay_buffer.next_observations[i]}")
            print("-" * 80)

    def insert_custom_data(replay_buffer, custom_data, num_writes=1):
        """向 ReplayBuffer 手动写入指定数据"""
        for _ in range(num_writes):
            index = replay_buffer.pos  # 获取当前写入索引
            obs, next_obs, action, reward, done = custom_data

            replay_buffer.observations[index] = np.array(obs)
            replay_buffer.next_observations[index] = np.array(next_obs)
            replay_buffer.actions[index] = np.array(action)
            replay_buffer.rewards[index] = np.array(reward)
            replay_buffer.dones[index] = np.array(done)

            # 更新 ReplayBuffer 索引
            replay_buffer.pos += 1
            if replay_buffer.pos >= replay_buffer.buffer_size:
                replay_buffer.full = True
                replay_buffer.pos = 0  # 重新开始覆盖旧数据

            print(f"✅ 已写入新数据到索引 {index}")

        return replay_buffer

    # **🔹 1. 指定要加载的 ReplayBuffer 文件**
    file_path = "logs_norm/rl_model_norm_replay_buffer_700_steps_2.pkl"
    replay_buffer = load_replay_buffer(file_path)

    # **🔹 2. 查看 ReplayBuffer 最新的 3 组数据**
    print("📌 加载 ReplayBuffer，查看最新 3 组数据:")
    print_latest_samples(replay_buffer, num_samples=3)

    # **🔹 3. 人为写入新数据（指定写入次数）**
    custom_data = (
        [[0.5, 1.751, 0.476]],  # 观测值 obs
        [[0.5, 1.621, 0.401]],  # 下一个观测值 next_obs
        [[-1, -1, -0.1, 1]],  # 动作 action
        [0.70243],  # 奖励 reward
        [0]  # 是否终止 done
    )
    num_writes = 80  # 指定写入次数
    replay_buffer = insert_custom_data(replay_buffer, custom_data, num_writes=num_writes)

    # **🔹 4. 保存更新后的 ReplayBuffer**
    save_replay_buffer(replay_buffer, file_path)

    # **🔹 5. 重新加载并查看最新的 3 组数据，确保写入成功**
    updated_replay_buffer = load_replay_buffer(file_path.replace(".pkl", "_updated.pkl"))
    print("\n📌 写入后 ReplayBuffer，查看最新 3 组数据:")
    print_latest_samples(updated_replay_buffer, num_samples=3)

if run == 'merge':

    def load_replay_buffer(file_path):
        """加载 ReplayBuffer 文件"""
        with open(file_path, "rb") as f:
            return pickle.load(f)

    def print_latest_samples(replay_buffer, file_name, num_samples=3):
        """打印 ReplayBuffer 中最新的 num_samples 组数据"""
        max_index = min(num_samples, replay_buffer.size())
        print(f"\n{file_name} 存储数量: {replay_buffer.size()}")
        print(f"当前存储位置: {replay_buffer.pos}")
        print(f"是否已满: {replay_buffer.full}")

        start_index = max(replay_buffer.pos - max_index, 0)
        for i in range(start_index, replay_buffer.pos):
            print(f"\n 样本索引 {i}:")
            print(f"状态 (obs): \n{replay_buffer.observations[i]}")
            print(f"动作 (action): \n{replay_buffer.actions[i]}")
            print(f"奖励 (reward): \n{replay_buffer.rewards[i]}")
            print(f"是否终止 (done): \n{replay_buffer.dones[i]}")
            print(f"下一个状态 (next_obs): \n{replay_buffer.next_observations[i]}")
            print("-" * 80)

    # 路径配置
    target_file = "logs_norm/rl_model_norm_replay_buffer_700_steps-0.pkl"
    injection_files = [
        'logs_norm/rl_model_norm_replay_buffer_700_steps-5.pkl',
        'logs_norm/rl_model_norm_replay_buffer_700_steps-10.pkl',
        'logs_norm/rl_model_norm_replay_buffer_700_steps-15.pkl',
        'logs_norm/rl_model_norm_replay_buffer_700_steps-30.pkl',
        'logs_norm/rl_model_norm_replay_buffer_600_steps-45.pkl'
    ]

    # 加载目标缓冲池
    replay_buffer_target = load_replay_buffer(target_file)
    buffer_size = replay_buffer_target.buffer_size
    pos_target = replay_buffer_target.pos

    # 逐个注入
    for injection_file in injection_files:
        replay_buffer_inject = load_replay_buffer(injection_file)
        inject_size = replay_buffer_inject.size()

        print(f"\n注入文件: {injection_file} 最新 3 组数据:")
        print_latest_samples(replay_buffer_inject, injection_file, num_samples=3)

        num_to_add = min(buffer_size, inject_size)
        indices_to_copy = np.arange(0, num_to_add)

        for idx in indices_to_copy:
            replay_buffer_target.observations[pos_target] = replay_buffer_inject.observations[idx]
            replay_buffer_target.next_observations[pos_target] = replay_buffer_inject.next_observations[idx]
            replay_buffer_target.actions[pos_target] = replay_buffer_inject.actions[idx]
            replay_buffer_target.rewards[pos_target] = replay_buffer_inject.rewards[idx]
            replay_buffer_target.dones[pos_target] = replay_buffer_inject.dones[idx]

            pos_target += 1
            if pos_target >= buffer_size:
                pos_target = 0
                replay_buffer_target.full = True

    # 更新缓冲池的指针位置
    replay_buffer_target.pos = pos_target

    # 保存新文件
    updated_filename = target_file.replace(".pkl", "_merged.pkl")
    with open(updated_filename, "wb") as f:
        pickle.dump(replay_buffer_target, f)

    print(f"\n合并完成！新缓冲池已保存至 {updated_filename}")
    print(f" 目标缓冲池更新后存储位置: {replay_buffer_target.pos}")

    # 检查合并后的内容
    updated_replay_buffer = load_replay_buffer(updated_filename)
    print("\n更新后的最新 3 组数据:")
    print_latest_samples(updated_replay_buffer, updated_filename, num_samples=3)

if run == 'newinject':

    def load_replay_buffer(file_path):
        """加载 ReplayBuffer 文件"""
        with open(file_path, "rb") as f:
            return pickle.load(f)

    def print_latest_samples(replay_buffer, file_name, num_samples=3):
        """打印 ReplayBuffer 中最新的 num_samples 组数据"""
        max_index = min(num_samples, replay_buffer.size())
        print(f"\n{file_name} 存储数量: {replay_buffer.size()}")
        print(f"当前存储位置: {replay_buffer.pos}")
        print(f"是否已满: {replay_buffer.full}")

        start_index = max(replay_buffer.pos - max_index, 0)
        for i in range(start_index, replay_buffer.pos):
            print(f"\n 样本索引 {i}:")
            print(f"状态 (obs): \n{replay_buffer.observations[i]}")
            print(f"动作 (action): \n{replay_buffer.actions[i]}")
            print(f"奖励 (reward): \n{replay_buffer.rewards[i]}")
            print(f"是否终止 (done): \n{replay_buffer.dones[i]}")
            print(f"下一个状态 (next_obs): \n{replay_buffer.next_observations[i]}")
            print("-" * 80)

    injection_file = "logs_norm/rl_model_norm_replay_buffer_700_steps-5.pkl"
    target_file = "logs_norm/rl_model_norm_replay_buffer_700_steps.pkl"

    replay_buffer_inject = load_replay_buffer(injection_file)
    replay_buffer_target = load_replay_buffer(target_file)

    print("注入文件的最新 3 组数据:")
    print_latest_samples(replay_buffer_inject, injection_file, num_samples=3)

    buffer_size = replay_buffer_target.buffer_size
    pos_target = replay_buffer_target.pos
    inject_size = replay_buffer_inject.size()

    num_to_add = min(700, inject_size)
    indices_to_copy = np.arange(0, num_to_add)

    for idx in indices_to_copy:
        replay_buffer_target.observations[pos_target] = replay_buffer_inject.observations[idx]
        replay_buffer_target.next_observations[pos_target] = replay_buffer_inject.next_observations[idx]
        replay_buffer_target.actions[pos_target] = replay_buffer_inject.actions[idx]
        replay_buffer_target.rewards[pos_target] = replay_buffer_inject.rewards[idx]
        replay_buffer_target.dones[pos_target] = replay_buffer_inject.dones[idx]

        pos_target += 1
        if pos_target >= buffer_size:
            pos_target = 0
            replay_buffer_target.full = True

    replay_buffer_target.pos = pos_target

    updated_filename = target_file.replace(".pkl", "_updated.pkl")
    with open(updated_filename, "wb") as f:
        pickle.dump(replay_buffer_target, f)

    print(f"\n合并完成！新缓冲池已保存至 {updated_filename}")
    print(f" 目标缓冲池更新后存储位置: {replay_buffer_target.pos}")

    updated_replay_buffer = load_replay_buffer(updated_filename)
    print("\n更新后的最新 3 组数据:")
    print_latest_samples(updated_replay_buffer, updated_filename, num_samples=3)