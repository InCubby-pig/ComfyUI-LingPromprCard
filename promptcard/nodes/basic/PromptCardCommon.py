import random
from typing import Dict, List, Tuple

from ...PromptCardData import PROMPT_CARD_DATA
from ...data.danbooru_i18n import format_label_display, format_tag_display, load_zh_cn_lexicon


class LingPromptCardBase:
    """Prompt 抽卡节点公共逻辑。"""

    NODE_KEY = ""
    CATEGORY = "lingpromptcard/cards"
    FUNCTION = "draw_prompt"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("正面提示词", "负面提示词")
    MODE_OPTIONS = ("🔒 手动指定", "🎲 部分随机(手动优先)", "🔓 完全随机")
    MODE_DEFAULT = "🔒 手动指定"
    DATA_SOURCE = PROMPT_CARD_DATA

    _CACHED_CONFIG: Dict[str, object] = {}

    @classmethod
    def _build_config(cls) -> Dict[str, object]:
        node_data = cls.DATA_SOURCE.get(cls.NODE_KEY, {})
        raw_categories = node_data.get("categories", [])
        zh_lexicon = load_zh_cn_lexicon()

        categories = []
        used_display_labels = set()
        for idx, cat in enumerate(raw_categories, start=1):
            items = cat.get("items", [])
            if not items:
                continue

            label = str(cat.get("label", f"分类{idx}")).strip() or f"分类{idx}"
            input_key = str(cat.get("input_key", label)).strip() or label
            raw_display_label = str(cat.get("display_label", "")).strip()
            if not raw_display_label:
                raw_display_label = format_label_display(label, zh_lexicon)
            display_label = raw_display_label
            if display_label in used_display_labels:
                display_label = f"{raw_display_label} [{label}]"
            used_display_labels.add(display_label)

            item_options = ["(随机)"]
            display_to_item: Dict[str, Dict[str, object]] = {}
            raw_to_item: Dict[str, Dict[str, object]] = {}
            used_item_options = set(item_options)
            for item_idx, item in enumerate(items, start=1):
                item_title = str(item.get("title", f"条目{item_idx}")).strip()
                if not item_title:
                    item_title = f"条目{item_idx}"
                display_title = str(item.get("display_title", "")).strip()
                if not display_title:
                    display_title = format_tag_display(item_title, zh_lexicon)
                if display_title in used_item_options:
                    if display_title != item_title:
                        display_title = f"{display_title} [{item_title}]"
                    else:
                        display_title = f"{display_title} [{item_idx}]"
                used_item_options.add(display_title)
                item_options.append(display_title)
                display_to_item[display_title] = item
                raw_to_item[item_title] = item

            # 使用分类名作为输入键，便于在 UI 里直接看到分类。
            categories.append(
                {
                    "label": label,
                    "display_label": display_label,
                    "input_key": input_key,
                    "items": items,
                    "item_options": item_options,
                    "display_to_item": display_to_item,
                    "raw_to_item": raw_to_item,
                }
            )

        manual_options = ["(不指定)"] + [c["display_label"] for c in categories]
        label_map = {c["label"]: c for c in categories}
        display_label_map = {c["display_label"]: c for c in categories}

        return {
            "categories": categories,
            "manual_options": manual_options,
            "label_map": label_map,
            "display_label_map": display_label_map,
        }

    @classmethod
    def _get_config(cls) -> Dict[str, object]:
        cache_key = cls.NODE_KEY
        if cache_key not in cls._CACHED_CONFIG:
            cls._CACHED_CONFIG[cache_key] = cls._build_config()
        return cls._CACHED_CONFIG[cache_key]

    @classmethod
    def INPUT_TYPES(cls):
        config = cls._get_config()
        manual_options: List[str] = config["manual_options"]
        categories: List[Dict[str, object]] = config["categories"]
        mode_options = list(cls.MODE_OPTIONS)
        mode_default = cls.MODE_DEFAULT
        if not mode_options:
            mode_options = ["🔒 手动指定", "🎲 部分随机(手动优先)", "🔓 完全随机"]
        if mode_default not in mode_options:
            mode_default = mode_options[0]

        required_inputs = {
            "总开关": (
                "BOOLEAN",
                {
                    "default": True,
                    "label_on": "节点开启",
                    "label_off": "节点关闭",
                    "display": "toggle",
                },
            ),
            "模式选择": (
                mode_options,
                {"default": mode_default},
            ),
            "seed": (
                "INT",
                {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "step": 1},
            ),
            "分类": (manual_options, {"default": "(不指定)"}),
        }

        for category in categories:
            required_inputs[category["input_key"]] = (
                category["item_options"],
                {"default": "(随机)"},
            )

        return {"required": required_inputs}

    def draw_prompt(self, **kwargs) -> Tuple[str, str]:
        if not kwargs.get("总开关", True):
            return ("", "")

        config = self.__class__._get_config()
        categories: List[Dict[str, object]] = config["categories"]
        label_map: Dict[str, Dict[str, object]] = config["label_map"]
        display_label_map: Dict[str, Dict[str, object]] = config["display_label_map"]

        mode = kwargs.get("模式选择", self.MODE_DEFAULT)
        manual_label = kwargs.get("分类", kwargs.get("手动分类", "(不指定)"))
        seed = int(kwargs.get("seed", 0))
        rng = random.Random(seed)

        all_items = []
        for cat in categories:
            all_items.extend(cat["items"])

        if not all_items:
            return ("", "")

        selected_items = list(all_items)
        use_category_scope = mode != "🔓 完全随机"

        if use_category_scope:
            manual_cat = None
            if manual_label != "(不指定)":
                manual_cat = display_label_map.get(manual_label) or label_map.get(manual_label)
                if not manual_cat:
                    return ("", "")

            # 当用户直接在某个分类下拉里选了具体 item，自动以该分类为准。
            explicit_item_cats = []
            for category in categories:
                manual_item_value = kwargs.get(category["input_key"], "(随机)")
                if manual_item_value != "(随机)":
                    explicit_item_cats.append(category)

            if explicit_item_cats and manual_cat not in explicit_item_cats:
                manual_cat = explicit_item_cats[0]

            if manual_cat:
                selected_items = list(manual_cat["items"])
                manual_item = kwargs.get(manual_cat["input_key"], "(随机)")
                if manual_item != "(随机)":
                    display_item = manual_cat["display_to_item"].get(manual_item)
                    raw_item = manual_cat["raw_to_item"].get(manual_item)
                    if display_item is not None:
                        selected_items = [display_item]
                    elif raw_item is not None:
                        selected_items = [raw_item]

        if not selected_items:
            return ("", "")

        chosen = rng.choice(selected_items)
        prompt_pos = chosen.get("prompt_pos", "")
        prompt_neg = chosen.get("prompt_neg", "")
        if not isinstance(prompt_pos, str):
            return ("", "")
        if not isinstance(prompt_neg, str):
            prompt_neg = ""
        return (prompt_pos, prompt_neg)
