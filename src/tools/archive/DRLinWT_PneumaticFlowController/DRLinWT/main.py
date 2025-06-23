import time
import torch
import numpy as np
from flow_env import myEnv_flow
from wind_tunnel import wind_tunnel_env
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.noise import NormalActionNoise
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.utils import set_random_seed
from example.MPS4264 import MPS4264
from example.flow_controller import flow_controller

set_random_seed(1)
# ips = ['191.30.90.184', '191.30.90.241']
# MPS = MPS4264(ips)
# MPS.TCP_send_command(MPS.device_ip[0],'CALZ')
# MPS.TCP_send_command(MPS.device_ip[1],'CALZ')

run = 'eval'
# 注意train_load时更改文件目录
# wind_tunnel_env = DummyVecEnv([lambda: myEnv_flow()])
num_steps = 800 
load_model_path = r'logs_norm_random_2mins_0003\rl_model_norm_{}_steps.zip'.format(num_steps)
load_buffer_path = r'logs_norm_random_2mins_0003\rl_model_norm_replay_buffer_{}_steps.pkl'.format(num_steps)
load_normalize_env_path = r'logs_norm_random_2mins_0003\rl_model_norm_vecnormalize_{}_steps.pkl'.format(num_steps)

if run == 'train':
    # Save a checkpoint every 1000 steps
    checkpoint_callback = CheckpointCallback(
    save_freq=10,
    save_path="./logs_norm/",
    name_prefix="rl_model_norm",
    save_replay_buffer=True,
    save_vecnormalize=True,
    )
    env = DummyVecEnv([lambda: myEnv_flow()])
    env = VecNormalize(env, norm_obs=False, norm_reward=True,clip_obs=10.)
    
    n_actions = env.action_space.shape[-1]
    policy_kwargs = dict(activation_fn=torch.nn.ReLU,
                        net_arch=dict(pi=[256,256], qf=[256,256]))
    action_noise = NormalActionNoise(mean=np.zeros(n_actions), sigma=0.1 * np.ones(n_actions))
    model = SAC("MlpPolicy", 
                env, 
                verbose=1,
                policy_kwargs = policy_kwargs,
                batch_size=128,
                learning_rate=0.001,
                buffer_size=100000,
                learning_starts=32,
                train_freq = (1,'step'),
                seed = 0,
                ent_coef='auto_0.3',
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
    save_freq=10,
    save_path="./logs_norm/",
    name_prefix="rl_model_norm",
    save_replay_buffer=True,
    save_vecnormalize=True,
    )
    env = DummyVecEnv([lambda: myEnv_flow()])
    env = VecNormalize.load(load_normalize_env_path,env)

    model = SAC.load(load_model_path,
                    env = env,
                    learning_rate = 0.001,
                    batch_size = 512,
                    learning_starts = 0,
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
    env = DummyVecEnv([lambda: myEnv_flow()])
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
            


def calculate_mse(list1, list2):
    """
    计算两个列表之间的均方误差

    参数:
    list1 -- 第一个列表，包含实际值
    list2 -- 第二个列表，包含预测值

    返回:
    mse -- 均方误差
    """
    # 确保两个列表长度相同
    assert len(list1) == len(list2), "列表长度不一致"

    # 将列表转换为NumPy数组
    arr1 = np.array(list1)
    arr2 = np.array(list2)

    # 计算均方误差
    mse = np.mean((arr1 - arr2) ** 2)

    return mse

if run =='test':
    import matplotlib.pyplot as plt
    import numpy as np
    env = DummyVecEnv([lambda: myEnv_flow()])
    env = VecNormalize.load(load_normalize_env_path,env)
    model = SAC.load(load_model_path,env = env)
    t1 = time.time()
    # obs = env.reset()
    # obs = np.linspace(0.2,1.1,50)
    mse_min = np.inf
    # x = [3,4,5,6,7,8,9,10]
    # y = [22,28,34,36,40,47,53,53]
    # xs = []
    # ys = []
    # for i in obs:
    #     action, _states = model.predict(np.array(i).reshape(1,), deterministic=True)
    #     xs.append(i*10)
    #     ys.append((action + 1)/2 * 70)
    # plt.plot(x,y, marker='o', label = 'target', markersize = 1, color = 'red')
    # plt.plot(xs,ys, marker='o', label = f'current_{num_steps}', markersize = 1, color = 'blue')
    # plt.xlim(3,10)
    # plt.savefig('results_v_a.png', dpi = 450)
    for i in range(200,1940,20):
        num = i
        load_model_path = r'logs_norm\rl_model_norm_{}_steps.zip'.format(num)
        load_buffer_path = r'logs_norm\rl_model_norm_replay_buffer_{}_steps.pkl'.format(num)
        load_normalize_env_path = r'logs_norm\rl_model_norm_vecnormalize_{}_steps.pkl'.format(num)
        env = DummyVecEnv([lambda: myEnv_flow()])
        env = VecNormalize.load(load_normalize_env_path,env)
        model = SAC.load(load_model_path,env = env)
        x = [3,4,5,6,7,8,9,10]
        y = [21,29,34,38,38,43,50,50]
        ys = []
        
        for i in x:
            action, _states = model.predict(np.array(i/10).reshape(1,), deterministic=True)
            ys.append((action + 1)/2 * 70)
            
        mse = calculate_mse(ys,y)
        print(ys,mse, num)
        if mse < mse_min:
            
            target_plot = ys
            target_num = num
            mse_min = mse
            print(mse_min)
    print(target_plot,mse_min)
    plt.plot(x,y, marker='o', label = 'target', markersize = 1, color = 'red')
    plt.plot(x,target_plot, marker='o', label = f'current_{target_num}', markersize = 1, color = 'blue')
    plt.legend()
    plt.xlim(3,10)
    plt.savefig('results_v_a.png', dpi = 450)
        
    
