# Haute Couture Framework

高奢品高定服装创意与设计多智能体协作框架

基于 AutoGen 框架实现的专业服装设计AI系统。

## 项目概述

面向高奢品牌设计师的智能辅助设计系统，通过6个专业智能体的协作，实现从创意概念到设计图的完整工作流。

## 核心特性

- **6个专业Agent协作**：服装设计师、提示框架师、创意总监、艺术总监、艺术评论家+服装设计师、优化策略师
- **7维度专业评分**：款式廓形、色彩图案、面料肌理、工艺结构、创意主题、市场商业、整体系列
- **7n+a提示策略**：论文+专业知识驱动的prompt生成
- **自增强优化**：基于α和βₖ权重的迭代优化
- **CI阈值控制**：每张图CI≥28的严格标准

## 系统架构

```
用户输入 → 选择m → 创意策划层 → 图像生成层 → 评估筛选层 → 自增强层（如需要）
                ↓
        6个Agent协作
```

## 安装

```bash
pip install -r requirements.txt
```

## 配置

```bash
cp .env.example .env
# 编辑.env，填入API密钥
```

## 运行

```bash
python main.py
```

## 项目结构

```
haute-couture-framework/
├── agents/              # 6个专业Agent
├── workflow/           # GraphFlow工作流
├── config/            # 配置文件
├── main.py           # 主入口
├── requirements.txt
└── README.md
```
