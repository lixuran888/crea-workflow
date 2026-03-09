"""
评分计算工具
7维度服装专业评分
"""

import json
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

from autogen_agentchat.tools import FunctionTool


@dataclass
class DimensionScore:
    """维度评分"""
    name: str
    raw_score: float  # 原始分（满分15-20）
    max_score: float  # 该维度满分
    normalized_score: float  # 标准化5分制
    comment: str


@dataclass
class EvaluationResult:
    """评估结果"""
    image_id: str
    dimensions: List[DimensionScore]
    ci_score: float  # 综合创新指数
    passed: bool  # 是否通过（CI>=28）
    low_dimensions: List[str]  # 低分项（<4分）


# 7维度配置
DIMENSION_CONFIG = {
    "款式与廓形": {"max_raw": 15, "weight": 1.0},
    "色彩与图案": {"max_raw": 20, "weight": 1.0},
    "面料与肌理": {"max_raw": 15, "weight": 1.0},
    "工艺与结构": {"max_raw": 20, "weight": 1.0},
    "创意与主题": {"max_raw": 20, "weight": 1.0},
    "市场与商业": {"max_raw": 20, "weight": 1.0},
    "整体与系列": {"max_raw": 20, "weight": 1.0},
}


def evaluate_7_dimensions(
    image_id: str,
    prompt: str,
    llm_response: str,
) -> EvaluationResult:
    """
    解析LLM的7维度评分响应
    
    Args:
        image_id: 图像ID
        prompt: 生成prompt
        llm_response: LLM的评分响应文本
        
    Returns:
        EvaluationResult: 评估结果
    """
    
    dimensions = []
    
    # 尝试解析JSON格式
    try:
        json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            dimensions = _parse_json_scores(data)
    except:
        pass
    
    # 如果JSON解析失败，尝试文本解析
    if not dimensions:
        dimensions = _parse_text_scores(llm_response)
    
    # 如果都失败，使用默认值
    if not dimensions:
        dimensions = _get_default_scores()
    
    # 计算CI
    ci_score = sum(d.normalized_score for d in dimensions)
    
    # 找出低分项（<4分）
    low_dimensions = [d.name for d in dimensions if d.normalized_score < 4.0]
    
    # 判断是否通过
    passed = ci_score >= 28.0 and all(d.normalized_score >= 4.0 for d in dimensions)
    
    return EvaluationResult(
        image_id=image_id,
        dimensions=dimensions,
        ci_score=ci_score,
        passed=passed,
        low_dimensions=low_dimensions,
    )


def _parse_json_scores(data: dict) -> List[DimensionScore]:
    """解析JSON格式的评分"""
    dimensions = []
    
    dim_mapping = {
        "款式与廓形": "款式与廓形",
        "silhouette": "款式与廓形",
        "色彩与图案": "色彩与图案",
        "color": "色彩与图案",
        "面料与肌理": "面料与肌理",
        "fabric": "面料与肌理",
        "工艺与结构": "工艺与结构",
        "craftsmanship": "工艺与结构",
        "创意与主题": "创意与主题",
        "creativity": "创意与主题",
        "市场与商业": "市场与商业",
        "market": "市场与商业",
        "整体与系列": "整体与系列",
        "overall": "整体与系列",
    }
    
    for key, value in data.get("scores", {}).items():
        dim_name = dim_mapping.get(key, key)
        if dim_name in DIMENSION_CONFIG:
            config = DIMENSION_CONFIG[dim_name]
            raw = float(value.get("raw", 0))
            normalized = (raw / config["max_raw"]) * 5
            
            dimensions.append(DimensionScore(
                name=dim_name,
                raw_score=raw,
                max_score=config["max_raw"],
                normalized_score=min(normalized, 5.0),
                comment=value.get("comment", ""),
            ))
    
    return dimensions


def _parse_text_scores(text: str) -> List[DimensionScore]:
    """解析文本格式的评分"""
    dimensions = []
    
    # 匹配模式：维度名: X分 或 维度名: X/Y
    patterns = [
        r'款式与廓形[:：]\s*(\d+(?:\.\d+)?)',
        r'色彩与图案[:：]\s*(\d+(?:\.\d+)?)',
        r'面料与肌理[:：]\s*(\d+(?:\.\d+)?)',
        r'工艺与结构[:：]\s*(\d+(?:\.\d+)?)',
        r'创意与主题[:：]\s*(\d+(?:\.\d+)?)',
        r'市场与商业[:：]\s*(\d+(?:\.\d+)?)',
        r'整体与系列[:：]\s*(\d+(?:\.\d+)?)',
    ]
    
    dim_names = list(DIMENSION_CONFIG.keys())
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text)
        if match and i < len(dim_names):
            dim_name = dim_names[i]
            config = DIMENSION_CONFIG[dim_name]
            raw = float(match.group(1))
            normalized = (raw / config["max_raw"]) * 5
            
            dimensions.append(DimensionScore(
                name=dim_name,
                raw_score=raw,
                max_score=config["max_raw"],
                normalized_score=min(normalized, 5.0),
                comment="",
            ))
    
    return dimensions


def _get_default_scores() -> List[DimensionScore]:
    """获取默认评分（用于错误情况）"""
    dimensions = []
    
    for name, config in DIMENSION_CONFIG.items():
        default_raw = config["max_raw"] * 0.8  # 默认80分
        dimensions.append(DimensionScore(
            name=name,
            raw_score=default_raw,
            max_score=config["max_raw"],
            normalized_score=4.0,
            comment="默认评分",
        ))
    
    return dimensions


def calculate_ci_score(
    dimension_scores: List[float],
) -> Tuple[float, bool, List[int]]:
    """
    计算CI综合创新指数
    
    Args:
        dimension_scores: 7个维度的5分制分数列表
        
    Returns:
        Tuple[ci_score, passed, low_indices]
        - ci_score: CI总分
        - passed: 是否通过
        - low_indices: 低分项索引（<4分）
    """
    
    if len(dimension_scores) != 7:
        raise ValueError("需要提供7个维度的分数")
    
    ci_score = sum(dimension_scores)
    passed = ci_score >= 28.0 and all(s >= 4.0 for s in dimension_scores)
    low_indices = [i for i, s in enumerate(dimension_scores) if s < 4.0]
    
    return ci_score, passed, low_indices


# 创建FunctionTool
evaluate_7_dimensions_tool = FunctionTool(
    name="evaluate_7_dimensions",
    description="解析LLM的7维度评分响应，计算CI综合创新指数",
    func=evaluate_7_dimensions,
)

calculate_ci_score_tool = FunctionTool(
    name="calculate_ci_score",
    description="计算CI综合创新指数，判断是否通过阈值",
    func=calculate_ci_score,
)
