from .PromptCardCommon import LingPromptCardBase
from .PromptCardDanbooruData import DANBOORU_TAG_DATA


class LingPromptCardDanbooruSexR18(LingPromptCardBase):
    NODE_KEY = "danbooru_sex_r18"
    CATEGORY = "lingpromptcard/cards"
    DATA_SOURCE = DANBOORU_TAG_DATA


NODE_CLASS_MAPPINGS = {
    "LingPromptCardDanbooruSexR18": LingPromptCardDanbooruSexR18,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LingPromptCardDanbooruSexR18": "Danbooru标签-Sex/R18",
}
