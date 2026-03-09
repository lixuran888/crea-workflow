# Haute Couture Framework

高奢品高定服装创意与设计多智能体协作框架

基于 **AutoGen** 框架 + **阿里云DashScope**（通义千问+通义万相）实现的专业服装设计AI系统。

## 项目概述

面向高奢品牌设计师的智能辅助设计系统，通过**7个专业智能体**的协作，实现从创意概念到设计图的完整工作流。

## 核心特性

- **7个专业Agent协作**：
  - 服装设计师（蓝图+专业约束）
  - 提示框架师（7n+a策略生成）
  - 创意总监（任务分发+审核）
  - 艺术总监（审美+6项创造力原则）
  - 艺术评论家+服装设计师（多模态7维度评分）
  - 优化策略师（自增强+权重计算）
  - 生成执行器（图像生成工具调用）

- **13维度专业评分**：
  
  **6项美学创造力原则**（艺术总监负责）：
  1. Originality (原创性) - Boden创造力理论
  2. Expressiveness (表现力) - Amabile模型
  3. Aesthetic Appeal (审美吸引力) - Martindale美学模型
  4. Technical Execution (技术执行) - AI创造力框架
  5. Unexpected Associations (意外关联) - Geneplore模型
  6. Interpretability & Depth (可解释性与深度) - Ramachandran法则
  
  **7项服装专业原则**（服装设计师负责）：
  7. Silhouette & Structure (款式与廓形)
  8. Color & Pattern (色彩与图案)
  9. Fabric & Texture (面料与肌理)
  10. Craftsmanship & Construction (工艺与结构)
  11. Creativity & Theme (创意与主题)
  12. Market & Commercial (市场与商业)
  13. Overall & Collection (整体与系列)

- **7n+a提示策略**：论文+专业知识驱动的prompt生成
- **自增强优化**：基于α和βₖ权重的迭代优化
- **CI阈值控制**：每张图CI≥28的严格标准
- **真实工具调用**：通义万相图像生成API

## 系统架构

```
用户输入(m) → 创意策划层 → 图像生成层(k张) → 评估筛选层 → 自增强层（如需要）
                    ↓
            7个Agent协作 + 真实工具调用
```

## 四阶段闭环流程

### 阶段1：创意策划层
1. 服装设计师分析需求，提供蓝图
2. 提示框架师7n+a生成prompt
3. 三方会审（艺术总监+服装设计师+创意总监）
4. 循环直到全部通过

### 阶段2：图像生成层
1. 生成执行器调用通义万相API
2. 生成k张服装设计图

### 阶段3：评估筛选层
1. 艺术评论家+服装设计师7维度评分
2. 计算CI = ΣSi (i∈[1,7])
3. 选出最高分m张
4. 检查每张CI≥28

### 阶段4：自增强层（如需要）
1. 计算α = (28-CI)/28
2. 计算βₖ = γ×(L/L_max)×(1/(1+δ×k))
3. 优化策略师制定细化计划
4. 提示框架师更新prompt
5. 迭代直到达标或达到最大次数

## 安装

```bash
pip install -r requirements.txt
```

## 配置

1. 申请阿里云DashScope API Key：
   - https://dashscope.aliyun.com/

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env，填入你的API Key
DASHSCOPE_API_KEY=sk-your-api-key-here
```

## 运行

```bash
python main.py
```

## 项目结构

```
haute-couture-framework/
├── agents/                    # 7个专业Agent
│   ├── fashion_designer.py       # 服装设计师
│   ├── prompt_architect.py       # 提示框架师
│   ├── creative_director.py      # 创意总监
│   ├── art_director.py           # 艺术总监
│   ├── fashion_critic.py         # 艺术评论家+服装设计师
│   ├── refinement_strategist.py  # 优化策略师
│   └── generative_executor.py    # 生成执行器
├── tools/                     # 工具函数
│   ├── image_generation.py       # 通义万相图像生成
│   └── scoring.py                # 7维度评分计算
├── workflow/                  # GraphFlow工作流
│   └── haute_couture_workflow.py # 完整四阶段流程
├── config/                    # 配置文件
│   └── model_config.py           # 阿里云模型配置
├── main.py                   # 主入口
├── requirements.txt          # 依赖列表
├── .env.example              # 环境变量模板
└── README.md                 # 说明文档
```

## 评分标准

### CI计算（综合创新指数）
```
CI = ΣSi (i∈[1,13])

满分：65分（每项5分）
- 美学6项：30分
- 服装7项：35分

目标阈值：52分（每项平均4分）
单项最低：4分
```

### 优化权重公式
```
α = (28 - CI) / 28
βₖ = γ × (L/L_max) × (1 / (1 + δ×k))

其中：
- γ = 0.8 (全局缩放因子)
- L = 用户输入长度
- L_max = 100 (归一化常数)
- δ = 0.3 (衰减率)
- k = 迭代轮次
```

## 技术栈

- **框架**：Microsoft AutoGen
- **LLM**：阿里云通义千问 (Qwen-Max/Plus/Turbo)
- **图像生成**：阿里云通义万相 (Wanx-V1)
- **语言**：Python 3.9+

## 许可证

MIT License
