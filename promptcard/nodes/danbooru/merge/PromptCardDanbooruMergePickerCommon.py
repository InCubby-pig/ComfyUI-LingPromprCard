import random
from typing import Dict, List

from .PromptCardDanbooruMergeCommon import LingPromptCardMergeBase


class LingPromptCardMergePickerBase(LingPromptCardMergeBase):
    """Danbooru 合并提示词选择器公共逻辑。"""

    PICKED_TAGS_INPUT_KEY = "已选tags"

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
            cls.PICKED_TAGS_INPUT_KEY: (
                "STRING",
                {
                    "default": "",
                    "multiline": False,
                },
            ),
        }

        for row in lists:
            raw_options = row["item_options"]
            item_options: List[str] = []
            for option in raw_options:
                if option == "(不输出)":
                    continue
                if option not in item_options:
                    item_options.append(option)
            if "(随机)" not in item_options:
                item_options.insert(0, "(随机)")
            required_inputs[row["input_key"]] = (
                item_options,
                {"default": "(随机)"},
            )

        return {"required": required_inputs}

    @classmethod
    def _parse_selected_tags(cls, value: object) -> List[str]:
        if not isinstance(value, str):
            return []
        tags: List[str] = []
        seen = set()
        for raw in value.split(","):
            tag = raw.strip()
            if not tag or tag in seen:
                continue
            seen.add(tag)
            tags.append(tag)
        return tags

    @classmethod
    def _collect_fallback_tags(cls, kwargs: Dict[str, object], lists: List[Dict[str, object]]) -> List[str]:
        # 兜底：当运行环境没有前端扩展时，仍支持按每行当前选择输出。
        tags: List[str] = []
        seen = set()
        for row in lists:
            input_key = str(row["input_key"])
            raw_input_key = str(row.get("raw_input_key", input_key))
            value = kwargs.get(input_key, kwargs.get(raw_input_key, "(随机)"))
            if value == "(不输出)":
                continue

            if value == "(随机)":
                candidates = row.get("tags", [])
                if candidates:
                    chosen = random.choice(candidates)
                    if chosen not in seen:
                        seen.add(chosen)
                        tags.append(chosen)
                continue

            mapped = row["display_to_tag"].get(value)
            if mapped:
                if mapped not in seen:
                    seen.add(mapped)
                    tags.append(mapped)
                continue

            if value in row["raw_to_tag"] and value not in seen:
                seen.add(value)
                tags.append(value)

        return tags

    def draw_prompt(self, **kwargs) -> Dict[str, object]:
        if not kwargs.get("总开关", True):
            return self.__class__._build_result("", "", enabled=False)

        selected_raw = kwargs.get(self.PICKED_TAGS_INPUT_KEY, "")
        selected_tags = self.__class__._parse_selected_tags(selected_raw)
        if not selected_tags:
            config = self.__class__._get_config()
            selected_tags = self.__class__._collect_fallback_tags(kwargs, config["lists"])
        return self.__class__._build_result(", ".join(selected_tags), "")
