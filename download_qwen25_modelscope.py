#!/usr/bin/env python3
"""
从 ModelScope 下载 Qwen2.5-0.5B-Instruct 模型
然后创建符号链接让 Parallax 可以使用
"""

import os
import shutil
from pathlib import Path
from modelscope import snapshot_download

print("=" * 60)
print("从 ModelScope 下载 Qwen2.5-0.5B-Instruct")
print("=" * 60)

# ModelScope 上的模型 ID
model_id = "Qwen/Qwen2.5-0.5B-Instruct"

print(f"\n正在下载模型: {model_id}")
print("这可能需要几分钟，请耐心等待...\n")

try:
    # 下载模型到 ModelScope 缓存目录
    model_dir = snapshot_download(model_id)
    print(f"\n✅ 模型下载成功！")
    print(f"📁 模型位置: {model_dir}")
    
    # 创建 HuggingFace 缓存目录结构
    hf_cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    hf_cache_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建模型目录名（HuggingFace 格式）
    hf_model_name = "models--mlx-community--Qwen2.5-0.5B-Instruct"
    hf_model_dir = hf_cache_dir / hf_model_name
    
    # 如果已存在，先删除
    if hf_model_dir.exists():
        print(f"\n🗑️  删除旧的符号链接: {hf_model_dir}")
        shutil.rmtree(hf_model_dir)
    
    # 创建符号链接
    print(f"\n🔗 创建符号链接...")
    print(f"   从: {model_dir}")
    print(f"   到: {hf_model_dir}")
    
    # 创建 snapshots 目录结构
    snapshots_dir = hf_model_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建一个快照目录（使用固定的 hash）
    snapshot_hash = "main"
    snapshot_dir = snapshots_dir / snapshot_hash
    
    # 创建符号链接
    if snapshot_dir.exists():
        snapshot_dir.unlink()
    snapshot_dir.symlink_to(model_dir)
    
    print(f"\n✅ 符号链接创建成功！")
    print(f"\n现在你可以使用以下命令启动 Parallax:")
    print(f"   parallax run -m mlx-community/Qwen2.5-0.5B-Instruct -n 1")
    
except Exception as e:
    print(f"\n❌ 下载失败: {e}")
    print(f"\n请检查网络连接或尝试手动下载")
