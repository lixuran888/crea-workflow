"""
高奢服装框架工作流
基于AutoGen GraphFlow实现完整的四阶段闭环流程
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from autogen_agentchat.teams import DiGraph, RoundRobinGroupChat
from autogen_agentchat.base import ChatAgent, TaskResult, TerminationCondition
from autogen_agentchat.messages import ChatMessage, TextMessage
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core.models import ChatCompletionClient

from ..agents import (
    create_fashion_designer_agent,
    create_prompt_architect_agent,
    create_creative_director_agent,
    create_art_director_agent,
    create_fashion_critic_agent,
    create_refinement_strategist_agent,
    create_generative_executor_agent,
)
from ..tools import generate_images, evaluate_7_dimensions, calculate_ci_score


@dataclass
class WorkflowState:
    """工作流状态"""
    user_input: str = ""
    target_count: int = 3  # 用户选择的m值
    generation_count: int = 5  # 生成的k值
    blueprint: str = ""
    prompts: List[str] = field(default_factory=list)
    selected_prompt: str = ""
    generated_images: List[Dict] = field(default_factory=list)
    evaluations: List[Any] = field(default_factory=list)
    selected_images: List[str] = field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 5
    is_complete: bool = False
    approval_status: Dict[str, bool] = field(default_factory=dict)


class HauteCoutureWorkflow:
    """
    高奢服装创意与设计工作流
    
    四阶段闭环：
    1. 创意策划层：用户输入 → 7n+a生成 → 三方会审
    2. 图像生成层：绘图模型生成k张
    3. 评估筛选层：7维度评分 → 选m张 → CI≥28检查
    4. 自增强层：优化策略 → 迭代更新prompt
    """
    
    def __init__(self, model_client: ChatCompletionClient):
        self.model_client = model_client
        self.state = WorkflowState()
        
        # 创建7个专业Agent
        self.fashion_designer = create_fashion_designer_agent(model_client)
        self.prompt_architect = create_prompt_architect_agent(model_client)
        self.creative_director = create_creative_director_agent(model_client)
        self.art_director = create_art_director_agent(model_client)
        self.fashion_critic = create_fashion_critic_agent(model_client)
        self.refinement_strategist = create_refinement_strategist_agent(model_client)
        self.generative_executor = create_generative_executor_agent(model_client)
    
    async def run(self, user_input: str, target_count: int = 3, generation_count: int = 5) -> Dict[str, Any]:
        """
        运行完整工作流
        
        Args:
            user_input: 用户设计需求
            target_count: 用户选择的输出数量m
            generation_count: AI生成的数量k
            
        Returns:
            工作流结果
        """
        self.state = WorkflowState(
            user_input=user_input,
            target_count=target_count,
            generation_count=generation_count
        )
        
        print("=" * 60)
        print("开始高奢服装设计工作流")
        print("=" * 60)
        print(f"用户需求: {user_input}")
        print(f"目标输出: {target_count}张")
        print(f"生成数量: {generation_count}张")
        print()
        
        # 阶段1：创意策划（循环直到三方通过）
        await self._phase1_creative_planning()
        
        if self.state.is_complete:
            return self._get_result()
        
        # 阶段2-4：生成-评估-优化循环
        while not self.state.is_complete and self.state.iteration_count < self.state.max_iterations:
            print(f"\n{'='*60}")
            print(f"迭代轮次: {self.state.iteration_count + 1}/{self.state.max_iterations}")
            print(f"{'='*60}")
            
            # 阶段2：图像生成
            await self._phase2_image_generation()
            
            # 阶段3：评估筛选
            await self._phase3_evaluation()
            
            if self.state.is_complete:
                break
            
            # 阶段4：自增强优化
            await self._phase4_self_enhancement()
            self.state.iteration_count += 1
        
        return self._get_result()
    
    async def _phase1_creative_planning(self):
        """阶段1：创意策划层 - 三方会审循环"""
        print("\n" + "="*60)
        print("阶段1: 创意策划")
        print("="*60)
        
        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"\n尝试 {attempt + 1}/{max_attempts}")
            
            # 1. 服装设计师提供蓝图
            print("\n[1/6] 服装设计师分析需求...")
            designer_input = f"""用户需求：{self.state.user_input}

请提供：
1. 设计蓝图（廓形、风格、关键元素）
2. 7维度专业约束
3. 关键技术要求"""
            
            designer_response = await self._chat_agent(
                self.fashion_designer,
                designer_input
            )
            self.state.blueprint = designer_response
            print(f"✓ 蓝图已生成")
            
            # 2. 提示框架师7n+a生成
            print("\n[2/6] 提示框架师生成prompt...")
            architect_input = f"""设计蓝图：{self.state.blueprint}

请使用7n+a策略生成prompt：
- 7个维度各生成3个变体
- 加入服装专业知识扩展
- 通过Chain-of-Thought精选最优prompt

