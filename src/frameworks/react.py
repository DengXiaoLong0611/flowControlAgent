from typing import List, Dict, Any, Tuple
from .base import ThoughtFramework
from llama_index.core import VectorStoreIndex
from llama_index.llms.openai import OpenAI
import json
import re
import asyncio
from abc import ABC, abstractmethod

class ThoughtFramework(ABC):
    """思维框架的基类"""
    def __init__(self, index, llm):
        self.index = index
        self.llm = llm
        self.history = []
    
    @abstractmethod
    async def process_query(self, query: str) -> Dict[str, Any]:
        """处理查询的抽象方法"""
        pass

class ReAct(ThoughtFramework):
    """ReAct框架实现"""
    def __init__(self, index, llm):
        super().__init__(index, llm)
        self.max_iterations = 5
        self.thought_prompt = """作为土木工程专家，请分析当前情况并决定下一步行动。
当前问题：{query}
历史信息：{history}
知识库信息：{knowledge}
可用工具：{available_tools}

请以JSON格式输出你的思考过程，格式如下：
{{
    "thought": "你的推理过程",
    "action": {{
        "tool": "要使用的工具名称",
        "parameters": {{
            "param1": "value1",
            "param2": "value2"
        }}
    }},
    "is_final_answer": false
}}
"""
        
        self.observation_prompt = """基于以下观察结果，请更新你的理解：
观察结果：{observation}
历史信息：{history}
知识库信息：{knowledge}

请以JSON格式输出你的分析，格式如下：
{{
    "understanding": "对观察结果的理解",
    "next_action": {{
        "tool": "下一步要使用的工具",
        "parameters": {{
            "param1": "value1"
        }}
    }},
    "is_final_answer": false
}}
"""
    
    async def _search_knowledge_base(self, query: str) -> str:
        """搜索知识库"""
        try:
            retriever = self.index.as_retriever(search_kwargs={"k": 5})  # 这里的5可以调整
            nodes = await retriever.aretrieve(query)
            if nodes:
                return "\n".join([node.text for node in nodes])
            
            # 如果在知识库中找不到信息，使用GPT模型的知识
            gpt_prompt = f"""作为土木工程专家，请回答以下问题。如果问题涉及专业知识，请提供详细的解释：

问题：{query}

请提供结构化的回答，包括：
1. 主要观点
2. 技术细节
3. 实际应用建议
"""
            response = self.llm.complete(gpt_prompt)
            return f"知识库中未找到相关信息，以下是基于GPT模型的知识：\n{response.text}"
            
        except Exception as e:
            return f"搜索知识库时出错: {str(e)}"
    
    async def think(self, context: str) -> str:
        """思考阶段"""
        # 首先从知识库搜索相关信息
        knowledge = await self._search_knowledge_base(context)
        
        # 构建提示词
        prompt = self.thought_prompt.format(
            query=context,
            history="\n".join(self.history),
            knowledge=knowledge,
            available_tools=json.dumps(self._get_available_tools(), ensure_ascii=False)
        )
        
        response = self.llm.complete(prompt)
        return response.text
        
    async def act(self, thought: str) -> str:
        """行动阶段"""
        try:
            # 解析思考结果
            action_data = json.loads(thought)
            tool_name = action_data["action"]["tool"]
            parameters = action_data["action"]["parameters"]
            
            # 根据工具名称执行相应的操作
            if tool_name == "search_knowledge_base":
                return await self._search_knowledge_base(parameters.get("query", ""))
            elif tool_name == "calculate":
                return await self._calculate(parameters)
            elif tool_name == "analyze_structure":
                return await self._analyze_structure(parameters)
            else:
                return f"未知工具: {tool_name}"
        except Exception as e:
            return f"执行行动时出错: {str(e)}"
        
    async def observe(self, action: str) -> str:
        """观察阶段"""
        # 从知识库搜索与行动结果相关的信息
        knowledge = await self._search_knowledge_base(action)
        
        # 构建提示词
        prompt = self.observation_prompt.format(
            observation=action,
            history="\n".join(self.history),
            knowledge=knowledge
        )
        
        response = self.llm.complete(prompt)
        return response.text
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """处理查询的主函数"""
        steps = []
        context = query
        
        # 第一轮思考-行动-观察
        thought1 = await self.think(context)
        action1 = await self.act(thought1)
        observation1 = await self.observe(action1)
        
        steps.append({
            "thought": thought1,
            "action": action1,
            "observation": observation1
        })
        
        # 第二轮思考-行动-观察
        thought2 = await self.think(observation1)
        action2 = await self.act(thought2)
        observation2 = await self.observe(action2)
        
        steps.append({
            "thought": thought2,
            "action": action2,
            "observation": observation2
        })
        
        # 生成最终答案
        final_answer = await self._synthesize_final_answer({
            "query": query,
            "steps": steps
        })
        
        return {
            "query": query,
            "steps": steps,
            "final_result": final_answer
        }
    
    async def _synthesize_final_answer(self, state: Dict[str, Any]) -> str:
        """整合所有信息生成最终答案"""
        try:
            # 从知识库搜索相关信息
            knowledge = await self._search_knowledge_base(state['query'])
            
            # 检查是否使用了GPT模型的知识
            using_gpt_knowledge = "知识库中未找到相关信息" in knowledge
            
            synthesis_prompt = f"""作为土木工程专家，请基于以下信息提供最终答案：

原始问题：{state['query']}

知识库信息：
{knowledge}

执行历史：
{json.dumps(state['steps'], ensure_ascii=False, indent=2)}

{'注意：部分信息来自GPT模型的知识库，请确保信息的准确性和适用性。' if using_gpt_knowledge else ''}

请提供一个结构化的总结，包括：
1. 主要发现
2. 关键结论
3. 建议措施
4. 局限性说明（如果使用了GPT模型的知识）
"""
            
            response = self.llm.complete(synthesis_prompt)
            return response.text
            
        except Exception as e:
            return f"生成最终答案时出错: {str(e)}"
    
    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return [
            {
                "name": "search_knowledge_base",
                "description": "搜索知识库获取相关信息",
                "parameters": {
                    "query": "搜索查询"
                }
            },
            {
                "name": "calculate",
                "description": "执行工程计算",
                "parameters": {
                    "formula": "计算公式",
                    "variables": "变量值"
                }
            },
            {
                "name": "analyze_structure",
                "description": "分析结构特性",
                "parameters": {
                    "structure_type": "结构类型",
                    "parameters": "结构参数"
                }
            }
        ]
    
    async def _calculate(self, parameters: Dict[str, Any]) -> str:
        """执行工程计算"""
        try:
            # 这里可以实现具体的计算逻辑
            return f"计算结果: {parameters}"
        except Exception as e:
            return f"计算过程出错: {str(e)}"
    
    async def _analyze_structure(self, parameters: Dict[str, Any]) -> str:
        """分析结构特性"""
        try:
            # 这里可以实现具体的结构分析逻辑
            return f"结构分析结果: {parameters}"
        except Exception as e:
            return f"结构分析过程出错: {str(e)}" 