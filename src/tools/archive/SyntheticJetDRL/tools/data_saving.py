import pandas as pd
import os
import matplotlib.pyplot as plt
import math
import seaborn as sns

def data_save(header, data, save_path):
    try:
        df = pd.read_csv(save_path)
    except FileNotFoundError:
        df = pd.DataFrame(columns=header)
    
    data_list = [[d] for d in data]
    data_dict = dict(zip(header, data_list))
    df = pd.concat([df, pd.DataFrame(data_dict)], ignore_index=True)
    df.to_csv(save_path, index = False, mode='w')

def line_data(file_path, data_name):
    df= pd.read_csv(file_path)
    return df[data_name]

def is_string_or_list_of_strings(variable):
    # 判断变量是否是单个字符串
    if isinstance(variable, str):
        return True
    # 判断变量是否是仅包含字符串的列表
    elif isinstance(variable, list) and all(isinstance(item, str) for item in variable):
        return True
    return False

def is_list_of_strings(variable):

    # 判断变量是否是仅包含字符串的列表
    if isinstance(variable, list) and all(isinstance(item, str) for item in variable):
        return True
    return False

def plot_data(file_path, data_name, save_path = None, **kwargs):

    df= pd.read_csv(file_path)

    if not is_string_or_list_of_strings(data_name):
        print('The data type should be a string or a list of strings!')
    elif isinstance(data_name, str):
        plt.plot(range(df[data_name].size), df[data_name], **kwargs)
        plt.show()
    elif ((len(data_name) == 1) and isinstance(data_name[0], str)):
        plt.plot(range(df[data_name[0]].size), df[data_name[0]], **kwargs)
        plt.show()
    else:
        num_figure = len(data_name)
        root = int(math.sqrt(num_figure))
        
        # 从root开始向下寻找最接近的因子
        for factor in range(root, 0, -1):
            if num_figure % factor == 0:  # 如果找到了一个因子
                x,y = factor, num_figure // factor  # 返回这个因子和相应的商

        fig, axes = plt.subplots(x, y, figsize=(3*y, 3*x))
        
        for i, ax in enumerate(axes.flatten()):
            if i < num_figure:
                sns.lineplot(data=df[data_name[i]], ax=ax, **kwargs)
                ax.set_title(f"Data {data_name[i]}")  # 设置子图的标题
                ax.set_xlabel('Steps')
            else:
                ax.axis('off')  # 隐藏多余的子图
        # 设置整体标题
        plt.tight_layout()
        if save_path is not None:
            plt.savefig(save_path, dpi = 450)
        plt.show()



if __name__=='__main__':
    # for i in range(5):
    #     header = ['x', 'y']
    #     data = [datalog,datalog]
    #     data_save(header, data, 'test.csv')
    #     print(i)

    # x = line_data('test.csv', 'x')
    # print(type('datalog') == 'str')

    plot_data('test.csv', ['x', 'y'], 'datalog.png')


















