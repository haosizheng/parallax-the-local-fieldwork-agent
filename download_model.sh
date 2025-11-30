#!/bin/bash

# 手动下载 Qwen3-0.6B 模型
# 使用 HuggingFace 镜像源

echo "📥 开始下载 Qwen3-0.6B 模型..."
echo ""

# 进入项目目录
cd /Users/shibi/Documents/cursor-test/gradient/parallax

# 激活虚拟环境
source venv/bin/activate

# 设置 HuggingFace 镜像源
export HF_ENDPOINT=https://hf-mirror.com
echo "✅ 使用镜像源: $HF_ENDPOINT"
echo ""

# 使用 huggingface-cli 下载模型
echo "🔽 正在下载模型文件..."
huggingface-cli download \
  --repo-type model \
  --resume-download \
  mlx-community/Qwen3-0.6B-bf16

echo ""
echo "✅ 模型下载完成！"
echo "📁 模型位置: ~/.cache/huggingface/hub/"
