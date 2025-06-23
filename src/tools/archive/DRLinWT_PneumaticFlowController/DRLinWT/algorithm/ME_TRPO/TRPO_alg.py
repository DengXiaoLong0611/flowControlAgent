import argparse
import os
import pprint

import gymnasium as gym
import numpy as np
import torch
from torch import nn
from torch.distributions import Independent, Normal
from torch.utils.tensorboard import SummaryWriter
from tianshou.data import ReplayBuffer, Collector, VectorReplayBuffer
from tianshou.env import DummyVectorEnv
from tianshou.policy import TRPOPolicy, TD3Policy, PGPolicy, PPOPolicy, DDPGPolicy, SACPolicy
from tianshou.trainer import OnpolicyTrainer
from tianshou.utils import TensorboardLogger
from tianshou.utils.net.common import Net
from tianshou.utils.net.continuous import ActorProb, Critic
# from collector import Collector
import copy

def trpo(
    train_env,
    test_env,
    policy_net,
    reward_threshold=99,
    seed=1,
    buffer_size=50000,
    lr=1e-3,
    gamma=0.95,
    epoch=100,
    step_per_epoch=50000,
    step_per_collect=2048,
    repeat_per_collect=2,# 每次更新网络后会进行一次测试
    batch_size=9999,
    hidden_sizes=[64,64],
    training_num=50,
    test_num=10,
    eval_num = 10,
    logdir="log",
    render=0.0,
    device="cuda" if torch.cuda.is_available() else "cpu",
    gae_lambda=0.95,
    rew_norm=1,
    norm_adv=1,
    optim_critic_iters=5,
    max_kl=0.005,
    backtrack_coeff=0.8,
    max_backtracks=10,
    # deterministic_eval = True,
    stop_n = 5, 
    last_rew = 0
):
    # 在这里执行你的 TRPO 算法，使用上面定义的参数
    # 你可以在函数体内根据这些参数来配置和运行 TRPO
    # 最后返回结果或相关信息
    env = train_env
    state_shape = train_env.observation_space.shape or train_env.observation_space.n
    action_shape = train_env.action_space.shape or train_env.action_space.n
    max_action = train_env.action_space.high[0]
    # if reward_threshold is None:
    #     default_reward_threshold = {"Pendulum-v0": -250, "Pendulum-v1": -250}
    #     reward_threshold = default_reward_threshold.get(task, train_envs[0].spec.reward_threshold)
    # you can also use tianshou.train_envs[0].SubprocVectorEnv
    # train_envs = gym.make(task)
    train_envs = DummyVectorEnv([lambda: copy.deepcopy(train_env) for _ in range(training_num)])
    # test_envs = gym.make(task)
    # test_envs = DummyVectorEnv([lambda: gym.make("Pendulum-v1") for _ in range(test_num)])
    test_envs = DummyVectorEnv([lambda: copy.deepcopy(train_env) for _ in range(test_num)])



    # train_envs = train_env
    # test_envs = train_env
    # seed
    np.random.seed(seed)
    torch.manual_seed(seed)
    train_envs.seed(seed)
    test_envs.seed(seed)
    # model
    # net = Net(
    #     state_shape,
    #     hidden_sizes=hidden_sizes,
    #     activation=nn.Tanh,
    #     device=device,
    # )
    # actor = ActorProb(policy_net, action_shape, unbounded=True, device=device).to(device)
    previous_net = copy.deepcopy(policy_net)
    actor = policy_net
    critic = Critic(
        Net(
            state_shape,
            hidden_sizes=hidden_sizes,
            device=device,
            activation=nn.Tanh,
        ),
        device=device,
    ).to(device)
    # orthogonal initialization
    for m in list(actor.modules()) + list(critic.modules()):
        if isinstance(m, torch.nn.Linear):
            torch.nn.init.orthogonal_(m.weight)
            torch.nn.init.zeros_(m.bias)
    optim = torch.optim.Adam(critic.parameters(), lr=lr)

    # replace DiagGuassian with Independent(Normal) which is equivalent
    # pass *logits to be consistent with policy.forward
    def dist(*logits):
        return Independent(Normal(*logits), 1)

    policy = TRPOPolicy(
        actor=actor,
        critic=critic,
        optim=optim,
        dist_fn=dist,
        discount_factor=gamma,
        reward_normalization=rew_norm,
        advantage_normalization=norm_adv,
        gae_lambda=gae_lambda,
        action_space=env.action_space,
        optim_critic_iters=optim_critic_iters,
        max_kl=max_kl,
        backtrack_coeff=backtrack_coeff,
        max_backtracks=max_backtracks,
        action_bound_method = 'tanh',
        deterministic_eval = True
        # deterministic_eval = deterministic_eval
    )
    old_policy = copy.deepcopy(policy)
    # collector
    train_collector = Collector(
        policy,
        train_envs,
        VectorReplayBuffer(buffer_size, len(train_envs)),
    )
    test_collector = Collector(policy, test_envs)
    # log
    log_path = os.path.join(logdir, "task", "trpo")
    writer = SummaryWriter(log_path)
    logger = TensorboardLogger(writer)

    def save_best_fn(policy):
        torch.save(policy.state_dict(), os.path.join(log_path, "policy.pth"))

    # import collections
    # rewards=[]
    # def stop_fn(mean_rewards):
    #     rewards.append(round(mean_rewards,3))
    #     if (len(rewards) > stop_n) and (np.max(rewards[-1*stop_n:]) <= np.max(rewards[:-1*stop_n])):
    #         # print(rewards) 
    #         return True
    #     else:
    #         return False

    # trainer
    trainer = OnpolicyTrainer(
        policy=policy,
        train_collector=train_collector,
        test_collector=None,
        max_epoch=epoch,
        step_per_epoch=step_per_epoch,
        repeat_per_collect=repeat_per_collect,
        episode_per_test=test_num,
        batch_size=batch_size,
        step_per_collect=step_per_collect,
        stop_fn=None,
        save_best_fn=save_best_fn,
        logger=logger,
    )

    # dynamics_envs = DummyVectorEnv([lambda: copy.deepcopy(train_env) for _ in range(eval_num)])
    # for i, T in enumerate(dynamics_envs.workers):
    #     T.is_test = i


    old_eval_env_list = []
    old_policy.eval()
    for index in range(eval_num):
        print('dynamics_env: ', index)
        T_env = copy.deepcopy(train_env)
        T_env.is_test = index
        old_collector = Collector(old_policy, T_env)
        old_result = old_collector.collect(n_episode=1)
        old_eval_env_list.append(old_result['rew'].mean())

    eval_epoch_list = []
    for epoch, epoch_stat, info in trainer:
        print("Epoch:", epoch)
        print(epoch_stat)
        print(info)
        if epoch % 3 == 0:

            policy.eval()
            eval_env_list = []
            
            for index in range(eval_num):
                print('dynamics_env: ', index)
                T_env = copy.deepcopy(train_env)
                T_env.is_test = index
                collector = Collector(policy, T_env)
                result = collector.collect(n_episode=1)
                eval_env_list.append(result['rew'].mean())

            comparisons = [1 if eval_env_list[i] > old_eval_env_list[i] else 0 for i in range(len(eval_env_list))]
            ratio = sum(comparisons) / len(eval_env_list)
            eval_epoch_list.append((np.mean(eval_env_list)))
            print('last_rew: ', last_rew)
            print('epoch rew: ', eval_epoch_list)
            print('ratio: ', ratio)

            if len(eval_epoch_list) > 5 and (np.max(eval_epoch_list[-1*stop_n:]) <= np.max(eval_epoch_list[:-1*stop_n])):
                break
            elif  ratio>= 0.7:
                policy.train()
                old_policy = copy.deepcopy(policy)
                old_eval_env_list = eval_env_list
                temporal_policy = copy.deepcopy(policy)
                continue
            else:
                if eval_epoch_list[-2] > last_rew:
                    policy = temporal_policy
                    break
                else:
                    return None, previous_net
            
    env = test_env
    policy.eval()
    collector = Collector(policy, env)
    result = collector.collect(n_episode=3, render=render)
    rews, lens = result["rews"], result["lens"]
    print(f"Real test reward: {rews.mean()}, length: {lens.mean()}")
    with open('virtual_rew.txt', 'a') as file:
        # 写入字符串到文件
        file.write(f"Final reward: {eval_epoch_list}\n")

    return rews.mean(), actor



if __name__=='__main__':
    import collections
    class Custom_Net(ActorProb):
        def apply_noise(self, std_dev):
            with torch.no_grad():
                for name, param in self.named_parameters():
                    if '0' in name or '3' in name:
                        # noise_mean  = random.uniform(-5,5)
                        noise_mean  = 0
                        x = torch.normal(noise_mean, std_dev, size=param.size()).to(device)
                        param.add_(x)


    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    seed = 1
    np.random.seed(seed)
    torch.manual_seed(seed)
    env = gym.make("Pendulum-v1")
    mean_rew_list = collections.deque(maxlen=25)
    mean_rew_max = 0

    policy_net = Net(
        env.observation_space.shape[0],
        hidden_sizes=[64,64],
        norm_layer=[nn.LayerNorm, nn.LayerNorm],
        activation=nn.Tanh,
        device=device,
    )

    # 扰动与非扰动网络
    import pickle
    policy_nn = Custom_Net(policy_net, env.action_space.shape[0], unbounded=False, conditioned_sigma=True, device=device).to(device)
    env = pickle.load(open('saved_networks.pkl', 'rb'))

    trpo(env, gym.make("Pendulum-v1"), policy_nn, eval_num=10)

