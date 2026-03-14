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
const PREVIEW_WIDGET_HEIGHT = 170;
const PREVIEW_NODE_MIN_HEIGHT = 420;

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

function applyPreviewElementStyle(el) {
    if (!el) {
        return;
    }
    el.readOnly = true;
    el.disabled = false;
    el.wrap = "soft";
    el.spellcheck = false;
    el.style.width = "100%";
    el.style.minHeight = `${PREVIEW_WIDGET_HEIGHT - 18}px`;
    el.style.height = `${PREVIEW_WIDGET_HEIGHT - 18}px`;
    el.style.resize = "none";
    el.style.boxSizing = "border-box";
    el.style.overflowY = "auto";
    el.style.whiteSpace = "pre-wrap";
    el.style.lineHeight = "1.35";
    el.style.fontFamily = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
    el.style.fontSize = "12px";
}

function normalizeTagDisplay(value) {
    if (typeof value !== "string") {
        return "";
    }
    let text = value.trim();
    if (!text) {
        return "";
    }
    const duplicateHint = text.match(/\s+\[([^\]]+)\]\s*$/);
    if (duplicateHint && duplicateHint[1]) {
        text = duplicateHint[1].trim();
    }
    const pipeIndex = text.lastIndexOf(" | ");
    if (pipeIndex >= 0) {
        text = text.slice(pipeIndex + 3).trim();
    }
    return text;
}

function hash32(seed, salt) {
    const seedNum = Number.isFinite(Number(seed)) ? Number(seed) : 0;
    let x = (seedNum >>> 0) ^ (salt >>> 0);
    x ^= x >>> 16;
    x = Math.imul(x, 0x85ebca6b);
    x ^= x >>> 13;
    x = Math.imul(x, 0xc2b2ae35);
    x ^= x >>> 16;
    return x >>> 0;
}

function pickDeterministic(items, seed, salt) {
    if (!Array.isArray(items) || items.length === 0) {
        return "";
    }
    const idx = hash32(seed, salt) % items.length;
    return items[idx] || "";
}

function getWidgetOptions(widget) {
    const values = widget?.options?.values;
    return Array.isArray(values) ? values : [];
}

function parseNegativeLine(text) {
    if (typeof text !== "string") {
        return "";
    }
    const line = text.split("\n").find((v) => v.startsWith("负面:"));
    if (!line) {
        return "";
    }
    return line.slice(3).trim();
}

function buildRealtimePreviewText(node) {
    const switchWidget = getWidgetByName(node, "总开关");
    if (switchWidget && switchWidget.value === false) {
        return "正面: (节点关闭)\n负面: (节点关闭)";
    }

    const seedWidget = getWidgetByName(node, "seed");
    const seed = Number(seedWidget?.value ?? 0);
    const modeWidget = getWidgetByName(node, "模式选择");
    const categoryWidget = getWidgetByName(node, "分类");
    const currentPreviewWidget = getWidgetByName(node, PREVIEW_WIDGET_NAME);
    const currentNeg = parseNegativeLine(currentPreviewWidget?.value);
    let pos = "";
    let neg = currentNeg || "(需执行后更新)";

    if (modeWidget && categoryWidget) {
        const labels = getCategoryLabels(categoryWidget);
        const itemWidgets = labels
            .map((name) => getWidgetByName(node, name))
            .filter((w) => !!w);

        const explicit = itemWidgets.find((w) => w.value !== "(随机)");
        let sourceWidget = null;
        if (modeWidget.value !== "🔓 完全随机") {
            if (explicit) {
                sourceWidget = explicit;
            } else if (categoryWidget.value !== "(不指定)") {
                sourceWidget = getWidgetByName(node, categoryWidget.value);
            }
        }

        if (sourceWidget && sourceWidget.value !== "(随机)") {
            pos = normalizeTagDisplay(sourceWidget.value);
        } else {
            let candidates = [];
            if (sourceWidget) {
                candidates = getWidgetOptions(sourceWidget)
                    .filter((v) => v !== "(随机)")
                    .map(normalizeTagDisplay)
                    .filter((v) => !!v);
                pos = pickDeterministic(candidates, seed, sourceWidget.name.length || 1);
            } else {
                for (const w of itemWidgets) {
                    const values = getWidgetOptions(w)
                        .filter((v) => v !== "(随机)")
                        .map(normalizeTagDisplay)
                        .filter((v) => !!v);
                    candidates.push(...values);
                }
                pos = pickDeterministic(candidates, seed, 0x9e3779b9);
            }
        }
    } else {
        const widgets = Array.isArray(node?.widgets) ? node.widgets : [];
        const mergeRows = widgets.filter((w) => {
            const values = getWidgetOptions(w);
            return values.includes("(不输出)") && values.includes("(随机)");
        });

        const outputs = [];
        for (let i = 0; i < mergeRows.length; i += 1) {
            const row = mergeRows[i];
            const value = row.value;
            if (value === "(不输出)") {
                continue;
            }
            if (value === "(随机)") {
                const candidates = getWidgetOptions(row)
                    .filter((v) => v !== "(不输出)" && v !== "(随机)")
                    .map(normalizeTagDisplay)
                    .filter((v) => !!v);
                const picked = pickDeterministic(candidates, seed, i + 1);
                if (picked) {
                    outputs.push(picked);
                }
                continue;
            }
            const normalized = normalizeTagDisplay(value);
            if (normalized) {
                outputs.push(normalized);
            }
        }
        pos = outputs.join(", ");
        neg = "(空)";
    }

    return `正面: ${pos || "(空)"}\n负面: ${neg}`;
}

