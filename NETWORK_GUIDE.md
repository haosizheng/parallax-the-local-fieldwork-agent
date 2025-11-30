# Parallax 网络问题解决方案

## 🌐 问题说明

中国大陆访问 HuggingFace 经常遇到以下问题：
- SSL 连接错误
- 连接超时
- 下载速度极慢
- 下载到 94% 卡住

## ✅ 解决方案：使用 HuggingFace 镜像源

我已经为你创建了配置好镜像源的启动脚本。

---

## 📋 完整使用流程

### 方案 A：先下载模型，再启动（推荐）

#### 步骤 1: 下载模型
```bash
./download_model.sh
```

这个脚本会：
- 使用 `hf-mirror.com` 镜像源
- 支持断点续传（中断后可继续）
- 下载 Qwen3-0.6B 模型（约 1.2GB）

**预计时间**: 5-10 分钟（取决于网速）

#### 步骤 2: 启动调度器
在**终端 1**中运行：
```bash
./start_scheduler.sh
```

#### 步骤 3: 启动节点
在**终端 2**（新终端）中运行：
```bash
./start_node.sh
```

#### 步骤 4: 访问 Web UI
打开浏览器访问：
```
http://localhost:3001
```

---

### 方案 B：直接启动（自动下载）

如果你想一步到位：

#### 终端 1: 启动调度器
```bash
./start_scheduler.sh
```

#### 终端 2: 启动节点
```bash
./start_node.sh
```

模型会在启动时自动下载（使用镜像源）。

---

## 🔧 镜像源配置说明

脚本中已经设置了以下环境变量：

```bash
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DOWNLOAD_TIMEOUT=300
```

这会：
- ✅ 使用国内镜像源（速度快）
- ✅ 增加超时时间到 300 秒
- ✅ 避免 SSL 错误

---

## 📁 模型存储位置

下载的模型会保存在：
```
~/.cache/huggingface/hub/models--mlx-community--Qwen3-0.6B-bf16/
```

下次启动时会直接使用缓存，不需要重新下载。

---

## 🐛 故障排查

### 问题 1: 下载仍然很慢
**解决方案**: 
- 检查网络连接
- 尝试更换网络（比如手机热点）
- 使用方案 A 的手动下载，支持断点续传

### 问题 2: 镜像源无法访问
**解决方案**: 
尝试其他镜像源，修改脚本中的 `HF_ENDPOINT`：
```bash
# 选项 1: ModelScope 镜像
export HF_ENDPOINT=https://modelscope.cn

# 选项 2: 阿里云镜像
export HF_ENDPOINT=https://mirrors.aliyun.com/huggingface
```

### 问题 3: 已经下载了 94%，不想重新下载
**解决方案**:
HuggingFace 的下载支持断点续传，直接运行 `./download_model.sh` 会从断点继续。

---

## 🎯 推荐步骤（当前情况）

你现在的情况：
- ✅ 调度器正在运行（终端 1）
- ❌ 节点下载失败（网络问题）
- 📦 模型已下载 94%

**建议操作**：

1. **保持终端 1 运行**（调度器）

2. **在新终端运行**：
   ```bash
   ./download_model.sh
   ```
   这会从 94% 继续下载剩余的 6%

3. **下载完成后，运行**：
   ```bash
   ./start_node.sh
   ```

4. **在浏览器中访问**：
   ```
   http://localhost:3001
   ```

---

## 📊 预期结果

成功后你会看到：

**终端 1（调度器）**:
```
INFO: Uvicorn running on http://localhost:3001
```

**终端 2（节点）**:
```
[INFO] Connected to scheduler
[INFO] Model loaded successfully
[INFO] Node ready
```

**Web UI**:
- 节点状态：🟢 Connected
- 可以开始聊天

---

祝你使用顺利！🚀
