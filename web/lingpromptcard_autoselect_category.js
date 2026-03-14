import { app } from "../../scripts/app.js";

const TARGET_NODE_NAMES = new Set([
    "LingPromptCardCostume",
    "LingPromptCardFraming",
    "LingPromptCardR18Scene",
    "LingPromptCardScene",
]);
const PREVIEW_WIDGET_NAME = "tags预览";
const PREVIEW_UI_KEY = "lingpromptcard_tags_preview";
const PREVIEW_DEFAULT_TEXT = "正面: (等待执行)\n负面: (等待执行)";

function isTargetNodeName(name) {
    if (!name) {
        return false;
    }
    if (TARGET_NODE_NAMES.has(name)) {
        return true;
    }
    return (
        name.startsWith("LingPromptCardDanbooruSelector")
        || name.startsWith("LingPromptCardDanbooruMerge")
    );
}

function getWidgetByName(node, name) {
    if (!node?.widgets) {
        return null;
    }
    return node.widgets.find((widget) => widget?.name === name) || null;
}

function normalizePreviewText(value) {
    if (typeof value === "string") {
        return value;
    }
    if (Array.isArray(value) && typeof value[0] === "string") {
        return value[0];
    }
    return "";
}

function extractPreviewFromMessage(message) {
    if (!message || typeof message !== "object") {
        return { found: false, text: "" };
    }
    if (Object.prototype.hasOwnProperty.call(message, PREVIEW_UI_KEY)) {
        return { found: true, text: normalizePreviewText(message[PREVIEW_UI_KEY]) };
    }
    const ui = message.ui;
    if (ui && typeof ui === "object" && Object.prototype.hasOwnProperty.call(ui, PREVIEW_UI_KEY)) {
        return { found: true, text: normalizePreviewText(ui[PREVIEW_UI_KEY]) };
    }
    return { found: false, text: "" };
}

function ensurePreviewWidget(node) {
    if (!node?.addWidget) {
        return null;
    }
    const existing = getWidgetByName(node, PREVIEW_WIDGET_NAME);
    if (existing) {
        if (existing.inputEl) {
            existing.inputEl.readOnly = true;
            existing.inputEl.disabled = true;
        }
        return existing;
    }

    const widget = node.addWidget(
        "text",
        PREVIEW_WIDGET_NAME,
        PREVIEW_DEFAULT_TEXT,
        null,
        { multiline: true },
    );
    if (!widget) {
        return null;
    }

    widget.options = { ...(widget.options || {}), multiline: true, serialize: false };
    widget.disabled = true;
    if (widget.inputEl) {
        widget.inputEl.readOnly = true;
        widget.inputEl.disabled = true;
    }
    return widget;
}

function updatePreviewWidget(node, text) {
    const widget = ensurePreviewWidget(node);
    if (!widget) {
        return;
    }
    const nextText = typeof text === "string" && text.length > 0 ? text : PREVIEW_DEFAULT_TEXT;
    if (widget.value === nextText) {
        return;
    }
    widget.value = nextText;
    if (widget.inputEl) {
        widget.inputEl.value = nextText;
    }
    node?.setDirtyCanvas?.(true, true);
}

function getCategoryLabels(categoryWidget) {
    const values = categoryWidget?.options?.values;
    if (!Array.isArray(values)) {
        return [];
    }
    return values.filter((label) => label !== "(不指定)");
}

function syncCategoryBySelectedItem(node) {
    const categoryWidget = getWidgetByName(node, "分类");
    if (!categoryWidget) {
        return;
    }

    const categoryLabels = getCategoryLabels(categoryWidget);
    for (const label of categoryLabels) {
        const itemWidget = getWidgetByName(node, label);
        if (!itemWidget) {
            continue;
        }
        if (itemWidget.value !== "(随机)") {
            categoryWidget.value = label;
            node?.setDirtyCanvas?.(true, true);
            return;
        }
    }
}

app.registerExtension({
    name: "LingPromptCard.AutoSelectCategory",
    beforeRegisterNodeDef(nodeType, nodeData) {
        if (!isTargetNodeName(nodeData?.name)) {
            return;
        }
        if (nodeType.prototype.__lingPromptCardAutoSelectPatched) {
            return;
        }
        nodeType.prototype.__lingPromptCardAutoSelectPatched = true;

        const originalOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (...args) {
            const result = originalOnConfigure ? originalOnConfigure.apply(this, args) : undefined;
            ensurePreviewWidget(this);
            syncCategoryBySelectedItem(this);
            return result;
        };

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function (...args) {
            const result = originalOnNodeCreated ? originalOnNodeCreated.apply(this, args) : undefined;
            ensurePreviewWidget(this);
            return result;
        };

        const originalOnWidgetChanged = nodeType.prototype.onWidgetChanged;
        nodeType.prototype.onWidgetChanged = function (name, value, oldValue, widget) {
            const result = originalOnWidgetChanged
                ? originalOnWidgetChanged.call(this, name, value, oldValue, widget)
                : undefined;

            if (this.__lingPromptCardSyncing) {
                return result;
            }

            const categoryWidget = getWidgetByName(this, "分类");
            if (!categoryWidget) {
                return result;
            }

            const categoryLabels = getCategoryLabels(categoryWidget);
            if (!categoryLabels.includes(name)) {
                return result;
            }
            if (value === "(随机)") {
                return result;
            }
            if (categoryWidget.value === name) {
                return result;
            }

            this.__lingPromptCardSyncing = true;
            try {
                categoryWidget.value = name;
                this.setDirtyCanvas?.(true, true);
            } finally {
                this.__lingPromptCardSyncing = false;
            }
            return result;
        };

        const originalOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            const result = originalOnExecuted ? originalOnExecuted.call(this, message) : undefined;
            const preview = extractPreviewFromMessage(message);
            if (preview.found) {
                updatePreviewWidget(this, preview.text);
            }
            return result;
        };
    },
});
