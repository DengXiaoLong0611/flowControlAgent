import matplotlib.pyplot as plt

# 初始化三个空列表来存储 wind_velocity、coef_1 和 coef_2 的值
wind_velocities = []
coef_1_values = []
coef_2_values = []
folders = []

# 读取 results.txt 文件
with open('results.txt', 'r') as f:
    for line in f:
        # 按照文件格式解析每一行数据
        parts = line.split()
        wind_velocity = float(parts[1])  # 读取 wind_velocity
        coef_1 = float(parts[3])         # 读取 coef_1
        coef_2 = float(parts[5])         # 读取 coef_2
        folder_name = parts[7]           # 读取文件夹名称（如果有额外字段）

        # 将 wind_velocity、coef_1、coef_2 和文件夹名添加到各自的列表中
        wind_velocities.append(wind_velocity)
        coef_1_values.append(coef_1)
        coef_2_values.append(coef_2)
        folders.append(folder_name)

# 创建一个1x3的图形布局
fig, axs = plt.subplots(1, 3, figsize=(15, 5))

# 绘制 wind_velocity 的变化曲线
axs[0].plot(folders, wind_velocities, marker='o', color='b')
axs[0].set_title('Wind Velocity')
axs[0].set_xlabel('Folder')
axs[0].set_ylabel('Wind Velocity')

# 绘制 coef_1 的变化曲线
axs[1].plot(folders, coef_1_values, marker='o', color='g')
axs[1].set_title('Coefficient 1')
axs[1].set_xlabel('Folder')
axs[1].set_ylabel('Coef 1')

# 绘制 coef_2 的变化曲线
axs[2].plot(folders, coef_2_values, marker='o', color='r')
axs[2].set_title('Coefficient 2')
axs[2].set_xlabel('Folder')
axs[2].set_ylabel('Coef 2')

# 调整布局
plt.tight_layout()
plt.show()
