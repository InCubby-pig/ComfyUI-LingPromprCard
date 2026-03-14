from .PromptCardCommon import LingPromptCardBase
from .PromptCardDanbooruData import DANBOORU_TAG_DATA


class LingPromptCardDanbooruCopyrightCharacter(LingPromptCardBase):
    NODE_KEY = "danbooru_copyright_character"
    CATEGORY = "lingpromptcard/cards"
    DATA_SOURCE = DANBOORU_TAG_DATA


NODE_CLASS_MAPPINGS = {
    "LingPromptCardDanbooruCopyrightCharacter": LingPromptCardDanbooruCopyrightCharacter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LingPromptCardDanbooruCopyrightCharacter": "Danbooru标签-版权与角色",
}
