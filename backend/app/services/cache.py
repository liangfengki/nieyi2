"""
Product DNA 缓存服务 — 基于图片内容 hash 缓存 Vision API 结果
避免相同产品图片重复调用 Vision API
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Optional

# 缓存目录
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "cache", "dna")
os.makedirs(CACHE_DIR, exist_ok=True)

# 缓存过期时间（秒）：24 小时
CACHE_TTL = 86400


def compute_images_hash(base64_images: list[str]) -> str:
    """
    根据图片列表计算唯一 hash 值
    使用第一张图片的 base64 内容作为 hash 依据
    """
    if not base64_images:
        return "empty"
    
    # 取第一张图片计算 hash（通常产品图第一张就是主图）
    content = base64_images[0][:1000]  # 取前 1000 字符足够区分
    return hashlib.md5(content.encode()).hexdigest()


def get_cached_dna(image_hash: str) -> Optional[str]:
    """
    从缓存中获取 Product DNA
    返回: 缓存的 DNA 文本，如果不存在或已过期则返回 None
    """
    cache_file = os.path.join(CACHE_DIR, f"{image_hash}.json")
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, "r") as f:
            data = json.load(f)
        
        # 检查是否过期
        if time.time() - data.get("timestamp", 0) > CACHE_TTL:
            os.remove(cache_file)
            return None
        
        return data.get("dna")
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def cache_dna(image_hash: str, dna: str) -> None:
    """
    将 Product DNA 写入缓存
    """
    cache_file = os.path.join(CACHE_DIR, f"{image_hash}.json")
    
    data = {
        "dna": dna,
        "timestamp": time.time(),
    }
    
    try:
        with open(cache_file, "w") as f:
            json.dump(data, f)
    except OSError:
        pass  # 缓存写入失败不影响主流程


def clear_expired_cache() -> int:
    """
    清理过期缓存文件
    返回: 清理的文件数量
    """
    count = 0
    if not os.path.exists(CACHE_DIR):
        return 0
    
    for filename in os.listdir(CACHE_DIR):
        cache_file = os.path.join(CACHE_DIR, filename)
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
            
            if time.time() - data.get("timestamp", 0) > CACHE_TTL:
                os.remove(cache_file)
                count += 1
        except (json.JSONDecodeError, KeyError, OSError):
            # 损坏的文件也删除
            try:
                os.remove(cache_file)
                count += 1
            except OSError:
                pass
    
    return count
