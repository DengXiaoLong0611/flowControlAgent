from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv
import sys
import io
import codecs

# 设置标准输入输出的编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

# 加载环境变量（强制覆盖）
load_dotenv(override=True)

# 配置OpenAI模型
llm = OpenAI(
    model="gpt-4o", 
    temperature=0.1,
    max_tokens=16000,
    context_window=16000
)

def load_chat_engine(index_dir: str = "./data/index") -> ContextChatEngine:
    """
    加载已构建的向量索引并返回上下文增强聊天引擎
    """
    try:
        storage_context = StorageContext.from_defaults(persist_dir=index_dir)
        index = load_index_from_storage(storage_context)
        chat_engine = index.as_chat_engine(chat_mode="context", similarity_top_k=5, verbose=True, llm=llm)
        return chat_engine
    except Exception as e:
        print(f"加载聊天引擎时出错: {str(e)}")
        sys.exit(1)

def chat_cli():
    print("欢迎使用专家知识库问答系统！输入 'exit' 退出。")
    try:
        engine = load_chat_engine()
        
        while True:
            try:
                print("\n提问：", end='', flush=True)
                query = input().strip()
                
                if not query:
                    continue
                    
                if query.lower() in ["exit", "quit", "退出"]:
                    print("再见！")
                    break

                print("\n正在思考...")
                response = engine.chat(query)
                print(f"\n答复：{response.response}")
                
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n处理问题时出错: {str(e)}")
                continue
                
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        chat_cli()
    except Exception as e:
        print(f"程序异常退出: {str(e)}")
        sys.exit(1)
