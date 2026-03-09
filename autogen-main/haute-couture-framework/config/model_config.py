"""
模型配置
支持OpenAI和Azure OpenAI
"""

import os
from typing import Optional

from autogen_core.models import ChatCompletionClient
from autogen_ext.models.openai import OpenAIChatCompletionClient


def create_model_client(
    model: str = "gpt-4",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> ChatCompletionClient:
    """
    创建模型客户端
    
    Args:
        model: 模型名称
        api_key: API密钥（默认从环境变量读取）
        base_url: 自定义base URL（Azure需要）
        
    Returns:
        ChatCompletionClient: 模型客户端
    """
    
    # 优先使用传入的api_key，否则从环境变量读取
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
    
    if api_key is None:
        raise ValueError(
            "请提供api_key或设置环境变量OPENAI_API_KEY/AZURE_OPENAI_KEY"
        )
    
    # 优先使用传入的base_url，否则从环境变量读取
    if base_url is None:
        base_url = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    # 创建客户端
    client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
    )
    
    return client


# 模型配置字典
MODEL_CONFIGS = {
    "gpt-4": {
        "model": "gpt-4",
        "description": "GPT-4，适合复杂推理和创意生成",
    },
    "gpt-4-turbo": {
        "model": "gpt-4-turbo-preview",
        "description": "GPT-4 Turbo，更快更便宜",
    },
    "gpt-3.5-turbo": {
        "model": "gpt-3.5-turbo",
        "description": "GPT-3.5 Turbo，经济实惠",
    },
}


def get_model_config(model_name: str) -> dict:
    """获取模型配置"""
    return MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["gpt-4"])
