import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI
from src.utils.utils import ThoughtFrameworkManager, ToolManager, StateManager, PromptManager
from src.frameworks.plan_execute import PlanAndExecute
from src.frameworks.react import ReAct

# 加载环境变量
load_dotenv()

async def main():
    # 1. 初始化必要的组件
    # 加载文档
    documents = SimpleDirectoryReader('data/raw/download_papers').load_data()
    # 创建索引
    index = VectorStoreIndex.from_documents(documents)
    # 初始化LLM
    llm = OpenAI(model="gpt-3.5-turbo")
    
    # 2. 初始化工具管理器
    tool_manager = ToolManager()
    
    # 注册一些示例工具
    async def search_papers(query: str) -> str:
        return f"搜索论文结果: {query}"
    
    async def analyze_paper(paper_id: str) -> str:
        return f"分析论文 {paper_id} 的结果"
    
    tool_manager.register_tool(
        name="search_papers",
        tool_func=search_papers,
        description="搜索相关论文",
        parameters={"query": "搜索关键词"}
    )
    
    tool_manager.register_tool(
        name="analyze_paper",
        tool_func=analyze_paper,
        description="分析特定论文",
        parameters={"paper_id": "论文ID"}
    )
    
    # 3. 初始化状态管理器
    state_manager = StateManager()
    
    # 4. 初始化提示词管理器
    prompt_manager = PromptManager()
    prompt_manager.register_prompt(
        "analysis",
        "请分析以下论文：{paper_title}\n关注点：{focus_points}"
    )
    
    # 5. 获取思维框架
    framework_manager = ThoughtFrameworkManager()
    
    # 使用Plan-and-Execute框架
    plan_execute = PlanAndExecute(index, llm)
    plan_execute.set_managers(tool_manager, state_manager, prompt_manager)
    
    # 使用ReAct框架
    react = ReAct(index, llm)
    react.set_managers(tool_manager, state_manager, prompt_manager)
    
    # 6. 执行查询
    query = "分析关于人工智能在土木工程中应用的论文"
    
    # 使用Plan-and-Execute框架处理
    print("使用Plan-and-Execute框架处理：")
    result_plan = await plan_execute.process_query(query)
    print(result_plan)
    
    # 使用ReAct框架处理
    print("\n使用ReAct框架处理：")
    result_react = await react.process_query(query)
    print(result_react)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 