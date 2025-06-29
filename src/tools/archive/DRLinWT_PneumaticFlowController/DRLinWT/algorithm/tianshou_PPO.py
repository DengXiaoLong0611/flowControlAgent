import argparse
import os
import pprint
from tabnanny import verbose

import gym
import numpy as np
import torch
from torch.distributions import Independent, Normal
from torch.utils.tensorboard import SummaryWriter
from torch.optim import lr_scheduler
from tianshou.data import Collector, VectorReplayBuffer
from tianshou.env import DummyVectorEnv
from tianshou.policy import PPOPolicy
from tianshou.trainer import OnpolicyTrainer
from tianshou.utils import TensorboardLogger
from tianshou.utils.net.common import ActorCritic, Net
from tianshou.utils.net.continuous import ActorProb, Critic


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', type=str, default='myenv-v0')   # 环境
    parser.add_argument('--reward-threshold', type=float, default=None) # 最大奖励阈值
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--buffer-size', type=int, default=50000)
    parser.add_argument('--lr', type=float, default=0.0005)
    parser.add_argument('--gamma', type=float, default=0.98)
    parser.add_argument('--epoch', type=int, default=500)
    parser.add_argument('--step-per-epoch', type=int, default=200)
    parser.add_argument('--episode-per-collect', type=int, default=2)
    parser.add_argument('--repeat-per-collect', type=int, default=200)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--hidden-sizes', type=int, nargs='*', default=[64])
    parser.add_argument('--training-num', type=int, default=1)
    parser.add_argument('--test-num', type=int, default=1)
    parser.add_argument('--logdir', type=str, default='log')
    parser.add_argument('--render', type=float, default=0.)
    parser.add_argument(
        '--device', type=str, default='cuda' if torch.cuda.is_available() else 'cpu'
    )
    # ppo special
    parser.add_argument('--vf-coef', type=float, default=0.25)  # 价值损失权重
    parser.add_argument('--ent-coef', type=float, default=0.01)  # 熵损失权重
    parser.add_argument('--eps-clip', type=float, default=0.1)  # 前后策略差
    parser.add_argument('--max-grad-norm', type=float, default=0.5) # 在反向传播中裁剪梯度
    parser.add_argument('--gae-lambda', type=float, default=0.95)   # 广义优势估计参数
    parser.add_argument('--rew-norm', type=int, default=0)  # 奖励标准化
    parser.add_argument('--dual-clip', type=float, default=None)    # 论文中提到的参数，要大于1
    parser.add_argument('--value-clip', type=int, default=1)    # 论文中提到的参数，默认为True
    parser.add_argument('--norm-adv', type=int, default=1)  # 是否做每小批量的优势标准化，'advantage_normalization'
    parser.add_argument('--recompute-adv', type=int, default=0) # 每次更新是否重新计算advantage
    parser.add_argument('--resume', default=False )    # 恢复训练过程
    parser.add_argument("--save-interval", type=int, default=1) # 保存周期
    parser.add_argument("--resume_from_log", type=bool, default=True) # 保存周期
    args = parser.parse_known_args()[0]
    return args


