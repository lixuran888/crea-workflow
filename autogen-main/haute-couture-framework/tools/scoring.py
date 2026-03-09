"""
评分计算工具
13维度评分：6项美学创造力原则 + 7项服装专业原则
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
    category: str  # "aesthetic" 或 "fashion"
    raw_score: float  # 原始分
    max_score: float  # 该维度满分
    normalized_score: float  # 标准化5分制
    comment: str


@dataclass
class EvaluationResult:
    """评估结果"""
    image_id: str
    aesthetic_dimensions: List[DimensionScore]  # 6项美学原则
    fashion_dimensions: List[DimensionScore]   # 7项服装原则
    all_dimensions: List[DimensionScore]        # 全部13项
    ci_score: float  # 综合创新指数 (13项总分)
    aesthetic_score: float  # 美学总分
    fashion_score: float    # 服装专业总分
    passed: bool  # 是否通过（CI>=52）
    low_dimensions: List[str]  # 低分项（<4分）


# 13维度配置
DIMENSION_CONFIG = {
    # 6项美学创造力原则（艺术总监负责）
    "Originality": {"max_raw": 20, "weight": 1.0, "category": "aesthetic", "cn_name": "原创性"},
    "Expressiveness": {"max_raw": 20, "weight": 1.0, "category": "aesthetic", "cn_name": "表现力"},
    "Aesthetic Appeal": {"max_raw": 20, "weight": 1.0, "category": "aesthetic", "cn_name": "审美吸引力"},
    "Technical Execution": {"max_raw": 20, "weight": 1.0, "category": "aesthetic", "cn_name": "技术执行"},
    "Unexpected Associations": {"max_raw": 20, "weight": 1.0, "category": "aesthetic", "cn_name": "意外关联"},
    "Interpretability & Depth": {"max_raw": 20, "weight": 1.0, "category": "aesthetic", "cn_name": "可解释性与深度"},
    
    # 7项服装专业原则（服装设计师负责）
    "Silhouette & Structure": {"max_raw": 15, "weight": 1.0, "category": "fashion", "cn_name": "款式与廓形"},
    "Color & Pattern": {"max_raw": 20, "weight": 1.0, "category": "fashion", "cn_name": "色彩与图案"},
    "Fabric & Texture": {"max_raw": 15, "weight": 1.0, "category": "fashion", "cn_name": "面料与肌理"},
    "Craftsmanship & Construction": {"max_raw": 20, "weight": 1.0, "category": "fashion", "cn_name": "工艺与结构"},
    "Creativity & Theme": {"max_raw": 20, "weight": 1.0, "category": "fashion", "cn_name": "创意与主题"},
    "Market & Commercial": {"max_raw": 20, "weight": 1.0, "category": "fashion", "cn_name": "市场与商业"},
    "Overall & Collection": {"max_raw": 20, "weight": 1.0, "category": "fashion", "cn_name": "整体与系列"},
}


def evaluate_13_dimensions(
    image_id: str,
    prompt: str,
    aesthetic_response: str,  # 艺术总监的6项评分
    fashion_response: str,    # 服装设计师的7项评分
) -> EvaluationResult:
    """
    解析LLM的13维度评分响应（6美学+7服装）
    
    Args:
        image_id: 图像ID
        prompt: 生成prompt
        aesthetic_response: 艺术总监的6项美学评分
        fashion_response: 服装设计师的7项服装评分
        
    Returns:
        EvaluationResult: 评估结果
    """
    
    # 解析6项美学原则
    aesthetic_dims = _parse_dimensions(
        aesthetic_response, 
        [k for k, v in DIMENSION_CONFIG.items() if v["category"] == "aesthetic"]
    )
    
    # 解析7项服装原则
    fashion_dims = _parse_dimensions(
        fashion_response,
        [k for k, v in DIMENSION_CONFIG.items() if v["category"] == "fashion"]
    )
    
    # 合并全部13项
    all_dims = aesthetic_dims + fashion_dims
    
    # 计算各项总分
    aesthetic_score = sum(d.normalized_score for d in aesthetic_dims)
    fashion_score = sum(d.normalized_score for d in fashion_dims)
    ci_score = aesthetic_score + fashion_score
    
    # 找出低分项（<4分）
    low_dimensions = [d.name for d in all_dims if d.normalized_score < 4.0]
    
    # 判断是否通过（CI >= 52，每项平均4分）
    passed = ci_score >= 52.0 and all(d.normalized_score >= 4.0 for d in all_dims)
    
    return EvaluationResult(
        image_id=image_id,
        aesthetic_dimensions=aesthetic_dims,
        fashion_dimensions=fashion_dims,
        all_dimensions=all_dims,
        ci_score=ci_score,
        aesthetic_score=aesthetic_score,
        fashion_score=fashion_score,
        passed=passed,
        low_dimensions=low_dimensions,
    )


def _parse_dimensions(response: str, dim_names: List[str]) -> List[DimensionScore]:
    """解析维度评分"""
    dimensions = []
    
    # 尝试JSON解析
    try:
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            for name in dim_names:
                if name in data.get("scores", {}):
                    value = data["scores"][name]
                    config = DIMENSION_CONFIG[name]
                    raw = float(value.get("raw", value.get("score", 0)))
                    normalized = (raw / config["max_raw"]) * 5
                    
                    dimensions.append(DimensionScore(
                        name=name,
                        category=config["category"],
                        raw_score=raw,
                        max_score=config["max_raw"],
                        normalized_score=min(normalized, 5.0),
                        comment=value.get("comment", ""),
                    ))
            
            if len(dimensions) == len(dim_names):
                return dimensions
    except:
        pass
    
    # 文本解析
    for name in dim_names:
        config = DIMENSION_CONFIG[name]
        cn_name = config["cn_name"]
        
        # 匹配英文或中文名称
        patterns = [
            rf'{name}[:：]\s*(\d+(?:\.\d+)?)',
            rf'{cn_name}[:：]\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                raw = float(match.group(1))
                normalized = (raw / config["max_raw"]) * 5
                
                dimensions.append(DimensionScore(
                    name=name,
                    category=config["category"],
                    raw_score=raw,
                    max_score=config["max_raw"],
                    normalized_score=min(normalized, 5.0),
                    comment="",
                ))
                break
        else:
            # 未找到评分，使用默认值
            default_raw = config["max_raw"] * 0.8
            dimensions.append(DimensionScore(
                name=name,
                category=config["category"],
                raw_score=default_raw,
                max_score=config["max_raw"],
                normalized_score=4.0,
                comment="默认评分",
            ))
    
    return dimensions


def calculate_ci_score_13(
    aesthetic_scores: List[float],
    fashion_scores: List[float],
) -> Tuple[float, float, float, bool, List[int]]:
    """
    计算13维度的CI综合创新指数
    
    Args:
        aesthetic_scores: 6项美学原则分数（5分制）
        fashion_scores: 7项服装原则分数（5分制）
        
    Returns:
        Tuple[ci_score, aesthetic_score, fashion_score, passed, low_indices]
        - ci_score: 13项总分（满分65）
        - aesthetic_score: 美学6项总分
        - fashion_score: 服装7项总分
        - passed: 是否通过（CI>=52）
        - low_indices: 低分项索引（<4分）
    """
    
    if len(aesthetic_scores) != 6:
        raise ValueError("需要提供6项美学原则分数")
    if len(fashion_scores) != 7:
        raise ValueError("需要提供7项服装原则分数")
    
    aesthetic_score = sum(aesthetic_scores)
    fashion_score = sum(fashion_scores)
    ci_score = aesthetic_score + fashion_score
    
    all_scores = aesthetic_scores + fashion_scores
    passed = ci_score >= 52.0 and all(s >= 4.0 for s in all_scores)
    low_indices = [i for i, s in enumerate(all_scores) if s < 4.0]
    
    return ci_score, aesthetic_score, fashion_score, passed, low_indices


# 创建FunctionTool
evaluate_13_dimensions_tool = FunctionTool(
    name="evaluate_13_dimensions",
    description="解析13维度评分（6美学+7服装），计算CI综合创新指数",
    func=evaluate_13_dimensions,
)

calculate_ci_score_13_tool = FunctionTool(
    name="calculate_ci_score_13",
    description="计算13维度的CI综合创新指数，判断是否通过阈值（CI>=52）",
    func=calculate_ci_score_13,
)
