import gymnasium as gym
import pickle
from tianshou.data import ReplayBuffer
import torch.nn as nn
import torch

from tianshou.data import Batch
import numpy as np
from torch.distributions import kl_divergence
import torch.distributions as td
import copy
def kl_diverge(m1, m2):
    return 0.5 * (np.trace(np.linalg.inv(m2.cov).dot(m1.cov)) + 
                  np.log(np.linalg.det(m2.cov) / np.linalg.det(m1.cov)) - 
                  m1.cov.shape[0] + np.dot(np.dot((m2.mean - m1.mean).T, np.linalg.inv(m2.cov)), (m2.mean - m1.mean)))


def collect_data(env, policy_nn, sigma_k, delta, buffer, buffer_size_onetime, device = 'cpu'):
    start_num = len(buffer)
    policy_nn = policy_nn.to(device)
    policy_nn_perturb = copy.deepcopy(policy_nn).to(device)
    policy_nn_perturb.apply_noise(sigma_k)
    obs,_ = env.reset()
    random_std = np.random.uniform(0, 3) # 调太大会有很多堆积在边界值
    step = 0
    trajectory = []
    # kl_list = []
    while True:
        step += 1
        pre_a = np.random.normal(0, random_std)
        (act_mean, act_std), _ = policy_nn(obs = torch.tensor(obs,dtype=torch.float32).reshape(1, -1).to(device))
        (act_mean_perturb, act_std_perturb), _ = policy_nn_perturb(torch.tensor(obs,dtype=torch.float32).reshape(1, -1))
        act_mean, act_std = act_mean.detach().cpu().numpy(), act_std.detach().cpu().numpy()
        act_mean_perturb, act_std_perturb = act_mean_perturb.detach().cpu().numpy(), act_std_perturb.detach().cpu().numpy()
        
        
        kl = kl_divergence(td.normal.Normal(float(act_mean), float(act_std)), td.normal.Normal(float(act_mean_perturb), float(act_std_perturb)))
        if kl >= delta:
            sigma_k /= 1.01
        else:
            sigma_k *= 1.01

        act = act_mean + pre_a
        act_perturb = act_mean_perturb + pre_a
        act = np.tanh(act).reshape(env.action_space.shape)*env.action_space.high[0]
        act_perturb = np.tanh(act_perturb).reshape(env.action_space.shape)*env.action_space.high[0]

        obs_next, reward,terminated,truncated,_ = env.step(act_perturb)
        # print(step, step_terminated, act, act_perturb, reward)
        data = Batch(obs={},act={},act_perturb = {},rew={},terminated={},truncated={},obs_next={})

        data.update(
                obs = obs.astype(np.float32),
                act = act.astype(np.float32),
                act_perturb = act_perturb.astype(np.float32),
                obs_next=obs_next.astype(np.float32),
                rew=np.array(reward).astype(np.float32),
                terminated=terminated,
                truncated=truncated,
            )
        
        trajectory.append(data)

        obs = obs_next

        if terminated or truncated:
            
            obs, _ = env.reset()

            if reward > 0:
                k = 1
            else:
                k = 1
            found = False
            for _ in range(k):    
                for i in trajectory:
                    buffer.add(i)

                    if len(buffer) == (start_num + buffer_size_onetime):
                        found = True
                        break
                if found == True:
                    break

            trajectory = []
            random_std = np.random.uniform(0, 3)

        policy_nn_perturb.load_state_dict((policy_nn.state_dict()))
        policy_nn_perturb.apply_noise(sigma_k)
        
        if len(buffer) == start_num + buffer_size_onetime:
            print('buffer_num: ', len(buffer))
            pickle.dump(buffer, open('buffer.pkl', "wb"))
            break
    return buffer

if __name__ == "__main__":
    from tianshou.utils.net.common import Net
    from tianshou.utils.net.continuous import ActorProb, Critic
    import copy
    seed = 1
    np.random.seed(seed)
    torch.manual_seed(seed)
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    env = gym.make("MountainCarContinuous-v0")
    policy_net = Net(
    env.observation_space.shape[0],
    hidden_sizes=[64,64],
    norm_layer=[nn.LayerNorm, nn.LayerNorm],
    activation=nn.Tanh,
    device=device,
    )
    # for name, param in policy_net.named_parameters():
    #     print(name)
    # print(policy_net.model)

    class Custom_Net(ActorProb):
        def apply_noise(self, std_dev):
            with torch.no_grad():
                for name, param in self.named_parameters():
                    if '0' in name or '3' in name:
                        x = torch.normal(0, std_dev, size=param.size()).to(device)
                        param.add_(x)
                # print('apply new parameter noise!')

    collect_nn = Custom_Net(policy_net, env.action_space.shape[0], unbounded=False, device=device)
    # collect_nn_perturb = Custom_Net(policy_net, env.action_space.shape[0], unbounded=False, device=device)
    collect_nn_perturb = copy.deepcopy(collect_nn)
    from tianshou.data import ReplayBuffer
    buffer_size_onetime = 30000
    buffer = ReplayBuffer(buffer_size_onetime*30, 1)

    collect_data(env, collect_nn, collect_nn_perturb, 0.2, 1000, 0.05, buffer, 100000, device=device)