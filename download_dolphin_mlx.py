#!/usr/bin/env python3
"""
Download mlx-community/dolphin-2.9.2-qwen2-7b-4bit from HuggingFace (using mirror)
and create symlinks for Parallax.
"""

import os
import shutil
from pathlib import Path
from huggingface_hub import snapshot_download

# Set HF Mirror for faster download in China
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

print("=" * 60)
print("Downloading mlx-community/dolphin-2.9.2-qwen2-7b-4bit")
print("=" * 60)

# Model ID on HuggingFace
model_id = "mlx-community/dolphin-2.9.2-qwen2-7b-4bit"

print(f"\nDownloading model: {model_id}")
print("Using HF Mirror: https://hf-mirror.com")
print("This may take a while depending on your internet connection...\n")

try:
    # Download model to default HF cache
    # This returns the path to the snapshot directory
    model_dir = snapshot_download(repo_id=model_id)
    print(f"\n✅ Model downloaded successfully!")
    print(f"📁 Source location: {model_dir}")
    
    # Define the target directory in the project's models folder
    # This matches the structure used in start_qwen25_7b.sh
    project_root = Path(__file__).parent
    target_dir = project_root / "models" / "mlx-community" / "dolphin-2.9.2-qwen2-7b-4bit"
    
    # Create parent directory if it doesn't exist
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    
    # If target exists, remove it (it might be a symlink or old dir)
    if target_dir.exists():
        print(f"\n🗑️  Removing existing link/directory: {target_dir}")
        if target_dir.is_symlink():
            target_dir.unlink()
        else:
            shutil.rmtree(target_dir)
    
    # Create symlink
    print(f"\n🔗 Creating symlink...")
    print(f"   From: {model_dir}")
    print(f"   To:   {target_dir}")
    
    target_dir.symlink_to(model_dir)
    
    print(f"\n✅ Setup complete!")
    print(f"\nYou can now start Parallax with this model using:")
    print(f"   ./start_dolphin.sh")
    
except Exception as e:
    print(f"\n❌ Download failed: {e}")
    print(f"\nPlease check your network connection.")
