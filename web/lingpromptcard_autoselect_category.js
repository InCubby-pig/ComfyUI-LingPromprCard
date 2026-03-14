import { app } from "../../scripts/app.js";

const TARGET_NODE_NAMES = new Set([
    "LingPromptCardCostume",
    "LingPromptCardFraming",
    "LingPromptCardR18Scene",
    "LingPromptCardScene",
]);
const LEGACY_PREVIEW_WIDGET_NAME = "tags预览";
const PREVIEW_POS_WIDGET_NAME = "正面tags预览";
const PREVIEW_NEG_WIDGET_NAME = "负面tags预览";
const PREVIEW_UI_KEY = "lingpromptcard_tags_preview";
const PREVIEW_WIDGET_HEIGHT = 150;
const PREVIEW_NODE_MIN_HEIGHT = 560;

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

function getWidgetOptions(widget) {
    const values = widget?.options?.values;
    return Array.isArray(values) ? values : [];
}

function getWidgetStringValue(widget) {
    if (!widget) {
        return "";
    }
    if (widget.__lingPreviewTextArea && typeof widget.__lingPreviewTextArea.value === "string") {
        return widget.__lingPreviewTextArea.value;
    }
    return typeof widget.value === "string" ? widget.value : "";
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

function normalizeOutputTagText(value) {
    if (typeof value !== "string") {
        return "";
    }
    let text = value.trim();
    while (text.endsWith(",")) {
        text = text.slice(0, -1).trimEnd();
    }
    if (
        text === "(空)"
        || text === "(节点关闭)"
        || text === "(等待执行)"
        || text === "(需执行后更新)"
    ) {
        return "";
    }
    return text;
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
    return normalizeOutputTagText(text);
}

function applyPreviewElementStyle(el, height) {
    if (!el) {
        return;
    }
    el.readOnly = true;
    el.disabled = false;
    el.wrap = "soft";
    el.spellcheck = false;
    el.style.width = "100%";
    el.style.minHeight = `${height - 18}px`;
    el.style.height = `${height - 18}px`;
    el.style.resize = "none";
    el.style.boxSizing = "border-box";
    el.style.overflowY = "auto";
    el.style.whiteSpace = "pre-wrap";
    el.style.lineHeight = "1.35";
    el.style.fontFamily = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
    el.style.fontSize = "12px";
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

function ensureNodeHeight(node) {
    if (!Array.isArray(node?.size)) {
        return;
    }
    node.size[1] = Math.max(node.size[1] || 0, PREVIEW_NODE_MIN_HEIGHT);
}

function removeLegacyPreviewWidget(node) {
    if (!node?.widgets) {
        return;
    }
    const index = node.widgets.findIndex((widget) => widget?.name === LEGACY_PREVIEW_WIDGET_NAME);
    if (index < 0) {
        return;
    }
    const legacy = node.widgets[index];
    node.widgets.splice(index, 1);
    if (legacy?.inputEl?.remove) {
        legacy.inputEl.remove();
    }
    if (legacy?.__lingPreviewTextArea?.remove) {
        legacy.__lingPreviewTextArea.remove();
    }
}

function ensurePreviewWidget(node, name, height) {
    if (!node) {
        return null;
    }
    const existing = getWidgetByName(node, name);
    if (existing) {
        if (existing.__lingPreviewTextArea) {
            applyPreviewElementStyle(existing.__lingPreviewTextArea, height);
        }
        if (existing.inputEl) {
            applyPreviewElementStyle(existing.inputEl, height);
        }
        existing.computeSize = (width) => [width, height];
        ensureNodeHeight(node);
        return existing;
    }

    let widget = null;
    if (typeof node.addDOMWidget === "function") {
        const textarea = document.createElement("textarea");
        textarea.value = "";
        applyPreviewElementStyle(textarea, height);
        widget = node.addDOMWidget(
            name,
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
        widget = node.addWidget("text", name, "", null, { multiline: true });
        if (widget?.inputEl) {
            applyPreviewElementStyle(widget.inputEl, height);
        }
    }

    if (!widget) {
        return null;
    }

    widget.options = { ...(widget.options || {}), multiline: true, serialize: false };
    widget.computeSize = (width) => [width, height];
    ensureNodeHeight(node);
    return widget;
}

function ensurePreviewWidgets(node) {
    removeLegacyPreviewWidget(node);
    const posWidget = ensurePreviewWidget(node, PREVIEW_POS_WIDGET_NAME, PREVIEW_WIDGET_HEIGHT);
    const negWidget = ensurePreviewWidget(node, PREVIEW_NEG_WIDGET_NAME, PREVIEW_WIDGET_HEIGHT);
    return { posWidget, negWidget };
}

function updateSinglePreviewWidget(widget, value) {
    if (!widget) {
        return;
    }
    const nextText = normalizeOutputTagText(value);
    if (widget.value !== nextText) {
        widget.value = nextText;
    }
    if (widget.__lingPreviewTextArea && widget.__lingPreviewTextArea.value !== nextText) {
        widget.__lingPreviewTextArea.value = nextText;
    }
    if (widget.inputEl && widget.inputEl.value !== nextText) {
        widget.inputEl.value = nextText;
    }
}

function updatePreviewWidgets(node, preview) {
    const { posWidget, negWidget } = ensurePreviewWidgets(node);
    if (!posWidget || !negWidget) {
        return;
    }
    updateSinglePreviewWidget(posWidget, preview?.pos || "");
    updateSinglePreviewWidget(negWidget, preview?.neg || "");
    node?.setDirtyCanvas?.(true, true);
}

function parsePreviewPayload(value) {
    if (Array.isArray(value)) {
        if (value.length >= 2 && typeof value[0] === "string" && typeof value[1] === "string") {
            return {
                pos: normalizeOutputTagText(value[0]),
                neg: normalizeOutputTagText(value[1]),
            };
        }
        if (value.length >= 1) {
            return parsePreviewPayload(value[0]);
        }
        return { pos: "", neg: "" };
    }

    if (value && typeof value === "object") {
        if (typeof value.pos === "string" || typeof value.neg === "string") {
            return {
                pos: normalizeOutputTagText(value.pos || ""),
                neg: normalizeOutputTagText(value.neg || ""),
            };
        }
        if (typeof value.positive === "string" || typeof value.negative === "string") {
            return {
                pos: normalizeOutputTagText(value.positive || ""),
                neg: normalizeOutputTagText(value.negative || ""),
            };
        }
        if (Array.isArray(value.result) && value.result.length >= 2) {
            return parsePreviewPayload(value.result);
        }
    }

    const text = normalizePreviewText(value).trim();
    if (!text) {
        return { pos: "", neg: "" };
    }

    const lines = text.split("\n").map((line) => line.trim());
    let pos = "";
    let neg = "";
    for (const line of lines) {
        if (line.startsWith("正面:")) {
            pos = line.slice(3).trim();
            continue;
        }
        if (line.startsWith("负面:")) {
            neg = line.slice(3).trim();
        }
    }

    if (pos || neg) {
        return {
            pos: normalizeOutputTagText(pos),
            neg: normalizeOutputTagText(neg),
        };
    }

    return { pos: normalizeOutputTagText(text), neg: "" };
}

function extractPreviewFromMessage(message) {
    const queue = [message];
    const visited = new Set();

    for (let depth = 0; depth < 5 && queue.length > 0; depth += 1) {
        const level = queue.splice(0, queue.length);
        for (const payload of level) {
            if (!payload || typeof payload !== "object") {
                continue;
            }
            if (visited.has(payload)) {
                continue;
            }
            visited.add(payload);

            if (Object.prototype.hasOwnProperty.call(payload, PREVIEW_UI_KEY)) {
                return { found: true, ...parsePreviewPayload(payload[PREVIEW_UI_KEY]) };
            }

            const ui = payload.ui;
            if (ui && typeof ui === "object" && Object.prototype.hasOwnProperty.call(ui, PREVIEW_UI_KEY)) {
                return { found: true, ...parsePreviewPayload(ui[PREVIEW_UI_KEY]) };
            }

            if (Array.isArray(payload.result) && payload.result.length >= 2) {
                return { found: true, ...parsePreviewPayload(payload.result) };
            }

            for (const value of Object.values(payload)) {
                if (value && typeof value === "object") {
                    queue.push(value);
                }
            }
        }
    }

    return { found: false, pos: "", neg: "" };
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

function buildRealtimePreview(node) {
    const switchWidget = getWidgetByName(node, "总开关");
    if (switchWidget && switchWidget.value === false) {
        return { pos: "", neg: "" };
    }

    const seedWidget = getWidgetByName(node, "seed");
    const seed = Number(seedWidget?.value ?? 0);
    const modeWidget = getWidgetByName(node, "模式选择");
    const categoryWidget = getWidgetByName(node, "分类");

    const negWidget = getWidgetByName(node, PREVIEW_NEG_WIDGET_NAME);
    let pos = "";
    let neg = normalizeOutputTagText(getWidgetStringValue(negWidget));

    if (modeWidget && categoryWidget) {
        const labels = getCategoryLabels(categoryWidget);
        const itemWidgets = labels.map((name) => getWidgetByName(node, name)).filter((w) => !!w);
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
            const candidates = [];
            if (sourceWidget) {
                for (const v of getWidgetOptions(sourceWidget)) {
                    if (v === "(随机)") {
                        continue;
                    }
                    const normalized = normalizeTagDisplay(v);
                    if (normalized) {
                        candidates.push(normalized);
                    }
                }
                pos = pickDeterministic(candidates, seed, sourceWidget.name.length || 1);
            } else {
                for (const w of itemWidgets) {
                    for (const v of getWidgetOptions(w)) {
                        if (v === "(随机)") {
                            continue;
                        }
                        const normalized = normalizeTagDisplay(v);
                        if (normalized) {
                            candidates.push(normalized);
                        }
                    }
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
                const candidates = [];
                for (const v of getWidgetOptions(row)) {
                    if (v === "(不输出)" || v === "(随机)") {
                        continue;
                    }
                    const normalized = normalizeTagDisplay(v);
                    if (normalized) {
                        candidates.push(normalized);
                    }
                }
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
        neg = "";
    }

    return {
        pos: normalizeOutputTagText(pos),
        neg: normalizeOutputTagText(neg),
    };
}

function isPreviewWidgetName(name) {
    return (
        name === PREVIEW_POS_WIDGET_NAME
        || name === PREVIEW_NEG_WIDGET_NAME
        || name === LEGACY_PREVIEW_WIDGET_NAME
    );
}

function refreshRealtimePreview(node, changedWidgetName) {
    if (isPreviewWidgetName(changedWidgetName)) {
        return;
    }
    updatePreviewWidgets(node, buildRealtimePreview(node));
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
            ensurePreviewWidgets(this);
            syncCategoryBySelectedItem(this);
            updatePreviewWidgets(this, buildRealtimePreview(this));
            return result;
        };

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function (...args) {
            const result = originalOnNodeCreated ? originalOnNodeCreated.apply(this, args) : undefined;
            ensurePreviewWidgets(this);
            updatePreviewWidgets(this, buildRealtimePreview(this));
            return result;
        };

        const originalOnWidgetChanged = nodeType.prototype.onWidgetChanged;
        nodeType.prototype.onWidgetChanged = function (name, value, oldValue, widget) {
            const result = originalOnWidgetChanged
                ? originalOnWidgetChanged.call(this, name, value, oldValue, widget)
                : undefined;

            if (this.__lingPromptCardSyncing) {
                refreshRealtimePreview(this, name);
                return result;
            }

            const categoryWidget = getWidgetByName(this, "分类");
            if (categoryWidget) {
                const categoryLabels = getCategoryLabels(categoryWidget);
                if (
                    categoryLabels.includes(name)
                    && value !== "(随机)"
                    && categoryWidget.value !== name
                ) {
                    this.__lingPromptCardSyncing = true;
                    try {
                        categoryWidget.value = name;
                        this.setDirtyCanvas?.(true, true);
                    } finally {
                        this.__lingPromptCardSyncing = false;
                    }
                }
            }

            refreshRealtimePreview(this, name);
            return result;
        };

        const originalOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            const result = originalOnExecuted ? originalOnExecuted.call(this, message) : undefined;
            const preview = extractPreviewFromMessage(message);
            if (preview.found) {
                updatePreviewWidgets(this, preview);
            }
            return result;
        };
    },
});
