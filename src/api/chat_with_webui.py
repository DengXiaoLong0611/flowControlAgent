import gradio as gr
import os
import json
from llama_index.core import StorageContext, load_index_from_storage, VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量（强制覆盖）
load_dotenv(override=True)

# 当前脚本根目录下的 pdf 目录
PROJECT_ROOT = os.path.dirname(__file__)
PDF_DIR = os.path.join(PROJECT_ROOT, "train_data", "pdfs")
INDEX_STATS_FILE = os.path.join(PROJECT_ROOT, "..", "..", "data", "index", "index_stats.json")

# 配置OpenAI模型
llm = OpenAI(
    model="gpt-4o", 
    temperature=0.1,  # 降低到0.2，使回答更理性准确
    max_tokens=16000,  # 增加到64000
    context_window=16000
)

# 加载现有索引
def load_engine(index_dir=r"data\index") -> ContextChatEngine:
    storage_context = StorageContext.from_defaults(persist_dir=index_dir)
    index = load_index_from_storage(storage_context)
    return index.as_chat_engine(chat_mode="context", verbose=True, llm=llm)

chat_engine = load_engine()
    
# 问答函数
def query_engine(prompt):
    response = chat_engine.chat(prompt)
    return response.response

# 获取训练时成功加载的PDF文件名（从 index_stats.json）
def get_trained_pdf_list():
    try:
        if not os.path.exists(INDEX_STATS_FILE):
            return []
        with open(INDEX_STATS_FILE, "r", encoding="utf-8") as f:
            stats = json.load(f)
        return stats.get("file_list", [])
    except Exception as e:
        print(f"⚠️ 获取训练文档列表失败: {e}")
        return []

# 上传新PDF后更新索引（保存文件）
def upload_and_update(file_obj):
    try:
        file_path = file_obj.name
        file_name = os.path.basename(file_path)
        save_path = os.path.join(PDF_DIR, file_name)

        os.makedirs(PDF_DIR, exist_ok=True)
        with open(file_path, "rb") as src, open(save_path, "wb") as dst:
            dst.write(src.read())

        return f"✅ 上传成功: {file_name}，请重新训练或重载索引。"
    except Exception as e:
        return f"❌ 上传失败: {str(e)}"

# 刷新文档显示逻辑（仅显示真正训练成功的文档）
def refresh_pdf_list():
    pdf_list = get_trained_pdf_list()
    if pdf_list:
        return "### 📘 当前知识库中已训练的PDF文件：\n\n" + "\n".join([f"- 📄 **{name}**" for name in pdf_list])
    else:
        return "⚠️ 暂无已训练文档。请运行构建脚本进行训练。"

# UI 组件
with gr.Blocks(title="土木工程专家知识问答系统") as demo:
    gr.Markdown("## 🏗️ 土木工程专家知识问答系统")

    with gr.Row():
        with gr.Column():
            question_input = gr.Textbox(lines=3, placeholder="请输入问题", label="提问 / 查询")
            submit_btn = gr.Button("Submit", variant="primary")
            clear_btn = gr.Button("Clear")

        with gr.Column():
            answer_output = gr.Textbox(lines=10, label="专家回答")

    submit_btn.click(fn=query_engine, inputs=question_input, outputs=answer_output)
    clear_btn.click(fn=lambda: "", outputs=answer_output)

    with gr.Accordion("📚 已训练的PDF文档列表", open=False):
        pdf_display = gr.Markdown(refresh_pdf_list)
        refresh_button = gr.Button("🔄 刷新文档列表")
        refresh_button.click(fn=refresh_pdf_list, outputs=pdf_display)

    with gr.Accordion("📤 上传新的PDF知识文档", open=False):
        file_input = gr.File(file_types=[".pdf"], label="上传PDF")
        upload_result = gr.Textbox(label="上传状态")
        file_input.change(fn=upload_and_update, inputs=file_input, outputs=upload_result)

    gr.Markdown("---")
    gr.Markdown("📘 如需使上传的文件立即生效，请运行知识库重构脚本。")

demo.launch()
