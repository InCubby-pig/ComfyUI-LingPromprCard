# ==========================================
# 灵感 PromptCard 抽卡节点（独立版）
# ==========================================

from .promptcard.PromptCardCostume import LingPromptCardCostume
from .promptcard.PromptCardDanbooruSelectors import (
    NODE_CLASS_MAPPINGS as DANBOORU_NODE_CLASS_MAPPINGS,
)
from .promptcard.PromptCardDanbooruSelectors import (
    NODE_DISPLAY_NAME_MAPPINGS as DANBOORU_NODE_DISPLAY_NAME_MAPPINGS,
)
from .promptcard.PromptCardFraming import LingPromptCardFraming
from .promptcard.PromptCardR18Scene import LingPromptCardR18Scene
from .promptcard.PromptCardScene import LingPromptCardScene


NODE_CLASS_MAPPINGS = {
    "LingPromptCardCostume": LingPromptCardCostume,
    "LingPromptCardFraming": LingPromptCardFraming,
    "LingPromptCardR18Scene": LingPromptCardR18Scene,
    "LingPromptCardScene": LingPromptCardScene,
}
NODE_CLASS_MAPPINGS.update(DANBOORU_NODE_CLASS_MAPPINGS)

NODE_DISPLAY_NAME_MAPPINGS = {
    "LingPromptCardCostume": "灵感抽卡-服装",
    "LingPromptCardFraming": "灵感抽卡-构图",
    "LingPromptCardR18Scene": "灵感抽卡-R18情景",
    "LingPromptCardScene": "灵感抽卡-场景",
}
NODE_DISPLAY_NAME_MAPPINGS.update(DANBOORU_NODE_DISPLAY_NAME_MAPPINGS)

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
