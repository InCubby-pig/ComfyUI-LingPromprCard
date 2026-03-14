from .PromptCardCommon import LingPromptCardBase


class LingPromptCardR18Scene(LingPromptCardBase):
    NODE_KEY = "r18_scene"
    CATEGORY = "lingpromptcard/cards/basic"


NODE_CLASS_MAPPINGS = {
    "LingPromptCardR18Scene": LingPromptCardR18Scene,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LingPromptCardR18Scene": "灵感抽卡-R18情景",
}
