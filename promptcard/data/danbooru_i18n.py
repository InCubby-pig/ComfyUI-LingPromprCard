# -*- coding: utf-8 -*-
"""Danbooru 中英显示辅助。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict


DEFAULT_LEXICON_PATH = (
    Path(__file__).resolve().parent / "danbooru_zh_cn_lexicon.json"
)


def _normalize_dict(data: object) -> Dict[str, str]:
    if not isinstance(data, dict):
        return {}
    out: Dict[str, str] = {}
    for key, value in data.items():
        k = str(key).strip()
        v = str(value).strip()
        if not k or not v:
            continue
        out[k] = v
    return out


@lru_cache(maxsize=1)
def load_zh_cn_lexicon() -> Dict[str, Dict[str, str]]:
    """加载汉化词库，不存在时返回空词库。"""
    if not DEFAULT_LEXICON_PATH.exists():
        return {"tags": {}, "labels": {}, "sources": {}}

    try:
        payload = json.loads(DEFAULT_LEXICON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"tags": {}, "labels": {}, "sources": {}}

    return {
        "tags": _normalize_dict(payload.get("tags", {})),
        "labels": _normalize_dict(payload.get("labels", {})),
        "sources": _normalize_dict(payload.get("sources", {})),
    }


def _bilingual(zh: str, en: str) -> str:
    zh = zh.strip()
    en = en.strip()
    if not zh or zh == en:
        return en
    return f"{zh} | {en}"


def format_tag_display(tag: str, lexicon: Dict[str, Dict[str, str]] | None = None) -> str:
    tag = str(tag).strip()
    if not tag:
        return ""
    lexicon = lexicon or load_zh_cn_lexicon()
    zh = lexicon.get("tags", {}).get(tag, "")
    return _bilingual(zh, tag)


def format_label_display(label: str, lexicon: Dict[str, Dict[str, str]] | None = None) -> str:
    label = str(label).strip()
    if not label:
        return ""

    lexicon = lexicon or load_zh_cn_lexicon()
    labels = lexicon.get("labels", {})
    if label in labels:
        return _bilingual(labels[label], label)

    if "/" not in label:
        return label

    segments = [seg.strip() for seg in label.split("/")]
    translated = []
    changed = False
    for seg in segments:
        zh = labels.get(seg, "")
        if zh:
            translated.append(zh)
            changed = True
        else:
            translated.append(seg)
    if not changed:
        return label
    return _bilingual(" / ".join(translated), label)


def get_tag_translation(tag: str, lexicon: Dict[str, Dict[str, str]] | None = None) -> str:
    tag = str(tag).strip()
    if not tag:
        return ""
    lexicon = lexicon or load_zh_cn_lexicon()
    return lexicon.get("tags", {}).get(tag, "")
