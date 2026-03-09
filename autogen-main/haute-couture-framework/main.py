"""
高奢品高定服装创意与设计框架 - 主入口
基于AutoGen框架实现
"""

import asyncio
import os
from dotenv import load_dotenv

from autogen_core.models import ChatCompletionClient
from autogen_ext.models.openai import OpenAIChatCompletionClient

from workflow import create_haute_couture_workflow


# 加载环境变量
load_dotenv()


def create_model_client() -> ChatCompletionClient:
    """创建模型客户端"""
    
    # OpenAI配置
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return OpenAIChatCompletionClient(
            model="gpt-4",
            api_key=api_key,
        )
    
    # Azure OpenAI配置
    azure_key = os.getenv("AZURE_OPENAI_KEY")
    if azure_key:
        return OpenAIChatCompletionClient(
            model="gpt-4",
            api_key=azure_key,
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
    
    raise ValueError("请配置OPENAI_API_KEY或AZURE_OPENAI_KEY")


async def main():
    """主函数"""
    
    print("=" * 60)
    print("高奢品高定服装创意与设计框架 (Haute Couture Framework)")
    print("基于AutoGen多智能体协作")
    print("=" * 60)
    
    # 创建模型客户端
    try:
        model_client = create_model_client()
        print("✓ 模型客户端初始化成功")
    except ValueError as e:
        print(f"✗ 错误: {e}")
        print("请复制.env.example为.env并配置API密钥")
        return
    
    # 创建工作流
    workflow = create_haute_couture_workflow(model_client)
    print("✓ 工作流初始化成功")
    print()
    
    # 用户输入
    print("请输入您的设计需求（例如：设计一套融合中国传统云纹元素的晚礼服）：")
    user_input = input("> ").strip()
    
    if not user_input:
        user_input = "设计一套融合中国传统云纹元素的晚礼服，要求优雅奢华，适合红毯场合"
        print(f"使用默认需求：{user_input}")
    
    # 用户选择输出数量
    print(f"\n请选择需要生成的设计图数量（默认3张）：")
    try:
        target_count = int(input("> ").strip())
    except ValueError:
        target_count = 3
        print(f"使用默认值：{target_count}张")
    
    print()
    print("=" * 60)
    print("开始运行工作流...")
    print("=" * 60)
    print()
    
    # 运行工作流
    try:
        result = await workflow.run(user_input, target_count)
        
        print()
        print("=" * 60)
        print("工作流完成！")
        print("=" * 60)
        print()
        print(f"最终输出：{len(result['selected_images'])}张设计图")
        print(f"迭代次数：{result['iterations']}")
        print()
        print("选中的设计图：")
        for i, img in enumerate(result['selected_images'], 1):
            print(f"  {i}. {img}")
        print()
        print("评分详情：")
        for eval_data in result['evaluations']:
            print(f"  {eval_data['image']}: CI={eval_data['CI']}")
        
    except Exception as e:
        print(f"\n✗ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
