"""
高奢服装框架工作流
基于AutoGen GraphFlow实现四阶段闭环流程
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from autogen_agentchat.teams import DiGraph
from autogen_agentchat.base import ChatAgent, TaskResult
from autogen_agentchat.messages import ChatMessage, TextMessage
from autogen_core.models import ChatCompletionClient

from ..agents import (
    create_fashion_designer_agent,
    create_prompt_architect_agent,
    create_creative_director_agent,
    create_art_director_agent,
    create_fashion_critic_agent,
    create_refinement_strategist_agent,
)


@dataclass
class WorkflowState:
    """工作流状态"""
    user_input: str = ""
    target_count: int = 3  # 用户选择的m值
    blueprint: str = ""
    prompts: List[str] = field(default_factory=list)
    selected_prompt: str = ""
    generated_images: List[str] = field(default_factory=list)
    evaluations: List[Dict] = field(default_factory=list)
    selected_images: List[str] = field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 5
    is_complete: bool = False


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
        
        # 创建6个专业Agent
        self.fashion_designer = create_fashion_designer_agent(model_client)
        self.prompt_architect = create_prompt_architect_agent(model_client)
        self.creative_director = create_creative_director_agent(model_client)
        self.art_director = create_art_director_agent(model_client)
        self.fashion_critic = create_fashion_critic_agent(model_client)
        self.refinement_strategist = create_refinement_strategist_agent(model_client)
        
        # 构建GraphFlow
        self.workflow_graph = self._build_workflow_graph()
    
    def _build_workflow_graph(self) -> DiGraph:
        """构建工作流有向图"""
        
        # 定义节点（Agent）
        nodes = {
            "fashion_designer": self.fashion_designer,
            "prompt_architect": self.prompt_architect,
            "creative_director": self.creative_director,
            "art_director": self.art_director,
            "fashion_critic": self.fashion_critic,
            "refinement_strategist": self.refinement_strategist,
        }
        
        # 定义边（流转关系）
        edges = [
            # 阶段1：创意策划
            ("fashion_designer", "prompt_architect"),  # 设计师提供约束
            ("prompt_architect", "creative_director"),  # 生成prompt提交审核
            ("creative_director", "art_director"),  # 艺术总监审核
            ("art_director", "creative_director"),  # 返回审核结果
            ("creative_director", "fashion_designer"),  # 设计师审核
            ("fashion_designer", "creative_director"),  # 返回审核结果
            
            # 阶段2：图像生成（外部调用，这里用creative_director代表）
            ("creative_director", "fashion_critic"),  # 生成k张后送评
            
            # 阶段3：评估筛选
            ("fashion_critic", "creative_director"),  # 返回评分结果
            
            # 阶段4：自增强（如果需要）
            ("creative_director", "refinement_strategist"),  # 需要优化
            ("refinement_strategist", "prompt_architect"),  # 优化策略更新prompt
        ]
        
        # 创建有向图
        graph = DiGraph(nodes=nodes, edges=edges)
        
        return graph
    
    async def run(self, user_input: str, target_count: int = 3) -> Dict[str, Any]:
        """
        运行工作流
        
        Args:
            user_input: 用户设计需求
            target_count: 用户选择的输出数量m
            
        Returns:
            工作流结果
        """
        self.state = WorkflowState(
            user_input=user_input,
            target_count=target_count
        )
        
        # 阶段1：创意策划
        await self._phase1_creative_planning()
        
        # 阶段2：图像生成（模拟）
        await self._phase2_image_generation()
        
        # 阶段3&4：评估与自增强循环
        while not self.state.is_complete and self.state.iteration_count < self.state.max_iterations:
            await self._phase3_evaluation()
            
            if self.state.is_complete:
                break
                
            await self._phase4_self_enhancement()
            self.state.iteration_count += 1
        
        return {
            "selected_images": self.state.selected_images,
            "evaluations": self.state.evaluations,
            "iterations": self.state.iteration_count,
            "final_prompt": self.state.selected_prompt,
        }
    
    async def _phase1_creative_planning(self):
        """阶段1：创意策划层"""
        
        # 1. 服装设计师分析需求，提供蓝图
        designer_input = f"""用户需求：{self.state.user_input}
目标数量：{self.state.target_count}张

