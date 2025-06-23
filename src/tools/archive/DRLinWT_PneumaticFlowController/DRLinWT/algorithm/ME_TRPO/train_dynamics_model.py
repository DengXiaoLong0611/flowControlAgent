from typing import Optional
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
from torch.utils.data import Dataset
import torch.nn.functional as F
import torch.nn as nn
from flow_env import DModel
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')



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





def train_models(env, 
                networks,
                state_data, 
                action_data, 
                next_state_data, 
                hidden_layers_size,
                batch_size = 2000, 
                learning_rate = 3e-4,
                max_num_epochs = 10000,
                device = 'cpu', 
                precision = 5
                ):



    X_train = torch.concatenate([torch.tensor(state_data), torch.tensor(action_data)], dim = 1)
    y_train = torch.tensor(next_state_data,dtype=torch.float32)
    # a = torch.max(X,dim = 0)
    # X = F.normalize(X, dim=1)

    # 若要在此处使用归一化 要保证后续的状态传入都进行相同的归一化
    # mean = torch.mean(X_train, dim=0)
    # std = torch.std(X_train, dim=0)
    # X_train = (X_train - mean) / (std+1e-12)

    max  = np.concatenate((env.observation_space.high,env.action_space.high))
    min  = np.concatenate((env.observation_space.low,env.action_space.low))
    X_train = (X_train - min) / (max-min)
    y_train = (y_train - env.observation_space.low) / (env.observation_space.high-env.observation_space.low)

    # 分割数据为训练集和测试集
    # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)


    # 创建自定义数据集类
    class CustomDataset(Dataset):
        def __init__(self, inputs, targets):
            self.inputs = inputs
            self.targets = targets

        def __len__(self):
            return len(self.inputs)

        def __getitem__(self, idx):
            return self.inputs[idx], self.targets[idx]

    # 创建训练和测试数据集
    train_dataset = CustomDataset(X_train, y_train)
    # test_dataset = CustomDataset(X_test, y_test)

    # 创建数据加载器
    batch_size = batch_size
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    # test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # 定义损失函数和优化器
    criterion = nn.MSELoss()
    optimizers = [optim.Adam(net.parameters(), lr=learning_rate) for net in networks]
    best_loss = np.inf
    stagnation_count = 0
    for epoch in range(max_num_epochs):
        # 对每个网络进行训练
        train_loss = 0
        for net, optimizer in zip(networks, optimizers):
            for inputs, targets in train_loader:
                inputs, targets = inputs.to(device), targets.to(device)  # 将数据移到 GPU
                optimizer.zero_grad()
                outputs = net(inputs)
                loss = criterion(outputs, targets)
                train_loss += loss.item()
                loss.backward()
                optimizer.step()
        if epoch % 5  == 0:
            train_loss = round(train_loss,precision)
            print('train_loss: ', train_loss, 'best_loss: ', best_loss, stagnation_count)
            if train_loss >= best_loss:
                    stagnation_count += 1
            else:
                stagnation_count = 0
                best_loss = train_loss

            if stagnation_count >= 5:
                print("Training stopped due to stagnation.")
                params_list = [net.state_dict() for net in networks]
                break
        
    return DModel(nets = params_list, hidden_layers_size=hidden_layers_size, is_test=False)

if __name__=='__main__':
    import gymnasium as gym
    import pickle
    env = gym.make("MountainCarContinuous-v0")
    
    # 随机生成训练数据
    data_size = 1000
    input_dim = env.observation_space.shape[0] + env.action_space.shape[0]
    output_dim = env.observation_space.shape[0]

    # X = torch.randn(data_size, env.observation_space.shape[0])  # 输入数据
    # y = torch.randn(data_size, env.action_space.shape[0])
    # y = torch.randn(data_size, 1)
    buffer = pickle.load(open(r'buffer.pkl', 'rb'))
    x = buffer.obs
    y = buffer.act
    z = buffer.act_perturb
    # import time
    # n = 0
    # for t in z:
    #     if t > 0:
    #         n+=1
    # print(n, len(z))
    # for i,j in zip(x,y):
    #     n += 1
    #     print(n, i, j)
    #     time.sleep(0.1)

    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    # print(n, len(x))
    # dynamics_models = train_models(env, buffer.obs, buffer.act_perturb, buffer.obs_next, n_networks=5)
    data = np.concatenate([x,y],axis=1)
    # data = [(1.0, 2.0, 3.0), (2.0, 3.0, 4.0), (3.0, 4.0, 5.0)]  # 这里只是示例数据

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    x = [d[0] for d in data]
    y = [d[1] for d in data]
    z = [d[2] for d in data]

    # ax.scatter(x, y, z, s=0.1, c = 'red')
    ax.scatter(x, y, z, s=0.1, c = 'blue')

    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')

    # plt.show()
    # plt.savefig('1.png', dpi = 450)





