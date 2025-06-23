import pickle
import seaborn as sns
import matplotlib.pyplot as plt

data = pickle.load(open('saved_buffer.pkl', 'rb'))
def pic(data):
    data = data[:len(data)]

    # 创建2x2子图
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))

    # 绘制 act_perturb 的 KDE
    sns.kdeplot(data.act_perturb, fill=True, color='blue', ax=axes[0, 0])
    axes[0, 0].set_title('act_perturb')
    axes[0, 0].set_xlim(-2, 2)

    # 绘制 obs0 的 KDE
    sns.kdeplot(data.obs[:, 0], fill=True, color='blue', ax=axes[0, 1])
    axes[0, 1].set_title('obs0')
    axes[0, 1].set_xlim(-1, 1)

    # 绘制 obs1 的 KDE
    sns.kdeplot(data.obs[:, 1], fill=True, color='blue', ax=axes[1, 0])
    axes[1, 0].set_title('obs1')
    axes[1, 0].set_xlim(-1, 1)

    # 绘制 obs2 的 KDE
    sns.kdeplot(data.obs[:, 2], fill=True, color='blue', ax=axes[1, 1])
    axes[1, 1].set_title('obs2')
    axes[1, 1].set_xlim(-8, 8)

    # 设置整体标题
    plt.suptitle('Kernel Density Estimation (KDE) Plots')

    # 调整布局
    plt.tight_layout()
    import time
    # 保存图形
    plt.savefig(r'figure\kde_plots+{}.png'.format(time.time()), dpi=450)

    # 显示图形
    plt.show()


if __name__=='__main__':
    pic(data)