请提供：
1. 设计蓝图
2. 专业约束（7维度要求）
3. 关键技术约束"""
        
        designer_response = await self.fashion_designer.on_messages([
            TextMessage(content=designer_input, source="user")
        ])
        
        self.state.blueprint = designer_response.chat_message.content
        
        # 2. 提示框架师7n+a生成
        architect_input = f"""设计蓝图：{self.state.blueprint}

请使用7n+a策略：
1. 7个维度各生成3个变体
2. 加入服装专业知识扩展
3. 通过Chain-of-Thought精选最优prompt"""
        
        architect_response = await self.prompt_architect.on_messages([
            TextMessage(content=architect_input, source="fashion_designer")
        ])
        
        self.state.selected_prompt = architect_response.chat_message.content
        
        # 3. 三方会审
        # 艺术总监审核
        art_review = await self.art_director.on_messages([
            TextMessage(content=f"请审核以下prompt方案：\n{self.state.selected_prompt}", source="prompt_architect")
        ])
        
        # 服装设计师审核
        fashion_review = await self.fashion_designer.on_messages([
            TextMessage(content=f"请从专业角度审核：\n{self.state.selected_prompt}", source="prompt_architect")
        ])
        
        # 创意总监终审
        director_input = f"""三方审核结果：
艺术总监：{art_review.chat_message.content}
服装设计师：{fashion_review.chat_message.content}

请做最终决策：通过/不通过"""
        
        director_response = await self.creative_director.on_messages([
            TextMessage(content=director_input, source="reviewers")
        ])
        
        # 如果不通过，需要重新生成（简化处理）
        if "不通过" in director_response.chat_message.content:
            # 实际应该返回提示框架师重新生成
            pass
    
    async def _phase2_image_generation(self):
        """阶段2：图像生成层（模拟）"""
        # 实际应该调用绘图模型生成k张
        # 这里模拟生成5张
        k = 5
        self.state.generated_images = [f"generated_image_{i}.png" for i in range(1, k+1)]
    
    async def _phase3_evaluation(self):
        """阶段3：评估筛选层"""
        
        # 艺术评论家+服装设计师进行7维度评分
        evaluations = []
        for img in self.state.generated_images:
            critic_input = f"""请对图像 {img} 进行7维度专业评分：

Prompt：{self.state.selected_prompt}

请输出JSON格式评分结果。"""
            
            critic_response = await self.fashion_critic.on_messages([
                TextMessage(content=critic_input, source="creative_director")
            ])
            
            # 解析评分（简化处理）
            evaluations.append({
                "image": img,
                "evaluation": critic_response.chat_message.content,
                "CI": 28.5,  # 模拟值
            })
        
        self.state.evaluations = evaluations
        
        # 创意总监筛选m张最高分
        sorted_evals = sorted(evaluations, key=lambda x: x["CI"], reverse=True)
        top_m = sorted_evals[:self.state.target_count]
        
        # 检查每张CI≥28
        all_passed = all(e["CI"] >= 28 for e in top_m)
        
        if all_passed:
            self.state.selected_images = [e["image"] for e in top_m]
            self.state.is_complete = True
        else:
            # 有需要优化的图像
            self.state.selected_images = [e["image"] for e in top_m]
    
    async def _phase4_self_enhancement(self):
        """阶段4：自增强层"""
        
        # 找出CI<28的图像
        low_ci_images = [e for e in self.state.evaluations if e["CI"] < 28]
        
        for low_img in low_ci_images:
            # 优化策略师分析
            strategist_input = f"""图像：{low_img['image']}
当前CI：{low_img['CI']}
目标CI：28
迭代轮次：{self.state.iteration_count + 1}

请：
1. 计算α和βₖ
2. 分析低分项
3. 制定优化策略
4. 输出新的prompt方向"""
            
            strategist_response = await self.refinement_strategist.on_messages([
                TextMessage(content=strategist_input, source="creative_director")
            ])
            
            # 提示框架师更新prompt
            architect_input = f"""优化策略：{strategist_response.chat_message.content}

请根据优化策略更新prompt。"""
            
            architect_response = await self.prompt_architect.on_messages([
                TextMessage(content=architect_input, source="refinement_strategist")
            ])
            
            self.state.selected_prompt = architect_response.chat_message.content


def create_haute_couture_workflow(model_client: ChatCompletionClient) -> HauteCoutureWorkflow:
    """创建工作流实例"""
    return HauteCoutureWorkflow(model_client)