def test_ppo(args=get_args()):
    env = gym.make(args.task)
    args.state_shape = env.observation_space.shape or env.observation_space.n
    args.action_shape = env.action_space.shape or env.action_space.n
    args.max_action = env.action_space.high[0]
    if args.reward_threshold is None:
        default_reward_threshold = {"Pendulum-v0": -250, "Pendulum-v1": -250}
        args.reward_threshold = default_reward_threshold.get(
            args.task, env.spec.reward_threshold
        )
    # you can also use tianshou.env.SubprocVectorEnv
    # train_envs = gym.make(args.task)
    train_envs = gym.make(args.task)
    # test_envs = gym.make(args.task)
    test_envs = gym.make(args.task)
    # seed
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    train_envs.seed(args.seed)
    test_envs.seed(args.seed)
    # model
    net = Net(args.state_shape, hidden_sizes=args.hidden_sizes, device=args.device)  # 默认cpu
    actor = ActorProb(
        net, args.action_shape, max_action=args.max_action, device=args.device
    ).to(args.device)
    critic = Critic(
        Net(args.state_shape, hidden_sizes=args.hidden_sizes, device=args.device),
        device=args.device
    ).to(args.device)
    actor_critic = ActorCritic(actor, critic)
    # orthogonal initialization
    for m in actor_critic.modules():
        if isinstance(m, torch.nn.Linear):
            torch.nn.init.orthogonal_(m.weight)
            torch.nn.init.zeros_(m.bias)
    optim = torch.optim.Adam(actor_critic.parameters(), lr=args.lr)
    lr_sche = lr_scheduler.StepLR(optim,step_size = 80,gamma = 0.5,last_epoch= -1,verbose =1)
    # replace DiagGuassian with Independent(Normal) which is equivalent
    # pass *logits to be consistent with policy.forward
    def dist(*logits):
        return Independent(Normal(*logits), 1)

    policy = PPOPolicy(
        actor,
        critic,
        optim,
        dist,   # 用于计算动作的分布类
        discount_factor=args.gamma,
        max_grad_norm=args.max_grad_norm,
        eps_clip=args.eps_clip,
        vf_coef=args.vf_coef,
        ent_coef=args.ent_coef,
        reward_normalization=True,
        advantage_normalization=args.norm_adv,
        recompute_advantage=args.recompute_adv,
        dual_clip=args.dual_clip,
        value_clip=args.value_clip,
        gae_lambda=args.gae_lambda,
        action_space=env.action_space,
        lr_scheduler = lr_sche,
        action_bound_method = 'tanh'
    )
    # collector
    train_collector = Collector(
        policy, train_envs, VectorReplayBuffer(args.buffer_size, 1),exploration_noise = True
    )
    test_collector = Collector(policy, test_envs)
    # log
    log_path = os.path.join(args.logdir, args.task, "ppo")
    writer = SummaryWriter(log_path)
    logger = TensorboardLogger(writer, save_interval=args.save_interval)

    def save_best_fn(policy):
        torch.save(policy.state_dict(), os.path.join(log_path, "policy.pth"))

    def stop_fn(mean_rewards):
        return mean_rewards >= args.reward_threshold

    def save_checkpoint_fn(epoch, env_step, gradient_step):
        # see also: https://pytorch.org/tutorials/beginner/saving_loading_models.html
        ckpt_path = os.path.join(log_path, "checkpoint.pth")
        # Example: saving by epoch num
        # ckpt_path = os.path.join(log_path, f"checkpoint_{epoch}.pth")
        torch.save(
            {
                "model": policy.state_dict(),
                "optim": optim.state_dict(),
            }, ckpt_path
        )
        return ckpt_path

    if args.resume:
        # load from existing checkpoint
        print(f"Loading agent under {log_path}")
        ckpt_path = os.path.join(log_path, "checkpoint.pth")
        if os.path.exists(ckpt_path):
            checkpoint = torch.load(ckpt_path, map_location=args.device)
            policy.load_state_dict(checkpoint["model"])
            optim.load_state_dict(checkpoint["optim"])
            print("Successfully restore policy and optim.")
        else:
            print("Fail to restore policy and optim.")

    # trainer
    trainer = OnpolicyTrainer(
        policy,
        train_collector,
        None,
        args.epoch,
        args.step_per_epoch,
        args.repeat_per_collect,
        args.test_num,
        args.batch_size,
        episode_per_collect=args.episode_per_collect,
        stop_fn=stop_fn,
        save_best_fn=save_best_fn,
        logger=logger,
        resume_from_log=True,
        save_checkpoint_fn=save_checkpoint_fn,
    )

    for epoch, epoch_stat, info in trainer:
        print(f"Epoch: {epoch}")
        print(epoch_stat)
        with open('rew.txt','a') as f:
            f.write(str(epoch_stat['rew'])+'\n')
        print(info)

    assert stop_fn(info["best_reward"])

    if __name__ == "__main__":
        pprint.pprint(info)
        # Let's watch its performance!
        env = gym.make(args.task)
        policy.eval()
        collector = Collector(policy, env)
        result = collector.collect(n_episode=1, render=args.render)
        rews, lens = result["rews"], result["lens"]
        print(f"Final reward: {rews.mean()}, length: {lens.mean()}")


def test_ppo_resume(args=get_args()):
    args.resume = True
    test_ppo(args)


if __name__ == "__main__":
    test_ppo()