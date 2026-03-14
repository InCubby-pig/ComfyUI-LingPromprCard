# ComfyUI-LingPromptCard

独立的 PromptCard 抽卡节点仓库。

## 包含内容
- `promptcard/`：PromptCard 抽卡节点与数据
- `promptcard/nodes/`：按分类组织的节点实现（基础 / Danbooru细分 / Danbooru合并）
- `promptcard/data/`：Danbooru 自动生成数据
- `tools/`：数据清洗与辅助脚本
- `__init__.py`：ComfyUI 节点注册入口

## 节点列表
- 灵感抽卡-服装
- 灵感抽卡-构图
- 灵感抽卡-R18情景
- 灵感抽卡-场景
- Danbooru标签-细分抽卡器（自动生成，多节点）
- Danbooru标签-合并抽卡器（自动生成，多列表并列）

## 安装方式
1. 将本仓库放入：`<ComfyUI>/custom_nodes/ComfyUI-LingPromptCard/`
2. 重启 ComfyUI
3. 在 `lingpromptcard/cards` 分类下使用节点
   - 基础节点：`lingpromptcard/cards/basic`
   - Danbooru细分：`lingpromptcard/cards/danbooru/split`
   - Danbooru合并：`lingpromptcard/cards/danbooru/merge`

## 开发校验
```bash
python3 -m py_compile __init__.py promptcard/*.py promptcard/nodes/**/*.py promptcard/data/*.py promptcard/data/danbooru/*.py
```

## Danbooru 数据更新
```bash
python3 tools/extract_danbooru_tag_groups.py
```
执行后会更新：
- `promptcard/data/danbooru/*.py`
- `promptcard/data/danbooru_index.py`
- `promptcard/data/danbooru_merge_index.py`
- `tools/danbooru_tag_groups_review.md`