function extractPreviewFromMessage(message) {
    const queue = [message];
    const visited = new Set();

    for (let depth = 0; depth < 5 && queue.length > 0; depth += 1) {
        const currentLevel = queue.splice(0, queue.length);
        for (const payload of currentLevel) {
            if (!payload || typeof payload !== "object") {
                continue;
            }
            if (visited.has(payload)) {
                continue;
            }
            visited.add(payload);

            if (Object.prototype.hasOwnProperty.call(payload, PREVIEW_UI_KEY)) {
                return { found: true, text: normalizePreviewText(payload[PREVIEW_UI_KEY]) };
            }

            const ui = payload.ui;
            if (ui && typeof ui === "object" && Object.prototype.hasOwnProperty.call(ui, PREVIEW_UI_KEY)) {
                return { found: true, text: normalizePreviewText(ui[PREVIEW_UI_KEY]) };
            }

            for (const value of Object.values(payload)) {
                if (value && typeof value === "object") {
                    queue.push(value);
                }
            }
        }
    }

    return { found: false, text: "" };
}

function ensurePreviewWidget(node) {
    if (!node) {
        return null;
    }
    const existing = getWidgetByName(node, PREVIEW_WIDGET_NAME);
    if (existing) {
        if (existing.__lingPreviewTextArea) {
            applyPreviewElementStyle(existing.__lingPreviewTextArea);
        }
        if (existing.inputEl) {
            applyPreviewElementStyle(existing.inputEl);
        }
        existing.computeSize = (width) => [width, PREVIEW_WIDGET_HEIGHT];
        if (Array.isArray(node.size)) {
            node.size[1] = Math.max(node.size[1] || 0, PREVIEW_NODE_MIN_HEIGHT);
        }
        return existing;
    }

    let widget = null;
    if (typeof node.addDOMWidget === "function") {
        const textarea = document.createElement("textarea");
        textarea.value = PREVIEW_DEFAULT_TEXT;
        applyPreviewElementStyle(textarea);
        widget = node.addDOMWidget(
            PREVIEW_WIDGET_NAME,
            "textarea",
            textarea,
            {
                serialize: false,
                hideOnZoom: false,
                getValue: () => textarea.value,
                setValue: (v) => {
                    textarea.value = typeof v === "string" ? v : "";
                },
            },
        );
        if (widget) {
            widget.__lingPreviewTextArea = textarea;
        }
    }

    if (!widget && typeof node.addWidget === "function") {
        widget = node.addWidget(
            "text",
            PREVIEW_WIDGET_NAME,
            PREVIEW_DEFAULT_TEXT,
            null,
            { multiline: true },
        );
        if (widget?.inputEl) {
            applyPreviewElementStyle(widget.inputEl);
        }
    }

    if (!widget) {
        return null;
    }

    widget.options = { ...(widget.options || {}), multiline: true, serialize: false };
    widget.computeSize = (width) => [width, PREVIEW_WIDGET_HEIGHT];
    if (Array.isArray(node.size)) {
        node.size[1] = Math.max(node.size[1] || 0, PREVIEW_NODE_MIN_HEIGHT);
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
    if (widget.__lingPreviewTextArea) {
        widget.__lingPreviewTextArea.value = nextText;
    }
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
            updatePreviewWidget(this, buildRealtimePreviewText(this));
            return result;
        };

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function (...args) {
            const result = originalOnNodeCreated ? originalOnNodeCreated.apply(this, args) : undefined;
            ensurePreviewWidget(this);
            updatePreviewWidget(this, buildRealtimePreviewText(this));
            return result;
        };

        const originalOnWidgetChanged = nodeType.prototype.onWidgetChanged;
        nodeType.prototype.onWidgetChanged = function (name, value, oldValue, widget) {
            const result = originalOnWidgetChanged
                ? originalOnWidgetChanged.call(this, name, value, oldValue, widget)
                : undefined;

            if (this.__lingPromptCardSyncing) {
                if (name !== PREVIEW_WIDGET_NAME) {
                    updatePreviewWidget(this, buildRealtimePreviewText(this));
                }
                return result;
            }

            const categoryWidget = getWidgetByName(this, "分类");
            if (!categoryWidget) {
                if (name !== PREVIEW_WIDGET_NAME) {
                    updatePreviewWidget(this, buildRealtimePreviewText(this));
                }
                return result;
            }

            const categoryLabels = getCategoryLabels(categoryWidget);
            if (!categoryLabels.includes(name)) {
                if (name !== PREVIEW_WIDGET_NAME) {
                    updatePreviewWidget(this, buildRealtimePreviewText(this));
                }
                return result;
            }
            if (value === "(随机)") {
                if (name !== PREVIEW_WIDGET_NAME) {
                    updatePreviewWidget(this, buildRealtimePreviewText(this));
                }
                return result;
            }
            if (categoryWidget.value === name) {
                if (name !== PREVIEW_WIDGET_NAME) {
                    updatePreviewWidget(this, buildRealtimePreviewText(this));
                }
                return result;
            }

            this.__lingPromptCardSyncing = true;
            try {
                categoryWidget.value = name;
                this.setDirtyCanvas?.(true, true);
            } finally {
                this.__lingPromptCardSyncing = false;
            }
            if (name !== PREVIEW_WIDGET_NAME) {
                updatePreviewWidget(this, buildRealtimePreviewText(this));
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
