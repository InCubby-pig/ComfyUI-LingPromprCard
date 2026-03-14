#!/usr/bin/env python3
"""抓取 Danbooru tag_groups 并生成细分选择器数据文件。"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, OrderedDict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Optional, Set, Tuple

API_URL = "https://danbooru.donmai.us/wiki_pages.json"
ROOT_TITLE = "tag_groups"
REQUEST_INTERVAL_SEC = 0.05
MAX_RETRIES = 3
MAX_CRAWL_PAGES = 1200

# 细分规则：除 Body 全拆外，其余按 source_page 体量阈值拆分。
SELECTOR_SPLIT_THRESHOLD = 150

WIKI_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"^\s*h([1-6])(?:#[^.]+)?\.\s*(.+?)\s*$", re.IGNORECASE)
BULLET_RE = re.compile(r"^(\*+)\s*(.*)$")

IGNORE_HEADING_KEYWORDS = {
    "see also",
    "table of contents",
    "toc",
}

BUCKET_PRIORITY = [
    "danbooru_metatags",
    "danbooru_sex_r18",
    "danbooru_copyright_character",
    "danbooru_visual",
]

NODE_META = OrderedDict(
    [
        (
            "danbooru_visual",
            {
                "title": "Danbooru标签-视觉",
                "sections": ["Visual characteristics"],
                "display_prefix": "Danbooru-视觉",
            },
        ),
        (
            "danbooru_sex_r18",
            {
                "title": "Danbooru标签-Sex/R18",
                "sections": ["Visual characteristics > Sex"],
                "display_prefix": "Danbooru-Sex",
            },
        ),
        (
            "danbooru_copyright_character",
            {
                "title": "Danbooru标签-版权与角色",
                "sections": ["Copyrights, artists, projects and media"],
                "display_prefix": "Danbooru-版权",
            },
        ),
        (
            "danbooru_metatags",
            {
                "title": "Danbooru标签-Metatags",
                "sections": ["Metatags"],
                "display_prefix": "Danbooru-Meta",
            },
        ),
    ]
)


@dataclass(frozen=True)
class CrawlContext:
    root_h5: str
    root_h6: str
    bucket: str


@dataclass
class BulletEntry:
    depth: int
    heading_path: List[str]
    text: str
    links: List[Tuple[str, str]]


@dataclass
class SelectorSpec:
    node_key: str
    class_name: str
    display_name: str
    module_name: str
    data: Dict[str, object]
    bucket: str
    category: str
    source: str
    item_count: int


def normalize_title_key(title: str) -> str:
    title = title.strip().lower().replace("_", " ")
    title = re.sub(r"\s+", " ", title)
    return title


def is_structural_page_title(title: str) -> bool:
    low = normalize_title_key(title)
    return (
        low.startswith("tag group:")
        or low.startswith("tag_group:")
        or low.startswith("list of ")
        or low in {"tag groups", "pool groups", "list of meta-wikis"}
    )


def classify_root_context(root_h5: str, root_h6: str) -> str:
    low_h5 = root_h5.lower().strip()
    low_h6 = root_h6.lower().strip()

    if "metatags" in low_h5:
        return "danbooru_metatags"
    if "copyrights, artists, projects and media" in low_h5:
        return "danbooru_copyright_character"
    if "visual characteristics" in low_h5:
        if "sex" in low_h6:
            return "danbooru_sex_r18"
        return "danbooru_visual"
    return ""


def parse_wiki_links(text: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for match in WIKI_LINK_RE.finditer(text):
        raw = match.group(1).strip()
        if not raw:
            continue

        if "|" in raw:
            target, label = raw.split("|", 1)
        else:
            target, label = raw, raw

        target = target.strip()
        label = label.strip() if label.strip() else target
        if not target:
            continue
        out.append((target, label))
    return out


def parse_heading(line: str) -> Optional[Tuple[int, str]]:
    match = HEADING_RE.match(line.strip())
    if not match:
        return None
    level = int(match.group(1))
    title = match.group(2).strip()
    return level, title


def fetch_wiki_page(title: str) -> Optional[Dict[str, object]]:
    params = urllib.parse.urlencode({"search[title]": title, "limit": "5"})
    url = f"{API_URL}?{params}"

    last_error: Optional[Exception] = None
    for _ in range(MAX_RETRIES):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ComfyUI-LingPromptCard/1.0 (+data-builder)",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))

            if not isinstance(payload, list) or not payload:
                return None

            wanted = normalize_title_key(title)
            exact = None
            for item in payload:
                item_title = str(item.get("title", ""))
                if normalize_title_key(item_title) == wanted:
                    exact = item
                    break

            page = exact if exact is not None else payload[0]
            return {
                "title": str(page.get("title", "")).strip(),
                "updated_at": str(page.get("updated_at", "")).strip(),
                "body": str(page.get("body", "")),
            }
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(0.6)

    if last_error:
        print(f"[warn] fetch failed: {title} ({last_error})")
    return None


def parse_root_contexts(
    root_body: str,
) -> Tuple[List[str], Dict[str, Set[CrawlContext]], Dict[str, Dict[str, int]]]:
    root_links: List[str] = []
    page_contexts: Dict[str, Set[CrawlContext]] = {}
    page_bucket_votes: Dict[str, Dict[str, int]] = {}

    current_h5 = ""
    current_h6 = ""

    for line in root_body.splitlines():
        heading = parse_heading(line)
        if heading:
            level, title = heading
            if level == 5:
                current_h5 = title
                current_h6 = ""
            elif level == 6:
                current_h6 = title
            elif level < 5:
                current_h5 = title
                current_h6 = ""
            continue

        if not line.strip().startswith("*"):
            continue

        links = parse_wiki_links(line)
        if not links:
            continue

        bucket = classify_root_context(current_h5, current_h6)

        for target, _ in links:
            root_links.append(target)
            key = normalize_title_key(target)
            if bucket:
                ctx = CrawlContext(root_h5=current_h5, root_h6=current_h6, bucket=bucket)
                page_contexts.setdefault(key, set()).add(ctx)
                vote = page_bucket_votes.setdefault(key, {})
                vote[bucket] = vote.get(bucket, 0) + 10

    return root_links, page_contexts, page_bucket_votes


def extract_bullet_entries(body: str) -> List[BulletEntry]:
    entries: List[BulletEntry] = []
    heading_stack: Dict[int, str] = {}

    for line in body.splitlines():
        heading = parse_heading(line)
        if heading:
            level, title = heading
            heading_stack[level] = title
            for old_level in list(heading_stack.keys()):
                if old_level > level:
                    del heading_stack[old_level]
            continue

        match = BULLET_RE.match(line.strip())
        if not match:
            continue

        stars, text = match.groups()
        links = parse_wiki_links(text)
        if not links:
            continue

        heading_path = [heading_stack[i] for i in sorted(heading_stack.keys()) if heading_stack[i].strip()]
        entries.append(
            BulletEntry(
                depth=len(stars),
                heading_path=heading_path,
                text=text.strip(),
                links=links,
            )
        )

    return entries


def should_recurse(title: str, root_link_keys: Set[str]) -> bool:
    key = normalize_title_key(title)
    if key in root_link_keys:
        return True
    return is_structural_page_title(title)


def canonicalize_tag(target: str) -> str:
    target = target.split("#", 1)[0].strip()
    if not target:
        return ""

    if is_structural_page_title(target):
        return ""

    if target.startswith("http://") or target.startswith("https://"):
        return ""

    tag = target.lower().replace(" ", "_")
    tag = re.sub(r"_+", "_", tag)
    tag = tag.strip("_")
    return tag


def choose_bucket(buckets: Iterable[str]) -> str:
    bucket_set = set(buckets)
    for key in BUCKET_PRIORITY:
        if key in bucket_set:
            return key
    return ""


def choose_bucket_by_vote(votes: Dict[str, int]) -> str:
    if not votes:
        return ""
    best_score = max(votes.values())
    candidates = [k for k, score in votes.items() if score == best_score]
    return choose_bucket(candidates)


def ignore_heading_path(heading_path: List[str]) -> bool:
    for title in heading_path:
        low = title.lower()
        for keyword in IGNORE_HEADING_KEYWORDS:
            if keyword in low:
                return True
    return False


def choose_context(contexts: Set[CrawlContext], bucket: str) -> Optional[CrawlContext]:
    filtered = [ctx for ctx in contexts if ctx.bucket == bucket]
    if not filtered:
        return None

    filtered.sort(
        key=lambda c: (
            0 if c.root_h6 else 1,
            len(c.root_h5),
            len(c.root_h6),
            c.root_h5,
            c.root_h6,
        )
    )
    return filtered[0]


def make_entry_id(node_key: str, category: str, title: str, prompt_pos: str, prompt_neg: str) -> str:
    raw = f"{node_key}|{category}|{title}|{prompt_pos}|{prompt_neg}".encode("utf-8")
    digest = hashlib.md5(raw).hexdigest()[:12]
    return f"{node_key}_{digest}"


def make_group_path(context: CrawlContext, page_title: str, heading_path: List[str]) -> str:
    parts = [context.root_h5, context.root_h6, page_title] + heading_path
    out: List[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if out and out[-1].lower() == part.lower():
            continue
        out.append(part)
    return " / ".join(out)


def choose_category_label(context: CrawlContext, heading_path: List[str]) -> str:
    base = context.root_h6.strip() or context.root_h5.strip() or "(未分类)"
    return base


def build_datasets(
    pages: Dict[str, Dict[str, object]],
    page_contexts: Dict[str, Set[CrawlContext]],
    page_bucket_votes: Dict[str, Dict[str, int]],
) -> Tuple[Dict[str, OrderedDict], Dict[str, int], List[str], List[str]]:
    datasets: Dict[str, OrderedDict] = OrderedDict()
    for key, meta in NODE_META.items():
        datasets[key] = OrderedDict(
            title=meta["title"],
            sections=list(meta["sections"]),
            categories=OrderedDict(),
        )

    per_bucket_page_count: Dict[str, int] = {k: 0 for k in NODE_META.keys()}
    bucket_conflict_pages: List[str] = []
    no_context_pages: List[str] = []

    dedupe: Dict[Tuple[str, str], Set[str]] = {}

    for page_key, page in pages.items():
        contexts = page_contexts.get(page_key, set())
        if not contexts:
            no_context_pages.append(str(page.get("title", page_key)))
            continue

        buckets = {ctx.bucket for ctx in contexts if ctx.bucket}
        if not buckets:
            no_context_pages.append(str(page.get("title", page_key)))
            continue

        bucket_votes = page_bucket_votes.get(page_key, {})
        voted_buckets = {k for k, v in bucket_votes.items() if v > 0}
        if len(voted_buckets) > 1:
            bucket_conflict_pages.append(str(page.get("title", page_key)))

        bucket = choose_bucket_by_vote(bucket_votes)
        if not bucket:
            bucket = choose_bucket(buckets)
        if not bucket:
            no_context_pages.append(str(page.get("title", page_key)))
            continue

        chosen_context = choose_context(contexts, bucket)
        if not chosen_context:
            no_context_pages.append(str(page.get("title", page_key)))
            continue

        per_bucket_page_count[bucket] += 1

        page_title = str(page.get("title", page_key))
        body = str(page.get("body", ""))
        entries = extract_bullet_entries(body)

        for entry in entries:
            if ignore_heading_path(entry.heading_path):
                continue

            category_label = choose_category_label(chosen_context, entry.heading_path)
            categories = datasets[bucket]["categories"]
            if category_label not in categories:
                categories[category_label] = []

            seen = dedupe.setdefault((bucket, category_label), set())
            group_title = entry.heading_path[-1] if entry.heading_path else page_title
            group_path = make_group_path(chosen_context, page_title, entry.heading_path)

            for target, _ in entry.links:
                tag = canonicalize_tag(target)
                if not tag or tag in seen:
                    continue
                seen.add(tag)

                prompt_pos = f"{tag}, "
                item_title = tag
                entry_id = make_entry_id(bucket, category_label, item_title, prompt_pos, "")
                categories[category_label].append(
                    {
                        "id": entry_id,
                        "title": item_title,
                        "group_title": group_title,
                        "group_path": group_path,
                        "source_page": page_title,
                        "prompt_pos": prompt_pos,
                        "prompt_neg": "",
                    }
                )

    # 去掉空分类，并固定顺序。
    for node_key in list(datasets.keys()):
        old_categories = datasets[node_key]["categories"]
        new_categories = OrderedDict()
        for label in sorted(old_categories.keys(), key=lambda x: x.lower()):
            items = old_categories[label]
            if not items:
                continue
            items.sort(key=lambda x: x["title"])
            new_categories[label] = items
        datasets[node_key]["categories"] = new_categories

    return datasets, per_bucket_page_count, bucket_conflict_pages, no_context_pages


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("tag_group:", "")
    text = text.replace("list_of_", "")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def titleize(text: str) -> str:
    text = text.replace("tag_group:", "")
    text = text.replace("list_of_", "")
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.title() if text else "Pool"


def sanitize_node_key(*parts: str) -> str:
    merged = "_".join(slugify(p) for p in parts if p)
    merged = re.sub(r"_+", "_", merged).strip("_")
    return f"danbooru_selector_{merged}"


def make_class_name(node_key: str) -> str:
    tokens = [t for t in node_key.split("_") if t]
    return "LingPromptCard" + "".join(t.capitalize() for t in tokens)


def make_display_name(bucket: str, category: str, source: str) -> str:
    prefix = NODE_META[bucket]["display_prefix"]
    cat_title = titleize(category)
    if source == "__ALL__":
        return f"{prefix}-{cat_title}-总池"
    src_title = titleize(source)
    return f"{prefix}-{cat_title}-{src_title}"


def split_category_selectors(
    bucket: str,
    category: str,
    items: List[Dict[str, str]],
) -> List[Tuple[str, List[Dict[str, str]]]]:
    by_source: Dict[str, List[Dict[str, str]]] = {}
    for item in items:
        source = str(item.get("source_page", "")).strip() or "unknown"
        by_source.setdefault(source, []).append(item)

    for source_items in by_source.values():
        source_items.sort(key=lambda x: x["title"])

    if bucket == "danbooru_copyright_character" and category == "Characters":
        all_items = list(items)
        all_items.sort(key=lambda x: x["title"])
        return [("__ALL__", all_items)]

    if bucket == "danbooru_visual" and category == "Body":
        return sorted(by_source.items(), key=lambda kv: kv[0])

    source_counts = Counter({k: len(v) for k, v in by_source.items()})
    large_sources = [
        source for source, count in source_counts.items() if count >= SELECTOR_SPLIT_THRESHOLD
    ]
    large_sources.sort(key=lambda s: (-source_counts[s], s))

    if not large_sources:
        all_items = list(items)
        all_items.sort(key=lambda x: x["title"])
        return [("__ALL__", all_items)]

    out: Dict[str, List[Dict[str, str]]] = {s: list(by_source[s]) for s in large_sources}
    main_source = large_sources[0]

    for source, source_items in by_source.items():
        if source in out:
            continue
        # 低体量来源合并到当前分区最大池，避免节点数量爆炸且不丢数据。
        out[main_source].extend(source_items)

    for source in list(out.keys()):
        out[source].sort(key=lambda x: x["title"])

    return [(s, out[s]) for s in large_sources]


def clone_items_for_node(
    node_key: str,
    category_label: str,
    items: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for item in items:
        prompt_pos = str(item.get("prompt_pos", ""))
        prompt_neg = str(item.get("prompt_neg", ""))
        title = str(item.get("title", ""))
        entry_id = make_entry_id(node_key, category_label, title, prompt_pos, prompt_neg)
        out.append(
            {
                "id": entry_id,
                "title": title,
                "group_title": str(item.get("group_title", "")),
                "group_path": str(item.get("group_path", "")),
                "source_page": str(item.get("source_page", "")),
                "prompt_pos": prompt_pos,
                "prompt_neg": prompt_neg,
            }
        )
    return out


def build_selector_specs(datasets: Dict[str, OrderedDict]) -> List[SelectorSpec]:
    specs: List[SelectorSpec] = []
    used_node_keys: Set[str] = set()
    used_class_names: Set[str] = set()
    used_module_names: Set[str] = set()

    for bucket, node in datasets.items():
        for category_label, items in node["categories"].items():
            selector_groups = split_category_selectors(bucket, category_label, items)
            for source, selected_items in selector_groups:
                suffix_source = source if source != "__ALL__" else "all"
                base_node_key = sanitize_node_key(bucket, category_label, suffix_source)
                node_key = base_node_key
                class_name = make_class_name(node_key)
                module_name = slugify(node_key)

                idx = 2
                while node_key in used_node_keys or class_name in used_class_names or module_name in used_module_names:
                    node_key = f"{base_node_key}_{idx}"
                    class_name = make_class_name(node_key)
                    module_name = slugify(node_key)
                    idx += 1

                used_node_keys.add(node_key)
                used_class_names.add(class_name)
                used_module_names.add(module_name)

                display_name = make_display_name(bucket, category_label, source)
                node_data = {
                    "title": display_name,
                    "sections": list(node["sections"]),
                    "categories": [
                        {
                            "label": f"{titleize(category_label)} / {titleize(source)}",
                            "items": clone_items_for_node(node_key, category_label, selected_items),
                        }
                    ],
                }

                specs.append(
                    SelectorSpec(
                        node_key=node_key,
                        class_name=class_name,
                        display_name=display_name,
                        module_name=module_name,
                        data=node_data,
                        bucket=bucket,
                        category=category_label,
                        source=source,
                        item_count=len(selected_items),
                    )
                )

    specs.sort(key=lambda x: (x.bucket, x.category.lower(), x.source.lower()))
    return specs


def ensure_clean_data_dir(data_root: Path) -> None:
    data_pkg_dir = data_root / "danbooru"
    if data_pkg_dir.exists():
        shutil.rmtree(data_pkg_dir)
    data_pkg_dir.mkdir(parents=True, exist_ok=True)


def dump_selector_modules(data_root: Path, specs: List[SelectorSpec]) -> None:
    data_pkg_dir = data_root / "danbooru"

    (data_root / "__init__.py").write_text("# data package\n", encoding="utf-8")
    (data_pkg_dir / "__init__.py").write_text("# danbooru data package\n", encoding="utf-8")

    for spec in specs:
        lines: List[str] = []
        lines.append("# -*- coding: utf-8 -*-")
        lines.append('"""自动生成文件：由 tools/extract_danbooru_tag_groups.py 生成，请勿手改。"""')
        lines.append("")
        lines.append(f"SELECTOR_NODE_KEY = {spec.node_key!r}")
        lines.append(f"SELECTOR_CLASS_NAME = {spec.class_name!r}")
        lines.append(f"SELECTOR_DISPLAY_NAME = {spec.display_name!r}")
        lines.append(f"SELECTOR_BUCKET = {spec.bucket!r}")
        lines.append(f"SELECTOR_CATEGORY = {spec.category!r}")
        lines.append(f"SELECTOR_SOURCE = {spec.source!r}")
        lines.append("")
        lines.append(f"SELECTOR_DATA = {repr(spec.data)}")
        lines.append("")
        (data_pkg_dir / f"{spec.module_name}.py").write_text("\n".join(lines), encoding="utf-8")


def dump_index_py(index_path: Path, specs: List[SelectorSpec]) -> None:
    lines: List[str] = []
    lines.append("# -*- coding: utf-8 -*-")
    lines.append('"""自动生成文件：聚合 Danbooru 细分选择器数据。"""')
    lines.append("")

    for spec in specs:
        lines.append(
            f"from .danbooru.{spec.module_name} import ("
            f"SELECTOR_CLASS_NAME as C_{spec.module_name}, "
            f"SELECTOR_DATA as D_{spec.module_name}, "
            f"SELECTOR_DISPLAY_NAME as N_{spec.module_name}, "
            f"SELECTOR_NODE_KEY as K_{spec.module_name})"
        )

    lines.append("")
    lines.append("DANBOORU_SELECTOR_SPECS = [")
    for spec in specs:
        lines.append(
            "    {"
            f"'node_key': K_{spec.module_name}, "
            f"'class_name': C_{spec.module_name}, "
            f"'display_name': N_{spec.module_name}"
            "},"
        )
    lines.append("]")
    lines.append("")
    lines.append("DANBOORU_SELECTOR_DATA = {")
    for spec in specs:
        lines.append(f"    K_{spec.module_name}: D_{spec.module_name},")
    lines.append("}")
    lines.append("")

    index_path.write_text("\n".join(lines), encoding="utf-8")


def write_review_report(
    report_path: Path,
    root_updated_at: str,
    pages: Dict[str, Dict[str, object]],
    failed_pages: List[str],
    per_bucket_page_count: Dict[str, int],
    datasets: Dict[str, OrderedDict],
    bucket_conflict_pages: List[str],
    no_context_pages: List[str],
    specs: List[SelectorSpec],
) -> None:
    lines: List[str] = []
    lines.append("# Danbooru Tag Groups 抓取审查报告")
    lines.append("")
    lines.append(f"- 根页面: `{ROOT_TITLE}`")
    lines.append(f"- 根页面更新时间: `{root_updated_at}`")
    lines.append(f"- 抓取页面数: `{len(pages)}`")
    lines.append(f"- 抓取失败数: `{len(failed_pages)}`")
    lines.append(f"- 细分抽卡器数量: `{len(specs)}`")
    lines.append(f"- 细分阈值: `source_page >= {SELECTOR_SPLIT_THRESHOLD}`")
    lines.append("")

    lines.append("## 旧分区统计")
    lines.append("")
    for node_key, meta in NODE_META.items():
        categories = datasets[node_key]["categories"]
        item_count = sum(len(items) for items in categories.values())
        lines.append(
            f"- `{node_key}` ({meta['title']}): 页面 `{per_bucket_page_count.get(node_key, 0)}` / 分类 `{len(categories)}` / 条目 `{item_count}`"
        )
    lines.append("")

    lines.append("## 细分抽卡器统计")
    lines.append("")
    bucket_counter = Counter(spec.bucket for spec in specs)
    for bucket, count in bucket_counter.items():
        lines.append(f"- `{bucket}`: `{count}` 个")
    lines.append("")

    lines.append("## 细分抽卡器明细")
    lines.append("")
    for spec in specs:
        lines.append(
            f"- `{spec.class_name}` | `{spec.node_key}` | {spec.display_name} | "
            f"{spec.category} | {spec.source} | {spec.item_count}"
        )

    lines.append("")
    lines.append("## 复核项")
    lines.append("")
    lines.append(f"- 多桶冲突页面: `{len(bucket_conflict_pages)}`")
    lines.append(f"- 无上下文页面: `{len(no_context_pages)}`")
    lines.append(f"- 抓取失败页面: `{len(failed_pages)}`")

    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def crawl_all_pages(
    root_links: List[str],
    page_contexts: Dict[str, Set[CrawlContext]],
    page_bucket_votes: Dict[str, Dict[str, int]],
) -> Tuple[Dict[str, Dict[str, object]], List[str]]:
    root_keys = {normalize_title_key(t) for t in root_links}

    queue: Deque[str] = deque()
    seen_enqueued: Set[str] = set()

    for title in root_links:
        key = normalize_title_key(title)
        if key in seen_enqueued:
            continue
        seen_enqueued.add(key)
        queue.append(title)

    pages: Dict[str, Dict[str, object]] = {}
    failed_pages: List[str] = []
    processed = 0

    while queue:
        if processed >= MAX_CRAWL_PAGES:
            print(f"[warn] reach MAX_CRAWL_PAGES={MAX_CRAWL_PAGES}, stop crawl early.")
            break

        title = queue.popleft()
        key = normalize_title_key(title)
        if key in pages:
            continue

        page = fetch_wiki_page(title)
        time.sleep(REQUEST_INTERVAL_SEC)

        if not page:
            failed_pages.append(title)
            continue

        processed += 1
        if processed % 50 == 0:
            print(f"[progress] crawled={processed} queue={len(queue)} pages={len(pages)}")

        canonical_title = str(page["title"]).strip() or title
        canonical_key = normalize_title_key(canonical_title)

        pages[canonical_key] = page
        if canonical_key != key and key not in pages:
            if key in page_contexts:
                page_contexts.setdefault(canonical_key, set()).update(page_contexts[key])
            if key in page_bucket_votes:
                votes = page_bucket_votes.setdefault(canonical_key, {})
                for bucket, score in page_bucket_votes[key].items():
                    votes[bucket] = votes.get(bucket, 0) + score

        entries = extract_bullet_entries(str(page.get("body", "")))
        current_contexts = page_contexts.get(key, set()) | page_contexts.get(canonical_key, set())

        for entry in entries:
            if ignore_heading_path(entry.heading_path):
                continue
            for target, _ in entry.links:
                child_key = normalize_title_key(target)
                if not child_key:
                    continue

                if current_contexts:
                    if child_key not in page_contexts:
                        page_contexts[child_key] = set(current_contexts)
                    if child_key not in page_bucket_votes:
                        votes = page_bucket_votes.setdefault(child_key, {})
                        for ctx in current_contexts:
                            votes[ctx.bucket] = votes.get(ctx.bucket, 0) + 1

                if not should_recurse(target, root_keys):
                    continue

                if child_key in pages or child_key in seen_enqueued:
                    continue

                queue.append(target)
                seen_enqueued.add(child_key)

    return pages, failed_pages


def print_stats(
    root_updated_at: str,
    pages: Dict[str, Dict[str, object]],
    failed_pages: List[str],
    datasets: Dict[str, OrderedDict],
    specs: List[SelectorSpec],
) -> None:
    print("抓取完成。")
    print(f"- root_updated_at: {root_updated_at}")
    print(f"- pages: {len(pages)}")
    print(f"- failed_pages: {len(failed_pages)}")
    print(f"- selectors: {len(specs)}")

    for key, node in datasets.items():
        categories = node["categories"]
        item_count = sum(len(items) for items in categories.values())
        print(f"- {key}: 分类 {len(categories)} / 条目 {item_count}")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    data_root = repo_root / "promptcard" / "data"
    index_path = data_root / "danbooru_index.py"
    report_path = repo_root / "tools" / "danbooru_tag_groups_review.md"

    root_page = fetch_wiki_page(ROOT_TITLE)
    if not root_page:
        raise RuntimeError("无法获取 Danbooru 根页面 tag_groups")

    root_updated_at = str(root_page.get("updated_at", ""))
    root_body = str(root_page.get("body", ""))

    root_links, page_contexts, page_bucket_votes = parse_root_contexts(root_body)
    pages, failed_pages = crawl_all_pages(root_links, page_contexts, page_bucket_votes)

    datasets, per_bucket_page_count, bucket_conflict_pages, no_context_pages = build_datasets(
        pages, page_contexts, page_bucket_votes
    )

    specs = build_selector_specs(datasets)
    ensure_clean_data_dir(data_root)
    dump_selector_modules(data_root, specs)
    dump_index_py(index_path, specs)
    write_review_report(
        report_path=report_path,
        root_updated_at=root_updated_at,
        pages=pages,
        failed_pages=failed_pages,
        per_bucket_page_count=per_bucket_page_count,
        datasets=datasets,
        bucket_conflict_pages=bucket_conflict_pages,
        no_context_pages=no_context_pages,
        specs=specs,
    )

    print_stats(
        root_updated_at=root_updated_at,
        pages=pages,
        failed_pages=failed_pages,
        datasets=datasets,
        specs=specs,
    )
    print(f"- data_dir: {data_root / 'danbooru'}")
    print(f"- index_file: {index_path}")
    print(f"- review_report: {report_path}")


if __name__ == "__main__":
    main()
