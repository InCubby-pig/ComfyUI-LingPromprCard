import { app } from "../../scripts/app.js";

const TARGET_NODE_NAMES = new Set([
    "LingPromptCardCostume",
    "LingPromptCardFraming",
    "LingPromptCardR18Scene",
    "LingPromptCardScene",
]);

function getWidgetByName(node, name) {
    if (!node?.widgets) {
        return null;
    }
    return node.widgets.find((widget) => widget?.name === name) || null;
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
        if (!TARGET_NODE_NAMES.has(nodeData?.name)) {
            return;
        }
        if (nodeType.prototype.__lingPromptCardAutoSelectPatched) {
            return;
        }
        nodeType.prototype.__lingPromptCardAutoSelectPatched = true;

        const originalOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (...args) {
            const result = originalOnConfigure ? originalOnConfigure.apply(this, args) : undefined;
            syncCategoryBySelectedItem(this);
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
    },
});
