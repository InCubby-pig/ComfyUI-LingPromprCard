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
            item_options = row["item_options"]
            default_value = "(不输出)" if "(不输出)" in item_options else item_options[0]
            required_inputs[row["input_key"]] = (
                item_options,
                {"default": default_value},
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
            value = kwargs.get(input_key, kwargs.get(raw_input_key, "(不输出)"))
            if value in ("(不输出)", "(随机)"):
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
