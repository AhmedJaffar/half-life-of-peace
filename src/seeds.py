"""Resolve English article titles into per-language editions via MediaWiki langlinks.

Article titles in each language are resolved *programmatically* rather than
hand-translated, so the multilingual construction is auditable and
reproducible.  ``redirects=1`` is essential: several concept titles redirect
on English Wikipedia, and redirect pages expose no interlanguage links.
"""

import urllib.parse
from typing import Dict, List, Optional

from . import config
from .http import get_json, slug

_API = "https://en.wikipedia.org/w/api.php"


def _langlinks_url(en_title: str) -> str:
    params = {
        "action": "query",
        "prop": "langlinks",
        "titles": en_title,
        "redirects": "1",
        "lllimit": "max",
        "format": "json",
        "formatversion": "2",
    }
    return _API + "?" + urllib.parse.urlencode(params)


def resolve_langlinks(en_title: str) -> Dict[str, Optional[str]]:
    """Map an English title to titles in every requested language edition.

    Returns a dict keyed by language code (always including ``en``) whose
    values are article titles, or ``None`` where no article exists.
    """
    cache = config.CACHE / "langlinks" / (slug(en_title) + ".json")
    data = get_json(_langlinks_url(en_title), cache_path=cache)

    out = {lang: None for lang in config.LANGS}  # type: Dict[str, Optional[str]]
    if not data or data.get("_missing"):
        return out

    pages = data.get("query", {}).get("pages", [])
    if not pages:
        return out
    page = pages[0]
    if page.get("missing"):
        return out

    resolved = page.get("title")
    out["en"] = resolved
    for link in page.get("langlinks", []) or []:
        lang = link.get("lang")
        if lang in config.LANGS:
            out[lang] = link.get("title")
    return out


def concept_seed_table() -> List[dict]:
    """One row per (family, concept, language) with the resolved article title."""
    rows = []
    families = (("war", config.WAR_CONCEPTS), ("peace", config.PEACE_CONCEPTS))
    for family, concepts in families:
        for concept in concepts:
            mapping = resolve_langlinks(concept)
            for lang in config.CONCEPT_LANGS:
                rows.append(
                    {
                        "family": family,
                        "concept": concept,
                        "lang": lang,
                        "en_title": concept,
                        "article": mapping.get(lang),
                    }
                )
    return rows


def event_seed_table(events) -> List[dict]:
    """Resolve event and conflict articles for every event.

    ``events`` is a list of dicts with keys ``event_id``, ``en_wiki_article``
    and ``conflict_wiki_article``.  For each event and language we produce one
    row for the event-specific article and one for the conflict article.
    """
    rows = []
    for ev in events:
        for role, en_title in (
            ("event", ev.get("en_wiki_article")),
            ("conflict", ev.get("conflict_wiki_article")),
        ):
            if not en_title:
                continue
            mapping = resolve_langlinks(str(en_title))
            for lang in config.LANGS:
                rows.append(
                    {
                        "event_id": ev["event_id"],
                        "role": role,
                        "lang": lang,
                        "en_title": en_title,
                        "article": mapping.get(lang),
                    }
                )
    return rows
