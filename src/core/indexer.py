'''
功能说明：
1. 批量读取和处理PDF文档
2. 支持文档元数据提取
3. 包含错误处理机制
4. 记录文档分块信息
5. 过滤无效文档
6. 支持索引持久化
7. 支持增量训练
8. 支持自定义训练数据路径
'''

import os
from typing import List, Tuple
from llama_index.core import SimpleDirectoryReader, Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage import StorageContext
import logging
from collections import defaultdict
from llama_index.core import load_index_from_storage
import json
from dotenv import load_dotenv
from llama_index.core.settings import Settings
from llama_index.llms.openai import OpenAI
import re

# 加载环境变量
load_dotenv()

# 配置日志，只记录ERROR级别以上的信息
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('document_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置全局设置
Settings.llm = OpenAI(
    model="gpt-4o",
    temperature=0.1,  # 降低temperature使回答更准确
    max_tokens=16000,  # 增加最大token数
    context_window=16000  # 增加上下文窗口
)
Settings.chunk_size = 2000  # 增加chunk大小
Settings.chunk_overlap = 400  # 增加重叠

def clean_text(text: str) -> str:
    """
    清理文本中的特殊字符
    :param text: 输入文本
    :return: 清理后的文本
    """
    try:
        # 首先尝试编码解码来移除代理字符
        text = text.encode('utf-8', 'ignore').decode('utf-8')
        
        # 移除Unicode代理对字符
        text = re.sub(r'[\ud800-\udfff]', '', text)
        
        # 移除其他可能导致问题的特殊字符
        text = re.sub(r'[^\x00-\x7F\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', '', text)
        
        # 移除控制字符
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # 移除零宽字符
        text = re.sub(r'[\u200b-\u200d\u200e\u200f\u202a-\u202e\u2060-\u2064\u206a-\u206f]', '', text)
        
        # 移除其他可能导致问题的Unicode字符
        text = re.sub(r'[\ufeff\ufffe]', '', text)
        
        return text
    except Exception as e:
        logger.error(f"清理文本时出错: {str(e)}")
        return ""

def is_valid_document(doc: Document) -> bool:
    """
    验证文档是否有效
    :param doc: 文档对象
    :return: 是否有效
    """
    try:
        # 检查文档是否有内容
        if not doc.text or len(doc.text.strip()) == 0:
            return False
        # 检查文档是否有文件名
        if not doc.metadata.get('file_name'):
            return False
        return True
    except Exception as e:
        logger.error(f"验证文档时出错: {str(e)}")
        return False

def load_and_process_documents(input_dir: str, file_extns: List[str] = None) -> Tuple[List[Document], dict]:
    """
    加载指定目录下的文档并进行处理
    :param input_dir: 输入目录路径
    :param file_extns: 文件扩展名列表，例如 ['.pdf', '.txt']
    :return: (文档列表, 处理统计信息)
    """
    try:
        if not os.path.exists(input_dir):
            raise ValueError(f"目录不存在: {input_dir}")

        reader_kwargs = {
            "input_dir": input_dir,
            "recursive": True,
            "filename_as_id": True,
            "errors": "ignore",
            "num_files_limit": None,
            "required_exts": file_extns if file_extns else ['.pdf']
        }

        # 加载文档
        reader = SimpleDirectoryReader(**reader_kwargs)
        all_documents = reader.load_data()
        
        # 清理文档内容并创建新文档
        cleaned_documents = []
        for doc in all_documents:
            try:
                cleaned_text = clean_text(doc.text)
                # 创建新的Document对象而不是修改现有对象
                new_doc = Document(
                    text=cleaned_text,
                    metadata=doc.metadata
                )
                cleaned_documents.append(new_doc)
            except Exception as e:
                logger.error(f"清理文档内容时出错 {doc.metadata.get('file_name', '未知')}: {str(e)}")
                continue
        
        # 过滤掉无效文档
        documents = [doc for doc in cleaned_documents if is_valid_document(doc)]
        
        if not documents:
            logger.error("没有找到有效的文档")
            return [], defaultdict(int)
            
        # 创建文档分块器
        splitter = SentenceSplitter(
            chunk_size=2000,
            chunk_overlap=400,
            separator="\n"
        )
        
        # 处理统计信息
        stats = defaultdict(int)
        stats['total_documents'] = len(documents)
        stats['invalid_documents'] = len(all_documents) - len(documents)
        stats['unique_files'] = len(set(doc.metadata.get('file_name', '') for doc in documents))
        stats['file_list'] = sorted(list(set(doc.metadata.get('file_name', '') for doc in documents)))
        
        # 处理每个文档
        all_chunks = []
        for doc in documents:
            try:
                # 分块处理
                chunks = splitter.split_text(doc.text)
                all_chunks.extend(chunks)
                stats['total_chars'] += len(doc.text)
            except Exception as e:
                logger.error(f"处理文档时出错 {doc.metadata.get('file_name', '未知')}: {str(e)}")
                continue
        
        if all_chunks:
            stats['total_chunks'] = len(all_chunks)
            stats['avg_chunk_size'] = stats['total_chars'] / len(all_chunks)
            stats['min_chunk_size'] = min(len(chunk) for chunk in all_chunks)
            stats['max_chunk_size'] = max(len(chunk) for chunk in all_chunks)
        
        return documents, stats

    except Exception as e:
        logger.error(f"加载文档时出错: {str(e)}")
        return [], defaultdict(int)

def display_summary(stats: dict) -> None:
    """
    显示文档处理摘要
    :param stats: 处理统计信息
    """
    print("\n=== 文档处理摘要 ===")
    print(f"成功读取的PDF文件数: {stats['unique_files']}")
    if stats['invalid_documents'] > 0:
        print(f"无效文档数: {stats['invalid_documents']}")
    print(f"总chunks数: {stats['total_chunks']}")
    print(f"chunks大小统计:")
    print(f"  - 平均: {stats['avg_chunk_size']:.2f} 字符")
    print(f"  - 最小: {stats['min_chunk_size']} 字符")
    print(f"  - 最大: {stats['max_chunk_size']} 字符")
    
    print("\n=== PDF文件列表 ===")
    for i, filename in enumerate(stats['file_list'], 1):
        print(f"{i}. {filename}")

def create_and_save_index(documents: List[Document], save_dir: str = "index_storage", incremental: bool = False) -> VectorStoreIndex:
    """
    创建索引并保存到本地，支持增量训练
    :param documents: 文档列表
    :param save_dir: 索引保存目录
    :param incremental: 是否为增量训练
    :return: 创建的索引
    """
    try:
        # 配置索引创建参数
        index_kwargs = {
            "documents": documents,
            "show_progress": True
        }

        if incremental and os.path.exists(save_dir):
            # 加载现有索引
            storage_context = StorageContext.from_defaults(persist_dir=save_dir)
            index = load_index_from_storage(storage_context)
            # 添加新文档
            for doc in documents:
                try:
                    index.insert(doc)
                except Exception as e:
                    if "surrogate" in str(e).lower():
                        logger.warning(f"跳过包含无效Unicode字符的文档: {doc.metadata.get('file_name', '未知')}")
                        continue
                    else:
                        raise
        else:
            # 创建新索引
            try:
                index = VectorStoreIndex.from_documents(**index_kwargs)
            except Exception as e:
                if "surrogate" in str(e).lower():
                    logger.warning("创建索引时遇到无效Unicode字符，尝试逐个添加文档...")
                    # 如果批量创建失败，尝试逐个添加文档
                    index = VectorStoreIndex([])
                    for doc in documents:
                        try:
                            index.insert(doc)
                        except Exception as doc_e:
                            if "surrogate" in str(doc_e).lower():
                                logger.warning(f"跳过包含无效Unicode字符的文档: {doc.metadata.get('file_name', '未知')}")
                                continue
                            else:
                                raise
        
        # 确保保存目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 持久化保存索引
        try:
            index.storage_context.persist(persist_dir=save_dir)
            logger.info(f"索引已成功保存到: {save_dir}")
        except Exception as e:
            if "surrogate" in str(e).lower():
                logger.warning("保存索引时遇到无效Unicode字符，但索引已创建成功")
            else:
                raise
            
        return index
    except Exception as e:
        logger.error(f"保存索引时出错: {str(e)}")
        raise

def update_stats(old_stats: dict, new_stats: dict) -> dict:
    """
    更新统计信息，合并新旧统计
    :param old_stats: 原有统计信息
    :param new_stats: 新统计信息
    :return: 合并后的统计信息
    """
    if not old_stats:
        return new_stats
        
    merged_stats = old_stats.copy()
    
    # 更新文档数量
    merged_stats['total_documents'] += new_stats['total_documents']
    merged_stats['invalid_documents'] += new_stats['invalid_documents']
    
    # 更新文件列表
    merged_stats['file_list'] = sorted(list(set(merged_stats['file_list'] + new_stats['file_list'])))
    merged_stats['unique_files'] = len(merged_stats['file_list'])
    
    # 更新chunks信息
    merged_stats['total_chunks'] += new_stats['total_chunks']
    merged_stats['total_chars'] += new_stats['total_chars']
    
    # 更新chunks大小统计
    if merged_stats['total_chunks'] > 0:
        merged_stats['avg_chunk_size'] = merged_stats['total_chars'] / merged_stats['total_chunks']
        merged_stats['min_chunk_size'] = min(merged_stats.get('min_chunk_size', float('inf')), 
                                           new_stats['min_chunk_size'])
        merged_stats['max_chunk_size'] = max(merged_stats.get('max_chunk_size', 0), 
                                           new_stats['max_chunk_size'])
    
    return merged_stats

def load_saved_index(save_dir: str = "index_storage") -> VectorStoreIndex:
    """
    从本地加载保存的索引
    :param save_dir: 索引保存目录
    :return: 加载的索引
    """
    try:
        if not os.path.exists(save_dir):
            raise ValueError(f"索引目录不存在: {save_dir}")
            
        # 使用新的加载方法加载存储的索引
        storage_context = StorageContext.from_defaults(persist_dir=save_dir)
        # 假设新的加载方法是通过 `load_index_from_storage`
        index = load_index_from_storage(storage_context)

        
        logger.info(f"索引已成功从 {save_dir} 加载")
        return index
    except Exception as e:
        logger.error(f"加载索引时出错: {str(e)}")
        raise

def get_training_data_path() -> str:
    """
    获取训练数据路径
    优先使用环境变量中的路径，如果没有则使用默认路径
    """
    # 确保加载.env文件
    load_dotenv(override=True)
    
    # 从环境变量获取训练数据路径
    train_data_path = os.getenv('TRAIN_DATA_PATH')
    
    if not train_data_path:
        # 如果环境变量中没有设置，使用默认路径
        train_data_path = "./train_data/pdfs"
        logger.warning(f"未设置TRAIN_DATA_PATH环境变量，使用默认路径: {train_data_path}")
    else:
        logger.info(f"使用环境变量中的训练数据路径: {train_data_path}")
    
    # 确保路径存在
    if not os.path.exists(train_data_path):
        raise ValueError(f"训练数据目录不存在: {train_data_path}")
        
    return train_data_path

def main():
    """
    主函数
    """
    try:
        # 获取训练数据路径
        input_directory = get_training_data_path()
        file_extensions = ['.pdf']
        index_save_dir = "index_storage"
        
        print(f"使用训练数据目录: {input_directory}")
        
        # 检查是否为增量训练
        incremental = os.path.exists(index_save_dir)
        if incremental:
            print("检测到现有索引，将进行增量训练...")
            # 加载现有统计信息
            stats_path = os.path.join(index_save_dir, "index_stats.json")
            if os.path.exists(stats_path):
                with open(stats_path, "r", encoding="utf-8") as f:
                    old_stats = json.load(f)
            else:
                old_stats = {}
        else:
            old_stats = {}
            print("未检测到现有索引，将创建新索引...")

        print(f"开始从 {input_directory} 加载文档...")
        documents, new_stats = load_and_process_documents(input_directory, file_extensions)
        
        if documents:
            print("\n开始创建和保存索引...")
            index = create_and_save_index(documents, index_save_dir, incremental=incremental)
            print(f"索引已保存到: {index_save_dir}")
            
            # 更新统计信息
            merged_stats = update_stats(old_stats, new_stats)
            display_summary(merged_stats)
            
            # 保存更新后的统计信息
            stats_path = os.path.join(index_save_dir, "index_stats.json")
            with open(stats_path, "w", encoding="utf-8") as f:
                json.dump(merged_stats, f, ensure_ascii=False, indent=2)
            
            print("\n测试加载保存的索引...")
            loaded_index = load_saved_index(index_save_dir)
            print("索引加载成功！")
    except Exception as e:
        logger.error(f"训练过程出错: {str(e)}")
        raise

if __name__ == "__main__":
    main()