输出JSON格式：
{{
  "blueprint_prompts": [...],
  "knowledge_extensions": [...],
  "selected_prompt": "最终prompt"
}}"""
            
            architect_response = await self._chat_agent(
                self.prompt_architect,
                architect_input
            )
            
            # 解析selected_prompt
            self.state.selected_prompt = self._extract_prompt(architect_response)
            print(f"✓ Prompt已生成")
            print(f"  预览: {self.state.selected_prompt[:100]}...")
            
            # 3. 三方会审
            print("\n[3/6] 三方会审...")
            
            # 艺术总监审核
            art_review = await self._chat_agent(
                self.art_director,
                f"请从6项创造力原则审核以下prompt：\n{self.state.selected_prompt}"
            )
            art_passed = "通过" in art_review or "approved" in art_review.lower()
            
            # 服装设计师审核
            fashion_review = await self._chat_agent(
                self.fashion_designer,
                f"请从7维度专业角度审核：\n{self.state.selected_prompt}"
            )
            fashion_passed = "通过" in fashion_review or "approved" in fashion_review.lower()
            
            # 创意总监终审
            director_input = f"""三方审核：
艺术总监：{'通过' if art_passed else '不通过'} - {art_review[:100]}...
服装设计师：{'通过' if fashion_passed else '不通过'} - {fashion_review[:100]}...

请做最终决策。回复"通过"或"不通过"。"""
            
            director_response = await self._chat_agent(
                self.creative_director,
                director_input
            )
            director_passed = "通过" in director_response
            
            self.state.approval_status = {
                "art_director": art_passed,
                "fashion_designer": fashion_passed,
                "creative_director": director_passed
            }
            
            print(f"  艺术总监: {'✓' if art_passed else '✗'}")
            print(f"  服装设计师: {'✓' if fashion_passed else '✗'}")
            print(f"  创意总监: {'✓' if director_passed else '✗'}")
            
            if director_passed:
                print("\n✓ 三方会审通过！进入图像生成阶段")
                return
            else:
                print(f"\n✗ 审核未通过，重新生成...")
        
        # 超过最大尝试次数
        print("\n⚠ 警告：超过最大尝试次数，使用当前prompt继续")
    
    async def _phase2_image_generation(self):
        """阶段2：图像生成层"""
        print("\n" + "="*60)
        print("阶段2: 图像生成")
        print("="*60)
        
        print(f"\n生成 {self.state.generation_count} 张设计图...")
        print(f"Prompt: {self.state.selected_prompt[:150]}...")
        
        # 调用图像生成工具
        try:
            images = generate_images(
                prompt=self.state.selected_prompt,
                n=self.state.generation_count,
                size="1024x1024",
                quality="high"
            )
            
            self.state.generated_images = [
                {"id": img.image_id, "url": img.url, "prompt": img.prompt}
                for img in images
            ]
            
            print(f"✓ 成功生成 {len(images)} 张图像")
            for i, img in enumerate(images, 1):
                print(f"  [{i}] {img.image_id}")
                
        except Exception as e:
            print(f"✗ 图像生成失败: {e}")
            # 使用模拟数据继续
            self.state.generated_images = [
                {"id": f"mock_{i}", "url": f"https://example.com/{i}.png", "prompt": self.state.selected_prompt}
                for i in range(self.state.generation_count)
            ]
            print(f"✓ 使用模拟数据继续")
    
    async def _phase3_evaluation(self):
        """阶段3：评估筛选层"""
        print("\n" + "="*60)
        print("阶段3: 评估筛选")
        print("="*60)
        
        evaluations = []
        
        # 对每张图进行7维度评分
        for i, img in enumerate(self.state.generated_images, 1):
            print(f"\n[{i}/{len(self.state.generated_images)}] 评估 {img['id']}...")
            
            critic_input = f"""请对服装设计图进行7维度专业评分。

图像ID: {img['id']}
生成Prompt: {img['prompt']}

