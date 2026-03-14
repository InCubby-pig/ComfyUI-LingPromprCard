# ==========================================
# 灵感 PromptCard 抽卡节点（独立版）
# ==========================================

from .promptcard.PromptCardCostume import LingPromptCardCostume
from .promptcard.PromptCardDanbooruCopyrightCharacter import LingPromptCardDanbooruCopyrightCharacter
from .promptcard.PromptCardDanbooruMetatags import LingPromptCardDanbooruMetatags
from .promptcard.PromptCardDanbooruSexR18 import LingPromptCardDanbooruSexR18
from .promptcard.PromptCardDanbooruVisual import LingPromptCardDanbooruVisual
from .promptcard.PromptCardFraming import LingPromptCardFraming
from .promptcard.PromptCardR18Scene import LingPromptCardR18Scene
from .promptcard.PromptCardScene import LingPromptCardScene


NODE_CLASS_MAPPINGS = {
    "LingPromptCardCostume": LingPromptCardCostume,
    "LingPromptCardDanbooruCopyrightCharacter": LingPromptCardDanbooruCopyrightCharacter,
    "LingPromptCardDanbooruMetatags": LingPromptCardDanbooruMetatags,
    "LingPromptCardDanbooruSexR18": LingPromptCardDanbooruSexR18,
    "LingPromptCardDanbooruVisual": LingPromptCardDanbooruVisual,
    "LingPromptCardFraming": LingPromptCardFraming,
    "LingPromptCardR18Scene": LingPromptCardR18Scene,
    "LingPromptCardScene": LingPromptCardScene,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LingPromptCardCostume": "灵感抽卡-服装",
    "LingPromptCardDanbooruCopyrightCharacter": "Danbooru标签-版权与角色",
    "LingPromptCardDanbooruMetatags": "Danbooru标签-Metatags",
    "LingPromptCardDanbooruSexR18": "Danbooru标签-Sex/R18",
    "LingPromptCardDanbooruVisual": "Danbooru标签-视觉",
    "LingPromptCardFraming": "灵感抽卡-构图",
    "LingPromptCardR18Scene": "灵感抽卡-R18情景",
    "LingPromptCardScene": "灵感抽卡-场景",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
