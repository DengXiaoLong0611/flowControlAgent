from abc import ABC, abstractmethod
from typing import List, Dict, Any
from llama_index.core import VectorStoreIndex
from llama_index.llms.openai import OpenAI

class ThoughtFramework(ABC):
    """思维框架基类"""
    
    def __init__(self, index: VectorStoreIndex, llm: OpenAI):
        self.index = index
        self.llm = llm
        self.chat_history: List[Dict[str, str]] = []
    
    @abstractmethod
    async def process_query(self, query: str) -> str:
        """处理用户查询的抽象方法"""
        pass
    
    def add_to_history(self, role: str, content: str):
        """添加对话历史"""
        self.chat_history.append({"role": role, "content": content})
    
    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.chat_history
    
    def clear_history(self):
        """清空对话历史"""
        self.chat_history = [] 