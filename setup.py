#安装配置依赖

from setuptools import setup, find_packages

setup(
    name="rag_agent",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "llama-index",
        "python-dotenv",
        "openai"
    ]
) 