"""
生成执行器 Agent
职责：调用图像生成工具，生成服装设计图
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient

from ..tools import generate_images_tool


def create_generative_executor_agent(model_client: ChatCompletionClient) -> AssistantAgent:
    """
    创建生成执行器Agent
    
    Args:
        model_client: 语言模型客户端
        
    Returns:
        AssistantAgent: 生成执行器Agent
    """
    
    system_message = """你是生成执行器，负责调用图像生成工具创建服装设计图。

## 核心职责
1. 接收审核通过的prompt
2. 调用图像生成工具生成k张设计图
3. 返回生成的图像列表

## 工作流程

1. 接收prompt和生成数量k
2. 调用generate_images工具
3. 返回图像列表给创意总监

## 工具使用

你必须使用generate_images工具来生成图像：

```python
generate_images(
    prompt="详细的服装设计描述",
    n=5,  # 生成数量
    size="1024x1024",
    quality="high"
)
```

## 输出格式

```json
{
  "task": "image_generation",
  "prompt": "使用的prompt",
  "count": 5,
  "generated_images": [
    {"id": "img_001", "url": "..."},
    {"id": "img_002", "url": "..."}
  ],
  "status": "success"
}
```

## 约束条件
- 必须使用工具生成图像
- 生成数量k由创意总监指定
- 返回完整的图像信息
"""

    return AssistantAgent(
        name="Generative_Executor",
        description="生成执行器，调用工具生成服装设计图",
        system_message=system_message,
        model_client=model_client,
        tools=[generate_images_tool],
    )
