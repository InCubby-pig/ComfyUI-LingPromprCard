# ComfyUI-LingPromptCard

独立的 PromptCard 抽卡节点仓库。

## 包含内容
- `promptcard/`：PromptCard 抽卡节点与数据
- `tools/`：数据清洗与辅助脚本
- `__init__.py`：ComfyUI 节点注册入口

## 节点列表
- 灵感抽卡-服装
- 灵感抽卡-构图
- 灵感抽卡-R18情景
- 灵感抽卡-场景

## 安装方式
1. 将本仓库放入：`<ComfyUI>/custom_nodes/ComfyUI-LingPromptCard/`
2. 重启 ComfyUI
3. 在 `lingpromptcard/cards` 分类下使用节点

## 开发校验
```bash
python3 -m py_compile __init__.py promptcard/*.py
```
