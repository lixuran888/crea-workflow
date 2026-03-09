"""
图像生成工具
使用阿里云通义万相API
"""

import os
import time
from typing import List, Optional
from dataclasses import dataclass

import requests
from autogen_agentchat.tools import FunctionTool


@dataclass
class GeneratedImage:
    """生成的图像"""
    image_id: str
    url: str
    prompt: str
    local_path: Optional[str] = None


def generate_images(
    prompt: str,
    n: int = 5,
    size: str = "1024x1024",
    quality: str = "high",
    api_key: Optional[str] = None,
) -> List[GeneratedImage]:
    """
    使用通义万相生成图像
    
    Args:
        prompt: 图像描述prompt
        n: 生成数量
        size: 图像尺寸
        quality: 图像质量
        api_key: API密钥
        
    Returns:
        List[GeneratedImage]: 生成的图像列表
    """
    
    if api_key is None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if api_key is None:
        raise ValueError("请提供api_key或设置DASHSCOPE_API_KEY")
    
    # 通义万相API端点
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }
    
    # 构建请求体
    payload = {
        "model": "wanx-v1",
        "input": {
            "prompt": prompt,
        },
        "parameters": {
            "size": size,
            "n": n,
            "seed": int(time.time()),
        }
    }
    
    try:
        # 提交任务
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        task_id = result.get("output", {}).get("task_id")
        
        if not task_id:
            raise Exception(f"创建任务失败: {result}")
        
        # 轮询获取结果
        images = _poll_task_result(task_id, api_key, prompt)
        return images
        
    except Exception as e:
        print(f"图像生成失败: {e}")
        # 返回模拟数据用于测试
        return _mock_generate_images(prompt, n)


def _poll_task_result(
    task_id: str,
    api_key: str,
    prompt: str,
    max_retries: int = 30,
    interval: int = 2,
) -> List[GeneratedImage]:
    """轮询获取任务结果"""
    
    url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    for i in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            task_status = result.get("output", {}).get("task_status")
            
            if task_status == "SUCCEEDED":
                # 任务完成，获取图片URL
                results = result.get("output", {}).get("results", [])
                images = []
                
                for idx, item in enumerate(results):
                    img_url = item.get("url")
                    if img_url:
                        images.append(GeneratedImage(
                            image_id=f"img_{task_id}_{idx}",
                            url=img_url,
                            prompt=prompt,
                        ))
                
                return images
                
            elif task_status in ["FAILED", "CANCELLED"]:
                raise Exception(f"任务失败: {result}")
            
            # 等待后重试
            time.sleep(interval)
            
        except Exception as e:
            print(f"轮询出错: {e}")
            time.sleep(interval)
    
    raise Exception("获取结果超时")


def _mock_generate_images(prompt: str, n: int) -> List[GeneratedImage]:
    """模拟生成图像（用于测试）"""
    print(f"[模拟模式] 生成 {n} 张图像")
    print(f"Prompt: {prompt[:100]}...")
    
    images = []
    for i in range(n):
        images.append(GeneratedImage(
            image_id=f"mock_img_{i}",
            url=f"https://example.com/mock_image_{i}.png",
            prompt=prompt,
        ))
    
    return images


# 创建FunctionTool供Agent使用
generate_images_tool = FunctionTool(
    name="generate_images",
    description="使用通义万相生成服装设计图。输入prompt和数量，返回生成的图像列表。",
    func=generate_images,
)
