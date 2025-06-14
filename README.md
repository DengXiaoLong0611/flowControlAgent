<<<<<<< HEAD
# flowControlAgent
=======
# 桥梁流动控制智能体思维框架
# 🧠 flowControlAgent

一个集成了大语言模型（LLM）与深度强化学习（DRL）的智能体框架，用于桥梁流动控制、文献检索、多模态任务规划与响应控制。

***

## 📂 项目结构

    flowControlAgent/
    ├── src/                  # 源码目录，包含 agent 框架、接口调用
    ├── data/                 # 数据存储目录（大文件已忽略）
    ├── logs/                 # 运行日志目录
    ├── examples/             # 示例使用脚本
    ├── config/               # 配置文件，如 API Key（已被忽略）
    ├── requirements.txt      # Python依赖包
    ├── .gitignore            # Git 忽略规则
    ├── README.md             # 当前说明文档

***

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 设置环境变量（如 OpenAI Key）

新建 `.env` 文件：

    OPENAI_API_KEY=sk-xxxx

（⚠️ `.env` 文件已自动忽略，确保不会上传 GitHub）

***

### 启动示例

```bash
python examples/react_example.py
```

或者运行 Gradio 界面：

```bash
python src/api/chat_with_webui.py
```

***

## 🧠 模块功能说明

| 模块                    | 描述            |
| --------------------- | ------------- |
| `frameworks/react.py` | ReAct 推理策略实现  |
| `core/indexer.py`     | 文本向量索引与检索逻辑   |
| `api/chat.py`         | LLM 对话 API 封装 |
| `utils/utils.py`      | 辅助功能函数集合      |



## 模块实现了两种思维框架，用于增强土木工程智能体的推理和决策能力：

1. Plan-and-Execute 框架
2. ReAct 框架

## 功能特点

- 支持多步骤任务规划
- 动态工具调用
- 状态管理和历史记录
- 结构化输出
- 错误处理和恢复机制

## 使用方法

### 1. 初始化思维框架

```python
from thought_framework import PlanAndExecute, ReAct
from llama_index.core import VectorStoreIndex
from llama_index.llms.openai import OpenAI

# 初始化向量索引和语言模型
index = VectorStoreIndex(...)
llm = OpenAI(...)

# 选择思维框架
framework = PlanAndExecute(index, llm)  # 或 ReAct(index, llm)
```

### 2. 处理查询

```python
# 异步处理查询
response = await framework.process_query("如何设计一个抗震结构？")
print(response)
```

## 思维框架说明

### Plan-and-Execute 框架

该框架将复杂任务分解为可执行的步骤：

1. 规划阶段：将任务分解为具体步骤
2. 执行阶段：按顺序执行每个步骤
3. 结果整合：汇总所有步骤的结果

特点：

- 适合处理结构化的多步骤任务
- 支持并行执行
- 可以动态调整执行计划

### ReAct 框架

该框架通过思考-行动-观察的循环来解决问题：

1. 思考（Reasoning）：分析当前情况并决定下一步行动
2. 行动（Acting）：执行选定的工具
3. 观察（Observing）：分析行动结果并更新理解

特点：

- 适合处理动态和不确定的任务
- 支持迭代优化
- 可以处理意外情况

## 工具集成

框架支持以下工具：

1. 知识库搜索

   - 搜索相关文档
   - 提取关键信息
2. 风效应计算

   - 风压力计算
   - 荷载计算
   - 结构风致振动位移采集

3. 结构风致振动稳定性分析

   - 受力分析
   - 稳定性分析

4. 流动控制工具调用

   - 吹吸气射流-流量控制器
   - 吹吸气射流-合成射流装置
   - 垂直轴风机流动控制
   - 可变外形翼板流动控制

## 示例

### 使用 Plan-and-Execute 框架

```python
# 创建框架实例
framework = PlanAndExecute(index, llm)

# 处理复杂查询
query = "设计一个30层高层建筑的抗震结构，需要考虑地震烈度8度"
response = await framework.process_query(query)
```

### 使用 ReAct 框架

```python
# 创建框架实例
framework = ReAct(index, llm)

# 处理动态查询
query = "分析这个结构在强震作用下的响应"
response = await framework.process_query(query)
```

## 注意事项

1. 确保向量索引已正确加载
2. 配置适当的语言模型参数
3. 处理异常情况
4. 监控资源使用

## 扩展开发

可以通过以下方式框架：

1. 添加新的工具
2. 自定义提示词模板
3. 实现新的思维框架
4. 优化执行策略




协作流程：

1.  创建分支：`git checkout -b feature/xxx`

2.  提交更改并推送：`git push origin feature/xxx`

3.  GitHub 上发起 Pull Request（PR）

***

## 📄 License

本项目遵循 MIT 开源协议。

***

## 🙋 联系

作者：[hero19950611](https://github.com/hero19950611)\
欢迎通过 Issues、PR 或 Discussions 参与贡献！
