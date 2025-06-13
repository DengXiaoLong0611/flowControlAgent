from typing import Dict, Type, List, Any, Optional
from .base import ThoughtFramework
from .plan_execute import PlanAndExecute
from .react import ReAct
import json
import re
from datetime import datetime

class ThoughtFrameworkManager:
    """思维框架管理器"""
    
    def __init__(self):
        self.frameworks: Dict[str, Type[ThoughtFramework]] = {
            "plan_execute": PlanAndExecute,
            "react": ReAct
        }
    
    def get_framework(self, framework_name: str) -> Type[ThoughtFramework]:
        """获取指定的思维框架类"""
        if framework_name not in self.frameworks:
            raise ValueError(f"不支持的思维框架: {framework_name}")
        return self.frameworks[framework_name]
    
    def list_frameworks(self) -> List[str]:
        """列出所有可用的思维框架"""
        return list(self.frameworks.keys())
    
    def get_framework_description(self, framework_name: str) -> str:
        """获取思维框架的描述"""
        descriptions = {
            "plan_execute": "Plan-and-Execute框架：将复杂问题分解为可执行的步骤，逐步解决",
            "react": "ReAct框架：通过思考-行动-观察的循环过程来解决问题"
        }
        return descriptions.get(framework_name, "未知框架")

class ToolManager:
    """工具管理器，用于管理和执行各种工具"""
    
    def __init__(self):
        self.tools = {}
        self.tool_history = []
    
    def register_tool(self, name: str, tool_func: callable, description: str, parameters: Dict[str, str]):
        """注册新工具"""
        self.tools[name] = {
            "function": tool_func,
            "description": description,
            "parameters": parameters
        }
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """执行工具"""
        if tool_name not in self.tools:
            return f"未知工具: {tool_name}"
        
        try:
            tool = self.tools[tool_name]
            result = await tool["function"](**parameters)
            
            # 记录工具执行历史
            self.tool_history.append({
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "parameters": parameters,
                "result": result
            })
            
            return result
        except Exception as e:
            return f"执行工具时出错: {str(e)}"
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        return [
            {
                "name": name,
                "description": info["description"],
                "parameters": info["parameters"]
            }
            for name, info in self.tools.items()
        ]
    
    def get_tool_history(self) -> List[Dict[str, Any]]:
        """获取工具执行历史"""
        return self.tool_history

class StateManager:
    """状态管理器，用于管理思维框架的状态"""
    
    def __init__(self):
        self.state = {}
        self.history = []
    
    def update_state(self, key: str, value: Any):
        """更新状态"""
        self.state[key] = value
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "key": key,
            "value": value
        })
    
    def get_state(self, key: str) -> Any:
        """获取状态"""
        return self.state.get(key)
    
    def get_full_state(self) -> Dict[str, Any]:
        """获取完整状态"""
        return self.state.copy()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取状态历史"""
        return self.history
    
    def clear_state(self):
        """清空状态"""
        self.state = {}
        self.history = []

class PromptManager:
    """提示词管理器，用于管理和生成提示词"""
    
    def __init__(self):
        self.prompts = {}
    
    def register_prompt(self, name: str, template: str):
        """注册提示词模板"""
        self.prompts[name] = template
    
    def generate_prompt(self, name: str, **kwargs) -> str:
        """生成提示词"""
        if name not in self.prompts:
            return f"未知提示词模板: {name}"
        
        try:
            template = self.prompts[name]
            return template.format(**kwargs)
        except Exception as e:
            return f"生成提示词时出错: {str(e)}"
    
    def get_prompt_template(self, name: str) -> Optional[str]:
        """获取提示词模板"""
        return self.prompts.get(name)
    
    def list_prompts(self) -> List[str]:
        """列出所有提示词模板"""
        return list(self.prompts.keys())

class ResultFormatter:
    """结果格式化器，用于格式化输出结果"""
    
    @staticmethod
    def format_thought(thought: str) -> str:
        """格式化思考过程"""
        return f"思考过程：\n{thought}"
    
    @staticmethod
    def format_action(action: Dict[str, Any]) -> str:
        """格式化行动"""
        return f"执行行动：\n工具：{action['tool']}\n参数：{json.dumps(action['parameters'], ensure_ascii=False, indent=2)}"
    
    @staticmethod
    def format_observation(observation: str) -> str:
        """格式化观察结果"""
        return f"观察结果：\n{observation}"
    
    @staticmethod
    def format_final_answer(answer: str) -> str:
        """格式化最终答案"""
        return f"最终答案：\n{answer}"
    
    @staticmethod
    def format_error(error: str) -> str:
        """格式化错误信息"""
        return f"错误：\n{error}"
    
    @staticmethod
    def format_summary(summary: Dict[str, Any]) -> str:
        """格式化总结"""
        return f"""总结：
        主要发现：{summary.get('findings', '无')}
        关键结论：{summary.get('conclusions', '无')}
        建议措施：{summary.get('recommendations', '无')}
        """ 