"""
高奢品高定服装创意与设计框架 - 主入口
基于AutoGen框架实现
"""

import asyncio
import json
import os
from dotenv import load_dotenv

from config import create_model_client
from workflow import create_haute_couture_workflow


# 加载环境变量
load_dotenv()


async def main():
    """主函数"""
    
    print("=" * 70)
    print("  高奢品高定服装创意与设计框架 (Haute Couture Framework)")
    print("  基于AutoGen多智能体协作")
    print("=" * 70)
    print()
    
    # 创建模型客户端
    try:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            print("✗ 错误: 请设置DASHSCOPE_API_KEY环境变量")
            print("  复制.env.example为.env并填入你的阿里云API密钥")
            return
        
        model_client = create_model_client(
            model="qwen-max",
            api_key=api_key
        )
        print("✓ 模型客户端初始化成功 (通义千问)")
        
    except Exception as e:
        print(f"✗ 模型客户端初始化失败: {e}")
        return
    
    # 创建工作流
    try:
        workflow = create_haute_couture_workflow(model_client)
        print("✓ 工作流初始化成功")
        print(f"  - 7个专业Agent")
        print(f"  - 7维度服装专业评分")
        print(f"  - 自增强优化算法")
    except Exception as e:
        print(f"✗ 工作流初始化失败: {e}")
        return
    
    print()
    
    # 用户输入
    print("请输入您的设计需求（例如：设计一套融合中国传统云纹元素的晚礼服）：")
    user_input = input("> ").strip()
    
    if not user_input:
        user_input = "设计一套融合中国传统云纹元素的晚礼服，要求优雅奢华，适合红毯场合"
        print(f"使用默认需求: {user_input}")
    
    # 用户选择输出数量
    print(f"\n请选择需要生成的设计图数量 m (默认3张):")
    try:
        target_count = int(input("> ").strip())
        if target_count < 1:
            target_count = 3
    except ValueError:
        target_count = 3
        print(f"使用默认值: {target_count}张")
    
    # 用户选择生成数量
    print(f"\n请选择AI生成数量 k (默认5张，需≥m):")
    try:
        generation_count = int(input("> ").strip())
        if generation_count < target_count:
            generation_count = max(target_count + 2, 5)
            print(f"生成数量需≥m，调整为: {generation_count}张")
    except ValueError:
        generation_count = max(target_count + 2, 5)
        print(f"使用默认值: {generation_count}张")
    
    print()
    print("=" * 70)
    print("开始运行工作流...")
    print("=" * 70)
    print()
    
    # 运行工作流
    try:
        result = await workflow.run(
            user_input=user_input,
            target_count=target_count,
            generation_count=generation_count
        )
        
        # 输出结果
        print("\n" + "=" * 70)
        print("工作流完成!")
        print("=" * 70)
        print()
        print(f"最终输出: {len(result['selected_images'])}张设计图")
        print(f"迭代次数: {result['iterations']}")
        print(f"完成状态: {'✓ 成功' if result['is_complete'] else '⚠ 达到最大迭代次数'}")
        print()
        
        print("选中的设计图:")
        for i, img_id in enumerate(result['selected_images'], 1):
            eval_data = next((e for e in result['evaluations'] if e['image_id'] == img_id), None)
            if eval_data:
                print(f"  {i}. {img_id}")
                print(f"     CI得分: {eval_data['ci_score']:.2f}")
                print(f"     7维度: {[f\"{d['name']}:{d['score']:.1f}\" for d in eval_data['dimensions'][:3]]}...")
        
        print()
        print("最终Prompt:")
        print(f"  {result['final_prompt'][:200]}...")
        
        # 保存结果到文件
        output_file = "workflow_result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 详细结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"\n✗ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
