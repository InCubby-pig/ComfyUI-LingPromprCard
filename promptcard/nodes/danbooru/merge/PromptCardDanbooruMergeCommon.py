import random
from typing import Dict, List, Tuple

from ....data.danbooru_i18n import format_label_display, format_tag_display, load_zh_cn_lexicon


class LingPromptCardMergeBase:
    """Danbooru 合并抽卡器公共逻辑。"""

    NODE_KEY = ""
    CATEGORY = "lingpromptcard/cards"
    FUNCTION = "draw_prompt"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("正面提示词", "负面提示词")
    DATA_SOURCE: Dict[str, Dict[str, object]] = {}

    _CACHED_CONFIG: Dict[str, object] = {}

    @classmethod
    def _build_config(cls) -> Dict[str, object]:
        node_data = cls.DATA_SOURCE.get(cls.NODE_KEY, {})
        raw_lists = node_data.get("lists", [])
        zh_lexicon = load_zh_cn_lexicon()

        lists: List[Dict[str, object]] = []
        for idx, row in enumerate(raw_lists, start=1):
            label = str(row.get("label", f"列表{idx}")).strip() or f"列表{idx}"
            input_key = str(row.get("input_key", label)).strip() or label
            display_label = str(row.get("display_label", "")).strip()
            if not display_label:
                display_label = format_label_display(label, zh_lexicon)
            raw_tags = row.get("tags", [])
            display_tags_map = row.get("display_tags", {})

            dedupe_tags: List[str] = []
            display_to_tag: Dict[str, str] = {}
            raw_to_tag: Dict[str, str] = {}
            seen = set()
            for tag in raw_tags:
                tag = str(tag).strip()
                if not tag or tag in seen:
                    continue
                seen.add(tag)
                dedupe_tags.append(tag)
                display_tag = str(display_tags_map.get(tag, "")).strip()
                if not display_tag:
                    display_tag = format_tag_display(tag, zh_lexicon)
                if display_tag in display_to_tag and display_to_tag[display_tag] != tag:
                    display_tag = f"{display_tag} [{tag}]"
                display_to_tag[display_tag] = tag
                raw_to_tag[tag] = tag

            item_options = ["(不输出)", "(随机)"] + list(display_to_tag.keys())
            lists.append(
                {
                    "label": label,
                    "display_label": display_label,
                    "input_key": input_key,
                    "tags": dedupe_tags,
                    "item_options": item_options,
                    "display_to_tag": display_to_tag,
                    "raw_to_tag": raw_to_tag,
                }
            )

        return {"lists": lists}

    @classmethod
    def _get_config(cls) -> Dict[str, object]:
        cache_key = cls.NODE_KEY
        if cache_key not in cls._CACHED_CONFIG:
            cls._CACHED_CONFIG[cache_key] = cls._build_config()
        return cls._CACHED_CONFIG[cache_key]

    @classmethod
    def INPUT_TYPES(cls):
        config = cls._get_config()
        lists: List[Dict[str, object]] = config["lists"]

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
            "seed": (
                "INT",
                {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "step": 1},
            ),
        }

        for row in lists:
            required_inputs[row["input_key"]] = (
                row["item_options"],
                {"default": "(随机)"},
            )

        return {"required": required_inputs}

    def draw_prompt(self, **kwargs) -> Tuple[str, str]:
        if not kwargs.get("总开关", True):
            return ("", "")

        config = self.__class__._get_config()
        lists: List[Dict[str, object]] = config["lists"]
        seed = int(kwargs.get("seed", 0))

        outputs: List[str] = []
        for idx, row in enumerate(lists):
            input_key = str(row["input_key"])
            value = kwargs.get(input_key, "(随机)")
            tags = row["tags"]
            if not tags:
                continue

            if value == "(不输出)":
                continue

            if value == "(随机)":
                local_rng = random.Random((seed << 16) ^ (idx + 1))
                chosen = local_rng.choice(tags)
                outputs.append(chosen)
                continue

            mapped = row["display_to_tag"].get(value)
            if mapped:
                outputs.append(mapped)
                continue

            if value in row["raw_to_tag"]:
                outputs.append(value)

        return (", ".join(outputs), "")
