from .PromptCardCommon import LingPromptCardBase
from .PromptCardDanbooruData import DANBOORU_TAG_DATA


class LingPromptCardDanbooruMetatags(LingPromptCardBase):
    NODE_KEY = "danbooru_metatags"
    CATEGORY = "lingpromptcard/cards"
    DATA_SOURCE = DANBOORU_TAG_DATA


NODE_CLASS_MAPPINGS = {
    "LingPromptCardDanbooruMetatags": LingPromptCardDanbooruMetatags,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LingPromptCardDanbooruMetatags": "Danbooru标签-Metatags",
}
