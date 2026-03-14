from .PromptCardCommon import LingPromptCardBase


class LingPromptCardFraming(LingPromptCardBase):
    NODE_KEY = "framing"
    CATEGORY = "lingpromptcard/cards"


NODE_CLASS_MAPPINGS = {
    "LingPromptCardFraming": LingPromptCardFraming,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LingPromptCardFraming": "灵感抽卡-构图",
}
