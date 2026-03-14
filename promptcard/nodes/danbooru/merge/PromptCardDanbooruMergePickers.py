from .PromptCardDanbooruMergePickerCommon import LingPromptCardMergePickerBase
from ....data.danbooru_merge_index import DANBOORU_MERGE_SELECTOR_DATA, DANBOORU_MERGE_SELECTOR_SPECS


NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


def _to_picker_class_name(merge_class_name: str) -> str:
    prefix = "LingPromptCardDanbooruMerge"
    picker_prefix = "LingPromptCardDanbooruMergePicker"
    if merge_class_name.startswith(prefix):
        return merge_class_name.replace(prefix, picker_prefix, 1)
    return f"{merge_class_name}Picker"


def _to_picker_display_name(merge_display_name: str) -> str:
    prefix = "Danbooru-合并-"
    picker_prefix = "Danbooru-选择器-"
    if merge_display_name.startswith(prefix):
        return merge_display_name.replace(prefix, picker_prefix, 1)
    return f"{merge_display_name}-选择器"


for spec in DANBOORU_MERGE_SELECTOR_SPECS:
    node_key = str(spec["node_key"])
    merge_class_name = str(spec["class_name"])
    merge_display_name = str(spec["display_name"])

    class_name = _to_picker_class_name(merge_class_name)
    display_name = _to_picker_display_name(merge_display_name)

    cls = type(
        class_name,
        (LingPromptCardMergePickerBase,),
        {
            "NODE_KEY": node_key,
            "CATEGORY": "lingpromptcard/cards/danbooru/merge/picker",
            "DATA_SOURCE": DANBOORU_MERGE_SELECTOR_DATA,
            "__doc__": f"Danbooru 合并提示词选择器: {display_name}",
        },
    )
    cls.__module__ = __name__

    NODE_CLASS_MAPPINGS[class_name] = cls
    NODE_DISPLAY_NAME_MAPPINGS[class_name] = display_name
