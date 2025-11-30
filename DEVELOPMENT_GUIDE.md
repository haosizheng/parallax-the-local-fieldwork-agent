# Parallax 开发指南

这是一份针对 Parallax 项目的完整开发和测试指南。

## 📦 环境准备

### 系统要求
- **Python**: 3.11.0 - 3.13.x
- **操作系统**: macOS (Apple Silicon)
- **推荐**: 使用虚拟环境隔离依赖

### 安装步骤

#### 1. 激活虚拟环境
```bash
cd /Users/shibi/Documents/cursor-test/gradient/parallax
source venv/bin/activate
```

#### 2. 安装开发依赖
```bash
# 安装 Mac 版本 + 开发工具
pip install -e '.[mac,dev]'
```

这会安装：
- **核心依赖**: parallax 的基础功能
- **Mac 后端**: MLX-LM (Apple Silicon 优化的 LLM 推理引擎)
- **开发工具**: pytest, black, ruff, pre-commit 等

#### 3. 设置代码格式化工具
```bash
# 安装 pre-commit hooks
pre-commit install

# 手动运行检查（可选）
pre-commit run --all-files
```

---

## 🧪 测试流程

### 运行所有测试
```bash
# 在项目根目录下
pytest tests/

# 带详细输出
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --cov=src/parallax --cov-report=html
```

### 运行特定测试
```bash
# 测试单个文件
pytest tests/test_model.py -v

# 测试特定函数
pytest tests/test_model.py::test_shard_prefill -v

# 使用参数化测试
pytest tests/test_model.py::test_shard_prefill -v -k "0, 12"
```

### 常见测试场景

#### 1. 测试模型分片加载
```bash
pytest tests/test_model.py -v
```
这会测试 Parallax 的核心功能：将大模型切分到不同节点。

#### 2. 测试调度器
```bash
pytest tests/scheduler_tests/ -v
```

#### 3. 测试 HTTP 处理
```bash
pytest tests/test_http_handler.py -v
```

---

## 🛠️ 开发工作流

### 1. 创建功能分支
```bash
git checkout -b feat/your-feature-name
```

### 2. 编写代码
主要代码目录结构：
```
src/
├── parallax/          # 核心引擎
│   ├── cli.py        # 命令行接口
│   ├── server/       # 服务器逻辑
│   └── utils/        # 工具函数
├── scheduling/        # 调度算法
├── parallax_utils/    # 通用工具
├── backend/          # 后端实现 (MLX/SGLang)
└── frontend/         # Web UI
```

### 3. 运行代码格式化
```bash
# 自动格式化
black src/ tests/

# 检查代码风格
ruff check src/ tests/

# 或使用 pre-commit 一次性检查
pre-commit run --all-files
```

### 4. 编写测试
在 `tests/` 目录下创建对应的测试文件：
```python
# tests/test_your_feature.py
import pytest
from parallax.your_module import your_function

def test_your_feature():
    result = your_function()
    assert result == expected_value
```

### 5. 提交代码
```bash
git add .
git commit -m "feat: add your feature description"

# pre-commit 会自动运行检查
```

---

## 🚀 本地运行 Parallax

### 快速启动（单节点测试）

#### 1. 启动调度器
```bash
# 使用小模型测试
parallax run -m mlx-community/Qwen3-0.6B-bf16 -n 1
```

#### 2. 在另一个终端启动节点
```bash
source venv/bin/activate
parallax join
```

#### 3. 测试 API
```bash
curl --location 'http://localhost:3001/v1/chat/completions' \
  --header 'Content-Type: application/json' \
  --data '{
    "max_tokens": 100,
    "messages": [
      {
        "role": "user",
        "content": "你好，介绍一下你自己"
      }
    ],
    "stream": true
  }'
```

### 多节点测试（分布式）

#### 节点 1（调度器 + 第一个分片）
```bash
parallax run -m mlx-community/Qwen3-0.6B-bf16 -n 2 --host 0.0.0.0
# 记录显示的 scheduler-address
```

#### 节点 2（第二个分片）
```bash
parallax join -s <scheduler-address>
```

---

## 🐛 调试技巧

### 1. 查看详细日志
```bash
# 运行时添加调试信息
parallax run -m mlx-community/Qwen3-0.6B-bf16 -n 1 --log-level DEBUG
```

### 2. 使用 Python 调试器
```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 ipdb (更友好)
import ipdb; ipdb.set_trace()
```

### 3. 单元测试调试
```bash
# 进入 pdb 调试模式
pytest tests/test_model.py --pdb

# 在第一个失败时停止
pytest tests/ -x
```

---

## 📚 常用命令速查

| 命令 | 说明 |
|------|------|
| `source venv/bin/activate` | 激活虚拟环境 |
| `pip install -e '.[mac,dev]'` | 安装开发依赖 |
| `pytest tests/ -v` | 运行所有测试 |
| `pre-commit run --all-files` | 代码格式检查 |
| `parallax run -m MODEL -n N` | 启动调度器 |
| `parallax join` | 加入集群 |
| `parallax --help` | 查看所有命令 |

---

## 🔗 相关资源

- **官方文档**: [docs/user_guide/](./docs/user_guide/)
- **贡献指南**: [docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md)
- **Discord 社区**: https://discord.gg/parallax
- **GitHub Issues**: https://github.com/GradientHQ/parallax/issues

---

## 💡 开发建议

1. **从小模型开始**: 使用 `Qwen3-0.6B` 这样的小模型进行测试，速度快，占用资源少。
2. **先跑通测试**: 确保所有单元测试通过后再开发新功能。
3. **阅读现有代码**: 查看 `tests/` 目录下的测试用例，了解如何使用各个模块。
4. **增量开发**: 每次只改一小部分，及时测试，避免大规模重构。
5. **使用 pre-commit**: 提交前自动格式化，减少 PR 审查时的格式问题。

---

## 🎯 常见开发任务

### 添加新模型支持
1. 查看 `src/parallax/server/shard_loader.py`
2. 参考现有模型配置
3. 添加测试用例到 `tests/test_model.py`

### 优化调度算法
1. 修改 `src/scheduling/` 下的调度逻辑
2. 运行 `pytest tests/scheduler_tests/` 验证
3. 使用 benchmark 测试性能

### 改进 CLI
1. 编辑 `src/parallax/cli.py`
2. 测试命令: `parallax --help`
3. 添加集成测试

---

祝开发顺利！🎉
