from typing import List, Dict, Any, Tuple
from .base import ThoughtFramework
from llama_index.core import VectorStoreIndex
from llama_index.llms.openai import OpenAI
import json
import re

class PlanAndExecute(ThoughtFramework):
    """Plan-and-Execute 思维框架实现"""
    
    def __init__(self, index: VectorStoreIndex, llm: OpenAI):
        super().__init__(index, llm)
        self.plan_prompt = """作为一个土木工程专家，请将以下问题分解为具体的执行步骤。
        每个步骤应该是具体且可执行的。请以JSON格式输出，格式如下：
        {
            "steps": [
                {
                    "step_id": 1,
                    "description": "步骤描述",
                    "required_tools": ["工具1", "工具2"],
                    "expected_output": "预期输出"
                }
            ]
        }
        
        问题：{query}
        """
        
        self.execution_prompt = """作为土木工程专家，请执行以下步骤：
        步骤描述：{step_description}
        可用工具：{available_tools}
        历史信息：{history}
        
        请提供详细的执行过程和结果。
        """
    
    async def process_query(self, query: str) -> str:
        """处理用户查询的主方法"""
        try:
            # 1. 规划阶段
            plan = await self._create_plan(query)
            if not plan:
                return "无法创建执行计划"
            
            # 2. 执行阶段
            results = []
            for step in plan["steps"]:
                step_result = await self._execute_step(step)
                results.append(step_result)
                self.add_to_history("assistant", f"步骤 {step['step_id']} 完成: {step_result}")
            
            # 3. 整合结果
            final_result = await self._synthesize_results(results)
            return final_result
            
        except Exception as e:
            return f"处理过程中出错: {str(e)}"
    
    async def _create_plan(self, query: str) -> Dict[str, Any]:
        """创建执行计划"""
        try:
            # 使用LLM生成计划
            response = await self.llm.complete(
                self.plan_prompt.format(query=query)
            )
            
            # 解析JSON响应
            plan_text = response.text
            plan_json = json.loads(plan_text)
            return plan_json
            
        except Exception as e:
            print(f"创建计划时出错: {str(e)}")
            return None
    
    async def _execute_step(self, step: Dict[str, Any]) -> str:
        """执行单个步骤"""
        try:
            # 准备执行提示
            available_tools = ", ".join(step["required_tools"])
            history = "\n".join([f"{h['role']}: {h['content']}" for h in self.chat_history[-3:]])
            
            # 执行步骤
            response = await self.llm.complete(
                self.execution_prompt.format(
                    step_description=step["description"],
                    available_tools=available_tools,
                    history=history
                )
            )
            
            return response.text
            
        except Exception as e:
            return f"执行步骤时出错: {str(e)}"
    
    async def _synthesize_results(self, results: List[str]) -> str:
        """整合所有步骤的结果"""
        try:
            synthesis_prompt = f"""作为土木工程专家，请整合以下步骤的执行结果，提供一个完整的解决方案：
            
            步骤结果：
            {json.dumps(results, ensure_ascii=False, indent=2)}
            
            请提供一个结构化的总结，包括：
            1. 主要发现
            2. 关键结论
            3. 建议措施
            """
            
            response = await self.llm.complete(synthesis_prompt)
            return response.text
            
        except Exception as e:
            return f"整合结果时出错: {str(e)}" 