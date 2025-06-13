import asyncio
import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.frameworks.react import ReAct
from llama_index.core import VectorStoreIndex
from llama_index.llms.openai import OpenAI

# 加载环境变量
load_dotenv()

async def main():
    # 初始化语言模型
    llm = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-3.5-turbo"
    )
    
    # 初始化向量索引
    index = VectorStoreIndex([])
    
    # 创建ReAct框架实例
    react_framework = ReAct(index, llm)
    
    # 示例查询
    queries = [
        "如何设计一个高效的吹吸气流动控制系统抑制桥梁涡激振动？请考虑以下方面：1. 控制策略 2. 传感器布置 3. 执行器选择 4. 控制算法",
        "在桥梁流动控制中，如何优化吹吸气控制器的位置？",
        "如何评估吹吸气流动控制系统对于桥梁涡激振动抑制的性能？"
    ]
    
    for query in queries:
        print(f"\n问题: {query}")
        print("-" * 50)
        
        # 获取思维过程
        result = await react_framework.process_query(query)
        
        # 打印结果
        print("\n最终答案:")
        print(result)
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 