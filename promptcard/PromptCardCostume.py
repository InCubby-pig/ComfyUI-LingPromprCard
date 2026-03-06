from .PromptCardCommon import LingPromptCardBase


class LingPromptCardCostume(LingPromptCardBase):
    NODE_KEY = "costume"
    CATEGORY = "lingpromptcard/cards"


NODE_CLASS_MAPPINGS = {
    "LingPromptCardCostume": LingPromptCardCostume,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LingPromptCardCostume": "灵感抽卡-服装",
}
