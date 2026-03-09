"""
高奢品高定服装创意与设计框架 - 主入口
基于AutoGen框架实现
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

from config import create_model_client
from workflow import create_haute_couture_workflow


# 加载环境变量
load_dotenv()


@dataclass
class UserPreferences:
    """用户偏好设置"""
    user_input: str = ""  # 设计需求prompt
    selection_mode: str = "ai"  # "user"用户自选 / "ai"AI代选
    target_count: int = 3  # 最终想要几张（AI代选时）
    generation_count: int = 5  # AI生成数量k


def print_banner():
    """打印欢迎界面"""
    print("=" * 70)
    print("  👗 高奢品高定服装创意与设计框架 (Haute Couture Framework)")
    print("  🤖 基于AutoGen多智能体协作")
    print("  🎨 13维度专业评分 | 6美学原则 + 7服装原则")
    print("=" * 70)
    print()


def get_user_input() -> UserPreferences:
    """获取用户输入和偏好设置"""
    
    prefs = UserPreferences()
    
    # 1. 获取设计需求prompt
    print("📝 步骤 1/4: 请输入您的设计需求")
    print("   示例：设计一套融合中国传统云纹元素的晚礼服，优雅奢华，适合红毯")
    print()
    user_input = input("设计需求 > ").strip()
    
    if not user_input:
        user_input = "设计一套融合中国传统云纹元素的晚礼服，优雅奢华，适合红毯场合"
        print(f"   使用默认需求: {user_input}")
    
    prefs.user_input = user_input
    print()
    
    # 2. 选择图片选择模式
    print("🎯 步骤 2/4: 请选择图片选择模式")
    print("   [1] AI代选 - 系统自动选出最佳图片")
    print("   [2] 用户自选 - 生成所有图片，由您在前端选择")
    print()
    
    while True:
        mode_choice = input("请选择 (1/2) > ").strip()
        if mode_choice == "1":
            prefs.selection_mode = "ai"
            print("   ✓ 已选择: AI代选模式")
            break
        elif mode_choice == "2":
            prefs.selection_mode = "user"
            print("   ✓ 已选择: 用户自选模式")
            break
        else:
            print("   ✗ 无效输入，请输入 1 或 2")
    
    print()
    
    # 3. 根据模式询问数量
    if prefs.selection_mode == "ai":
        # AI代选：询问想要几张
        print("🔢 步骤 3/4: AI代选模式 - 请输入您最终想要几张设计图")
        print("   系统会生成多张，然后自动为您选出最佳的几张")
        print()
        
        while True:
            try:
                target = input("想要几张 (默认3张) > ").strip()
                if not target:
                    prefs.target_count = 3
                    prefs.generation_count = 5
                else:
                    prefs.target_count = int(target)
                    if prefs.target_count < 1:
                        print("   ✗ 至少需要1张")
                        continue
                    # 生成数量 = 目标数量 + 2（至少5张）
                    prefs.generation_count = max(prefs.target_count + 2, 5)
                
                print(f"   ✓ 将为您生成 {prefs.generation_count} 张，选出最佳 {prefs.target_count} 张")
                break
            except ValueError:
                print("   ✗ 请输入有效数字")
    
    else:
        # 用户自选：询问生成几张
        print("🔢 步骤 3/4: 用户自选模式 - 请输入需要生成几张设计图")
        print("   所有图片将展示在前端供您选择")
        print()
        
        while True:
            try:
                gen_count = input("生成几张 (默认5张) > ").strip()
                if not gen_count:
                    prefs.generation_count = 5
                else:
                    prefs.generation_count = int(gen_count)
                    if prefs.generation_count < 1:
                        print("   ✗ 至少需要1张")
                        continue
                
                prefs.target_count = prefs.generation_count  # 用户自选时，target=generation
                print(f"   ✓ 将生成 {prefs.generation_count} 张设计图")
                break
            except ValueError:
                print("   ✗ 请输入有效数字")
    
    print()
    
    # 4. 确认信息
    print("📋 步骤 4/4: 请确认您的设置")
    print(f"   设计需求: {prefs.user_input[:50]}...")
    print(f"   选择模式: {'AI代选' if prefs.selection_mode == 'ai' else '用户自选'}")
    print(f"   生成数量: {prefs.generation_count}张")
    if prefs.selection_mode == "ai":
        print(f"   最终输出: {prefs.target_count}张（AI自动选出最佳）")
    print()
    
    confirm = input("确认开始? (y/n) > ").strip().lower()
    if confirm not in ['y', 'yes', '是', '']:
        print("已取消")
        return get_user_input()  # 重新输入
    
    print()
    return prefs


def estimate_time(generation_count: int, max_iterations: int = 5) -> Dict[str, float]:
    """
    估算运行时间
    
    时间构成：
    - 阶段1（创意策划）: 3-5轮Agent对话 ≈ 30-60秒
    - 阶段2（图像生成）: 通义万相每张约10-15秒
    - 阶段3（13维度评分）: 2个Agent评估 ≈ 20-40秒
    - 阶段4（自增强）: 如有迭代，每轮≈ 60-90秒
    """
    
    # 基础时间（秒）
    phase1_time = 45  # 创意策划
    phase2_time_per_image = 12  # 图像生成每张
    phase3_time_per_image = 30  # 13维度评分每张
    phase4_time_per_iteration = 75  # 自增强每轮
    
    # 计算
    base_time = phase1_time  # 阶段1
    base_time += generation_count * phase2_time_per_image  # 阶段2
    base_time += generation_count * phase3_time_per_image  # 阶段3
    
    # 假设平均1.5轮自增强
    avg_iterations = 1.5
    iteration_time = avg_iterations * phase4_time_per_iteration
    
    min_time = base_time  # 无自增强
    max_time = base_time + (max_iterations - 1) * iteration_time  # 最大迭代
    expected_time = base_time + iteration_time  # 预期时间
    
    return {
        "min_minutes": min_time / 60,
        "expected_minutes": expected_time / 60,
        "max_minutes": max_time / 60,
    }


async def run_ai_selection_workflow(prefs: UserPreferences, model_client) -> Dict[str, Any]:
    """运行AI代选模式工作流"""
    
    workflow = create_haute_couture_workflow(model_client)
    
    print("=" * 70)
    print("开始AI代选模式工作流")
    print("=" * 70)
    print(f"📝 设计需求: {prefs.user_input}")
    print(f"🎯 生成 {prefs.generation_count} 张，AI将选出最佳 {prefs.target_count} 张")
    print(f"📊 评分标准: 13维度（6美学+7服装），CI阈值 52/65")
    print()
    
    start_time = time.time()
    
    # 运行完整工作流
    result = await workflow.run(
        user_input=prefs.user_input,
        target_count=prefs.target_count,
        generation_count=prefs.generation_count
    )
    
    elapsed_time = time.time() - start_time
    
    # 输出结果
    print("\n" + "=" * 70)
    print("✅ AI代选工作流完成!")
    print("=" * 70)
    print()
    print(f"⏱️  总耗时: {elapsed_time/60:.1f} 分钟")
    print(f"🖼️  生成总数: {prefs.generation_count}张")
    print(f"⭐ 选出最佳: {len(result['selected_images'])}张")
    print(f"🔄 迭代次数: {result['iterations']}")
    print(f"✅ 完成状态: {'全部达标' if result['is_complete'] else '达到最大迭代次数'}")
    print()
    
    print("🏆 最佳设计图:")
    for i, img_id in enumerate(result['selected_images'], 1):
        eval_data = next((e for e in result['evaluations'] if e['image_id'] == img_id), None)
        if eval_data:
            print(f"   {i}. {img_id}")
            print(f"      CI总分: {eval_data['ci_score']:.2f}/65")
            print(f"      美学6项: {eval_data.get('aesthetic_score', 0):.2f}/30")
            print(f"      服装7项: {eval_data.get('fashion_score', 0):.2f}/35")
            if eval_data.get('low_dimensions'):
                print(f"      低分项: {', '.join(eval_data['low_dimensions'][:3])}")
    
    return result


async def run_user_selection_workflow(prefs: UserPreferences, model_client) -> Dict[str, Any]:
    """运行用户自选模式工作流（只生成，不筛选）"""
    
    workflow = create_haute_couture_workflow(model_client)
    
    print("=" * 70)
    print("开始用户自选模式工作流")
    print("=" * 70)
    print(f"📝 设计需求: {prefs.user_input}")
    print(f"🎯 将生成 {prefs.generation_count} 张设计图供您选择")
    print(f"📊 每张图都会进行13维度评分")
    print()
    
    start_time = time.time()
    
    # 运行工作流，但跳过筛选阶段
    result = await workflow.run_for_user_selection(
        user_input=prefs.user_input,
        generation_count=prefs.generation_count
    )
    
    elapsed_time = time.time() - start_time
    
    # 输出结果
    print("\n" + "=" * 70)
    print("✅ 用户自选模式工作流完成!")
    print("=" * 70)
    print()
    print(f"⏱️  总耗时: {elapsed_time/60:.1f} 分钟")
    print(f"🖼️  已生成: {len(result['generated_images'])}张设计图")
    print()
    
    print("📋 所有设计图及评分:")
    for i, eval_data in enumerate(result['evaluations'], 1):
        print(f"   {i}. {eval_data['image_id']}")
        print(f"      CI总分: {eval_data['ci_score']:.2f}/65")
        print(f"      美学6项: {eval_data.get('aesthetic_score', 0):.2f}/30")
        print(f"      服装7项: {eval_data.get('fashion_score', 0):.2f}/35")
        print(f"      状态: {'✓ 达标' if eval_data['passed'] else '⚠ 未达标'}")
    
    print()
    print("💡 提示: 所有图片已生成，请在前端界面选择您喜欢的图片")
    print("   后端已提供完整的13维度评分数据供参考")
    
    return result


async def main():
    """主函数"""
    
    print_banner()
    
    # 检查API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("✗ 错误: 请设置DASHSCOPE_API_KEY环境变量")
        print("   复制.env.example为.env并填入你的阿里云API密钥")
        print()
        print("申请地址: https://dashscope.aliyun.com/")
        return
    
    # 创建模型客户端
    try:
        model_client = create_model_client(
            model="qwen-max",
            api_key=api_key
        )
        print("✓ 模型客户端初始化成功 (通义千问)")
        print()
    except Exception as e:
        print(f"✗ 模型客户端初始化失败: {e}")
        return
    
    # 获取用户输入
    prefs = get_user_input()
    
    # 估算时间
    time_estimate = estimate_time(prefs.generation_count)
    print()
    print("⏱️  预计运行时间:")
    print(f"   最快: {time_estimate['min_minutes']:.1f} 分钟")
    print(f"   预期: {time_estimate['expected_minutes']:.1f} 分钟")
    print(f"   最慢: {time_estimate['max_minutes']:.1f} 分钟")
    print()
    
    # 运行对应模式
    try:
        if prefs.selection_mode == "ai":
            result = await run_ai_selection_workflow(prefs, model_client)
        else:
            result = await run_user_selection_workflow(prefs, model_client)
        
        # 保存结果
        output_file = f"workflow_result_{prefs.selection_mode}_{int(time.time())}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 详细结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"\n✗ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
