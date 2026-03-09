"""
模型配置
支持阿里云DashScope（通义千问+通义万相）
"""

import os
from typing import Optional

from autogen_core.models import ChatCompletionClient
from autogen_ext.models.openai import OpenAIChatCompletionClient


def create_model_client(
    model: str = "qwen-max",
    api_key: Optional[str] = None,
) -> ChatCompletionClient:
    """
    创建模型客户端
    
    Args:
        model: 模型名称，默认qwen-max
        api_key: API密钥（默认从环境变量读取）
        
    Returns:
        ChatCompletionClient: 模型客户端
    """
    
    # 优先使用传入的api_key，否则从环境变量读取
    if api_key is None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if api_key is None:
        raise ValueError(
            "请提供api_key或设置环境变量DASHSCOPE_API_KEY"
        )
    
    # 阿里云DashScope使用OpenAI兼容接口
    client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    return client


# 阿里云模型配置
DASHSCOPE_MODELS = {
    "qwen-max": {
        "model": "qwen-max",
        "description": "通义千问Max，最强推理能力",
    },
    "qwen-plus": {
        "model": "qwen-plus",
        "description": "通义千问Plus，平衡性能与成本",
    },
    "qwen-turbo": {
        "model": "qwen-turbo",
        "description": "通义千问Turbo，快速响应",
    },
}


def get_model_config(model_name: str) -> dict:
    """获取模型配置"""
    return DASHSCOPE_MODELS.get(model_name, DASHSCOPE_MODELS["qwen-max"])
