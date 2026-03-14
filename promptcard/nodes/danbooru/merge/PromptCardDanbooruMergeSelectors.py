from .PromptCardDanbooruMergeCommon import LingPromptCardMergeBase
from ....data.danbooru_merge_index import DANBOORU_MERGE_SELECTOR_DATA, DANBOORU_MERGE_SELECTOR_SPECS


NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


for spec in DANBOORU_MERGE_SELECTOR_SPECS:
    class_name = str(spec["class_name"])
    node_key = str(spec["node_key"])
    display_name = str(spec["display_name"])

    cls = type(
        class_name,
        (LingPromptCardMergeBase,),
        {
            "NODE_KEY": node_key,
            "CATEGORY": "lingpromptcard/cards",
            "DATA_SOURCE": DANBOORU_MERGE_SELECTOR_DATA,
            "__doc__": f"Danbooru 合并抽卡器: {display_name}",
        },
    )
    cls.__module__ = __name__

    NODE_CLASS_MAPPINGS[class_name] = cls
    NODE_DISPLAY_NAME_MAPPINGS[class_name] = display_name
