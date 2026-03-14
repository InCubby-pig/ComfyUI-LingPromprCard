from .PromptCardCommon import LingPromptCardBase
from .PromptCardDanbooruData import DANBOORU_TAG_DATA


class LingPromptCardDanbooruVisual(LingPromptCardBase):
    NODE_KEY = "danbooru_visual"
    CATEGORY = "lingpromptcard/cards"
    DATA_SOURCE = DANBOORU_TAG_DATA


NODE_CLASS_MAPPINGS = {
    "LingPromptCardDanbooruVisual": LingPromptCardDanbooruVisual,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LingPromptCardDanbooruVisual": "Danbooru标签-视觉",
}
