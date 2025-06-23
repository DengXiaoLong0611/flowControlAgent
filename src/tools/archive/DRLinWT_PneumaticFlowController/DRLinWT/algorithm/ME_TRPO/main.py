from train_dynamics_model import train_models
import gymnasium as gym
from collect_data_kl import collect_data
import torch
from tianshou.utils.net.common import Net
from torch import nn
from tianshou.utils.net.continuous import ActorProb
import numpy as np
import pickle
from tianshou.data import ReplayBuffer
from TRPO_alg import trpo
import copy

class Custom_Net(ActorProb):
    def apply_noise(self, std_dev):
        with torch.no_grad():
            for name, param in self.named_parameters():
                if '0' in name or '3' in name:
                    # noise_mean  = random.uniform(-5,5)
                    noise_mean  = 0
                    x = torch.normal(noise_mean, std_dev, size=param.size()).to(device)
                    param.add_(x)

class dynamics_model_Net(nn.Module):
    def __init__(self, input_size, hidden_sizes, output_size, dropout_prob=0.5):
        super(dynamics_model_Net, self).__init__()
        self.fc_layers = nn.ModuleList()  # 用于存储隐藏层

        # 创建隐藏层，并在每个隐藏层后添加BatchNorm和Dropout
        for hidden_size in hidden_sizes:
            self.fc_layers.append(nn.Linear(input_size, hidden_size))
            # self.fc_layers.append(nn.BatchNorm1d(hidden_size))  # 添加BatchNorm层
            self.fc_layers.append(nn.ReLU())  # 添加激活函数
            # self.fc_layers.append(nn.Dropout(p=dropout_prob))  # 添加Dropout层
            input_size = hidden_size

        self.output_layer = nn.Linear(input_size, output_size)  # 输出与指定的输出维度相同

    def forward(self, x):
        for layer in self.fc_layers:
            x = layer(x)
        output = self.output_layer(x)
        return output

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
seed = 1
np.random.seed(seed)
torch.manual_seed(seed)
env = gym.make("MountainCarContinuous-v0")
mean_rew_list = [-np.inf]
mean_rew_max = -np.inf

policy_net = Net(
    env.observation_space.shape[0],
    hidden_sizes=[64,64],
    norm_layer=[nn.LayerNorm, nn.LayerNorm],
    activation=nn.Tanh,
    device=device,
)


buffer_size_onetime = 5000
buffer = ReplayBuffer(buffer_size_onetime*20, 1)
delta = 0.6 # 临界值 delta
sigma_k = 0.6 # 扰动标准差
n_networks = 10
dynamics_model_hidden_layers_size = [512,512]
# 扰动与非扰动网络
policy_nn = Custom_Net(policy_net, env.action_space.shape[0], unbounded=False, conditioned_sigma=True, device=device).to(device)
n_states = env.observation_space.shape[0]
n_actions = env.action_space.shape[0]
num_networks = n_networks
input_size = n_states + n_actions  # 输入维度
output_size = n_states  # 输出维度
networks = [dynamics_model_Net(input_size, dynamics_model_hidden_layers_size, output_size).to(device) for _ in range(num_networks)]
# 差距参数

while True:

    buffer = collect_data(env, policy_nn, sigma_k, delta, buffer, buffer_size_onetime, device=device)
    # buffer = pickle.load(open(r'buffer.pkl', 'rb'))
    with open('saved_buffer.pkl', 'wb') as f:
        pickle.dump(buffer, f)
    # pic(buffer)
    len_buffer = len(buffer)
    x = buffer.act_perturb[:len_buffer]
    y = buffer.obs[:len_buffer]
    z = buffer.obs_next[:len_buffer]
    e = buffer.rew[:len_buffer]

    dynamics_models = train_models(env, networks, y, x, z, dynamics_model_hidden_layers_size, device=device, precision=5)
    with open('saved_networks.pkl', 'wb') as f:
        pickle.dump(dynamics_models, f)

    # collect_nn.load_state_dict(torch.load('collect_nn.pth'))
    mean_rew, policy_nn = trpo(dynamics_models, copy.deepcopy(env), policy_nn, last_rew = mean_rew_list[-1], eval_num=n_networks, device=device)
    torch.save(policy_nn.state_dict(), 'collect_nn.pth')

    if mean_rew is not None:
        mean_rew_list.append(mean_rew)
        with open('real_rew.txt', 'a') as file:
            # 写入字符串到文件
            file.write(f"Final reward: {mean_rew}\n")
        if mean_rew > mean_rew_max:
            mean_rew_max = mean_rew
    print('mean_rew_list: ', mean_rew_list)
    if len(mean_rew_list) == 25 and max(mean_rew_list) < mean_rew_max:
        break

























