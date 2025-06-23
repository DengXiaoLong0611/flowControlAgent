import time
import torch
import numpy as np
from wind_tunnel import wind_tunnel_env
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.noise import NormalActionNoise
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize


run = 'train'
# 注意train_load时更改文件目录
wind_tunnel_env = DummyVecEnv([lambda: wind_tunnel_env()])
num_steps = 700
load_model_path = 'logs_norm\rl_model_norm_{}_steps.zip'.format(num_steps)
load_buffer_path = 'logs_norm\rl_model_norm_replay_buffer_{}_steps.pkl'.format(num_steps)
load_normalize_env_path = 'logs_norm\rl_model_norm_vecnormalize_{}_steps.pkl'.format(num_steps)

if run == 'train':
    # Save a checkpoint every 1000 steps
    checkpoint_callback = CheckpointCallback(
    save_freq=20,
    save_path="./logs_norm/",
    name_prefix="rl_model_norm",
    save_replay_buffer=True,
    save_vecnormalize=True,
    )

    env = VecNormalize(wind_tunnel_env, norm_obs=False, norm_reward=True,clip_obs=10.)

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


if run == 'continue_train':
    print(time.time(),'!!!!!!!!!!!!!!!!!!!!')
    # Save a checkpoint every 1000 steps
    checkpoint_callback = CheckpointCallback(
    save_freq=20,
    save_path="./logs_norm/",
    name_prefix="rl_model_norm",
    save_replay_buffer=True,
    save_vecnormalize=True,
    )

    env = VecNormalize.load(load_normalize_env_path,env)

    model = SAC.load(load_model_path,
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
    model.load_replay_buffer(load_buffer_path)

    print(model.actor)
    print(model.critic) 
    print(model.batch_size)
    print(model.replay_buffer.size())
    print(model.learning_rate)
    print(model._n_updates)

    model.learn(total_timesteps=10000, log_interval=1,callback=checkpoint_callback,reset_num_timesteps= False)

    model.save("sac_pendulum")

if run =='eval':

    env = VecNormalize.load(load_normalize_env_path,env)
    model = SAC.load(load_model_path,env = env)
    t1 = time.time()
    obs = env.reset()
    while True:
        t2 = time.time()
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)

        if done:
            t3 = time.time()
            print("Episode time: ", t3-t1)
            obs = env.reset()