请输出JSON格式评分：
{{
  "scores": {{
    "款式与廓形": {{"raw": 12, "comment": "评价"}},
    "色彩与图案": {{"raw": 16, "comment": "评价"}},
    "面料与肌理": {{"raw": 12, "comment": "评价"}},
    "工艺与结构": {{"raw": 15, "comment": "评价"}},
    "创意与主题": {{"raw": 17, "comment": "评价"}},
    "市场与商业": {{"raw": 15, "comment": "评价"}},
    "整体与系列": {{"raw": 16, "comment": "评价"}}
  }},
  "ci_score": 28.5
}}"""
            
            critic_response = await self._chat_agent(
                self.fashion_critic,
                critic_input
            )
            
            # 解析评分
            evaluation = evaluate_7_dimensions(
                image_id=img['id'],
                prompt=img['prompt'],
                llm_response=critic_response
            )
            
            evaluations.append(evaluation)
            
            print(f"  CI得分: {evaluation.ci_score:.2f}")
            print(f"  低分项: {', '.join(evaluation.low_dimensions) if evaluation.low_dimensions else '无'}")
            print(f"  状态: {'✓ 通过' if evaluation.passed else '✗ 需优化'}")
        
        self.state.evaluations = evaluations
        
        # 创意总监筛选m张最高分
        print(f"\n筛选最高分 {self.state.target_count} 张...")
        sorted_evals = sorted(evaluations, key=lambda x: x.ci_score, reverse=True)
        top_m = sorted_evals[:self.state.target_count]
        
        # 检查是否全部通过
        all_passed = all(e.passed for e in top_m)
        
        if all_passed:
            self.state.selected_images = [e.image_id for e in top_m]
            self.state.is_complete = True
            print(f"\n✓ 全部通过！输出 {len(top_m)} 张设计图")
        else:
            # 有需要优化的
            self.state.selected_images = [e.image_id for e in top_m]
            failed_count = sum(1 for e in top_m if not e.passed)
            print(f"\n✗ {failed_count} 张未达标，进入自增强优化")
    
    async def _phase4_self_enhancement(self):
        """阶段4：自增强层"""
        print("\n" + "="*60)
        print("阶段4: 自增强优化")
        print("="*60)
        
        # 找出CI<28的图像
        low_ci_evals = [e for e in self.state.evaluations if not e.passed]
        
        if not low_ci_evals:
            print("所有图像已达标，无需优化")
            return
        
        # 选择CI最低的进行优化
        worst_eval = min(low_ci_evals, key=lambda x: x.ci_score)
        
        print(f"\n优化目标: {worst_eval.image_id}")
        print(f"当前CI: {worst_eval.ci_score:.2f}")
        print(f"目标CI: 28.0")
        print(f"低分项: {', '.join(worst_eval.low_dimensions)}")
        
        # 计算优化参数
        alpha = (28 - worst_eval.ci_score) / 28
        
        # 简化β计算（实际应该根据用户输入长度）
        gamma = 0.8
        L = len(self.state.user_input)
        L_max = 100
        delta = 0.3
        k = self.state.iteration_count + 1
        beta_k = gamma * (min(L, L_max) / L_max) * (1 / (1 + delta * k))
        
        print(f"\n优化参数:")
        print(f"  α (规则权重): {alpha:.3f}")
        print(f"  β_k (用户权重): {beta_k:.3f}")
        
        # 优化策略师制定策略
        strategist_input = f"""优化分析：
图像: {worst_eval.image_id}
当前CI: {worst_eval.ci_score:.2f}
低分项: {', '.join(worst_eval.low_dimensions)}
α: {alpha:.3f}
β_k: {beta_k:.3f}

请制定优化策略，输出新的prompt方向。"""
        
        strategy_response = await self._chat_agent(
            self.refinement_strategist,
            strategist_input
        )
        
        print(f"\n优化策略: {strategy_response[:200]}...")
        
        # 提示框架师更新prompt
        architect_input = f"""当前prompt: {self.state.selected_prompt}

优化策略: {strategy_response}

低分项: {', '.join(worst_eval.low_dimensions)}

请根据优化策略更新prompt，重点改进低分项。"""
        
        new_prompt_response = await self._chat_agent(
            self.prompt_architect,
            architect_input
        )
        
        # 提取新prompt
        new_prompt = self._extract_prompt(new_prompt_response)
        
        print(f"\n✓ Prompt已更新")
        print(f"  新prompt: {new_prompt[:100]}...")
        
        self.state.selected_prompt = new_prompt
    
    async def _chat_agent(self, agent, message: str) -> str:
        """与Agent对话"""
        try:
            response = await agent.on_messages([
                TextMessage(content=message, source="user")
            ])
            return response.chat_message.content
        except Exception as e:
            print(f"Agent对话出错: {e}")
            return f"[错误: {str(e)}]"
    
    def _extract_prompt(self, response: str) -> str:
        """从响应中提取prompt"""
        # 尝试提取JSON中的selected_prompt
        try:
            json_match = json.loads(response)
            if "selected_prompt" in json_match:
                return json_match["selected_prompt"]
        except:
            pass
        
        # 尝试正则提取
        import re
        patterns = [
            r'"selected_prompt"[:：]\s*"([^"]+)"',
            r'最终prompt[:：]\s*(.+?)(?:\n|$)',
            r'selected_prompt[:：]\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # 返回整个响应作为prompt
        return response[:500]
    
    def _get_result(self) -> Dict[str, Any]:
        """获取工作流结果"""
        return {
            "user_input": self.state.user_input,
            "target_count": self.state.target_count,
            "selected_images": self.state.selected_images,
            "evaluations": [
                {
                    "image_id": e.image_id,
                    "ci_score": e.ci_score,
                    "passed": e.passed,
                    "low_dimensions": e.low_dimensions,
                    "dimensions": [
                        {"name": d.name, "score": d.normalized_score}
                        for d in e.dimensions
                    ]
                }
                for e in self.state.evaluations
            ],
            "iterations": self.state.iteration_count,
            "final_prompt": self.state.selected_prompt,
            "is_complete": self.state.is_complete,
        }


def create_haute_couture_workflow(model_client: ChatCompletionClient) -> HauteCoutureWorkflow:
    """创建工作流实例"""
    return HauteCoutureWorkflow(model_client)
