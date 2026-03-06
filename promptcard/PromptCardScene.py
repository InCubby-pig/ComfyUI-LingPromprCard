from .PromptCardCommon import LingPromptCardBase


class LingPromptCardScene(LingPromptCardBase):
    NODE_KEY = "scene_hint"
    CATEGORY = "lingpromptcard/cards"


NODE_CLASS_MAPPINGS = {
    "LingPromptCardScene": LingPromptCardScene,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LingPromptCardScene": "灵感抽卡-场景",
}
