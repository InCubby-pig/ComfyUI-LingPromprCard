# ==========================================
# 灵感 PromptCard 抽卡节点（独立版）
# ==========================================

from .promptcard.nodes.basic.PromptCardCostume import LingPromptCardCostume
from .promptcard.nodes.danbooru.split.PromptCardDanbooruSelectors import (
    NODE_CLASS_MAPPINGS as DANBOORU_NODE_CLASS_MAPPINGS,
)
from .promptcard.nodes.danbooru.split.PromptCardDanbooruSelectors import (
    NODE_DISPLAY_NAME_MAPPINGS as DANBOORU_NODE_DISPLAY_NAME_MAPPINGS,
)
from .promptcard.nodes.danbooru.merge.PromptCardDanbooruMergeSelectors import (
    NODE_CLASS_MAPPINGS as DANBOORU_MERGE_NODE_CLASS_MAPPINGS,
)
from .promptcard.nodes.danbooru.merge.PromptCardDanbooruMergeSelectors import (
    NODE_DISPLAY_NAME_MAPPINGS as DANBOORU_MERGE_NODE_DISPLAY_NAME_MAPPINGS,
)
from .promptcard.nodes.danbooru.merge.PromptCardDanbooruMergePickers import (
    NODE_CLASS_MAPPINGS as DANBOORU_MERGE_PICKER_NODE_CLASS_MAPPINGS,
)
from .promptcard.nodes.danbooru.merge.PromptCardDanbooruMergePickers import (
    NODE_DISPLAY_NAME_MAPPINGS as DANBOORU_MERGE_PICKER_NODE_DISPLAY_NAME_MAPPINGS,
)
from .promptcard.nodes.basic.PromptCardFraming import LingPromptCardFraming
from .promptcard.nodes.basic.PromptCardR18Scene import LingPromptCardR18Scene
from .promptcard.nodes.basic.PromptCardScene import LingPromptCardScene


NODE_CLASS_MAPPINGS = {
    "LingPromptCardCostume": LingPromptCardCostume,
    "LingPromptCardFraming": LingPromptCardFraming,
    "LingPromptCardR18Scene": LingPromptCardR18Scene,
    "LingPromptCardScene": LingPromptCardScene,
}
NODE_CLASS_MAPPINGS.update(DANBOORU_NODE_CLASS_MAPPINGS)
NODE_CLASS_MAPPINGS.update(DANBOORU_MERGE_NODE_CLASS_MAPPINGS)
NODE_CLASS_MAPPINGS.update(DANBOORU_MERGE_PICKER_NODE_CLASS_MAPPINGS)

NODE_DISPLAY_NAME_MAPPINGS = {
    "LingPromptCardCostume": "灵感抽卡-服装",
    "LingPromptCardFraming": "灵感抽卡-构图",
    "LingPromptCardR18Scene": "灵感抽卡-R18情景",
    "LingPromptCardScene": "灵感抽卡-场景",
}
NODE_DISPLAY_NAME_MAPPINGS.update(DANBOORU_NODE_DISPLAY_NAME_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(DANBOORU_MERGE_NODE_DISPLAY_NAME_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(DANBOORU_MERGE_PICKER_NODE_DISPLAY_NAME_MAPPINGS)

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
