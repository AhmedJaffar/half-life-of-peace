#!/usr/bin/env python3
"""
Systematic literature search for "The Half-Life of Peace".
Queries OpenAlex, Crossref, arXiv, and Semantic Scholar (best-effort),
saves raw results to paper/_search_raw.json and a human-readable log.

Read-only w.r.t. the project; writes only under paper/.
"""
import json, time, sys, re, os
import requests

H = {'User-Agent': 'half-life-of-peace-lit-review/1.0 (mailto:research@example.org)'}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_search_raw.json')

# ---- query plan: (thread, query, source) ----
QUERIES = [
    # A. Issue-attention cycle, agenda setting, attention decay, news half-life
    ('A_issue_attention_cycle', 'issue attention cycle', 'openalex'),
    ('A_issue_attention_cycle', 'issue attention cycle', 'crossref'),
    ('A_issue_attention_cycle', 'public attention policy issues rise fall', 'openalex'),
    ('A_attention_decay', 'attention decay news media', 'openalex'),
    ('A_attention_decay', 'half-life of news attention', 'openalex'),
    ('A_attention_decay', 'news half-life decay public attention', 'crossref'),
    ('A_attention_decay', 'media attention span', 'openalex'),
    ('A_collective_attention', 'collective attention dynamics', 'openalex'),
    ('A_collective_attention', 'collective attention dynamics half-life', 'arxiv'),
    ('A_collective_attention', 'attention decay social media hashtags', 'openalex'),
    ('A_agenda_setting', 'agenda setting public attention', 'openalex'),
    ('A_issue_attention_cycle', 'punctuated equilibrium public policy attention', 'openalex'),
    ('A_global_attention', 'global public attention issue salience', 'openalex'),

    # B. Wikipedia pageviews as attention proxy
    ('B_wikipedia_attention', 'Wikipedia pageviews collective attention', 'openalex'),
    ('B_wikipedia_attention', 'Wikipedia page views measure public attention', 'openalex'),
    ('B_wikipedia_attention', 'Wikipedia article views news events attention', 'crossref'),
    ('B_wikipedia_attention', 'Wikipedia pageview forecasting', 'openalex'),
    ('B_wikipedia_attention', 'Wikipedia traffic collective attention', 'arxiv'),
    ('B_wikipedia_multilingual', 'multilingual Wikipedia comparison language editions', 'openalex'),
    ('B_wikipedia_multilingual', 'cross-lingual Wikipedia cultural attention', 'openalex'),
    ('B_wikipedia_attention', 'Wikipedia salience issue attention', 'openalex'),
    ('B_wikipedia_attention', 'Wikipedia memory forgetting collective memory', 'openalex'),

    # C. Conflict forecasting / early warning
    ('C_conflict_forecasting', 'conflict forecasting early warning', 'openalex'),
    ('C_conflict_forecasting', 'ViEWS violence early warning system', 'openalex'),
    ('C_conflict_forecasting', 'predicting armed conflict machine learning', 'openalex'),
    ('C_conflict_forecasting', 'conflict prediction UCDP', 'openalex'),
    ('C_conflict_forecasting', 'early warning conflict attention indicators', 'openalex'),
    ('C_conflict_forecasting', 'nowcasting conflict event data', 'openalex'),
    ('C_conflict_forecasting', 'ACLED conflict event data forecasting', 'openalex'),
    ('C_conflict_forecasting', 'forecasting civil war onset', 'crossref'),

    # D. Peace durability / ceasefire survival
    ('D_peace_durability', 'peace agreement durability', 'openalex'),
    ('D_peace_durability', 'ceasefire survival duration', 'openalex'),
    ('D_peace_durability', 'ceasefire duration conflict recurrence', 'crossref'),
    ('D_peace_durability', 'peace spells conflict recurrence', 'openalex'),
    ('D_peace_durability', 'Fortna peace time ceasefire', 'openalex'),
    ('D_peace_durability', 'peacekeeping violence civilian protection', 'openalex'),
    ('D_peace_durability', 'third party guarantees peace agreement', 'openalex'),
    ('D_peace_durability', 'mediation ceasefire agreement', 'openalex'),
    ('D_peace_durability', 'ceasefire violation prediction', 'openalex'),

    # E. Computational social science, multilingual Wikipedia
    ('E_css_multilingual', 'computational social science multilingual Wikipedia', 'openalex'),
    ('E_css_multilingual', 'Wikipedia language editions cultural bias', 'openalex'),
    ('E_css_multilingual', 'digital trace data social science', 'openalex'),

    # F. Attention and peace/ceasefire specifically  (most threatening)
    ('F_attention_peace', 'attention peace process', 'openalex'),
    ('F_attention_peace', 'media attention peace negotiations', 'openalex'),
    ('F_attention_peace', 'news coverage ceasefire', 'openalex'),
    ('F_attention_peace', 'media attention armed conflict', 'openalex'),
    ('F_attention_peace', 'public attention war', 'openalex'),
    ('F_attention_peace', 'media coverage conflict foreign policy CNN effect', 'openalex'),
    ('F_attention_peace', 'audience costs public opinion conflict', 'openalex'),
    ('F_attention_peace', 'issue salience armed conflict media', 'openalex'),
    ('F_attention_peace', 'public attention humanitarian crisis', 'openalex'),
    ('F_attention_peace', 'media attention natural disasters decay', 'openalex'),
    ('F_attention_peace', 'attention humanitarian emergencies donate', 'openalex'),
    ('F_attention_peace', 'ceasefire media coverage', 'crossref'),
    ('F_attention_peace', 'attention peace', 'crossref'),
    ('F_attention_peace', 'Wikipedia war attention', 'openalex'),
    ('F_attention_peace', 'social media attention conflict Ukraine', 'openalex'),
    ('F_attention_peace', 'Google Trends conflict attention', 'openalex'),
    ('F_attention_peace', 'search data nowcasting social attention', 'openalex'),
    ('F_attention_peace', 'attention decay international crises', 'crossref'),
    ('F_attention_peace', 'public attention civil war', 'openalex'),
]

S2_QUERIES = [
    ('A_issue_attention_cycle', 'issue attention cycle'),
    ('A_attention_decay', 'attention decay news half-life'),
    ('B_wikipedia_attention', 'Wikipedia pageviews collective attention'),
    ('C_conflict_forecasting', 'conflict forecasting early warning'),
    ('D_peace_durability', 'ceasefire survival duration'),
    ('F_attention_peace', 'attention peace process ceasefire media'),
    ('F_attention_peace', 'public attention armed conflict media'),
    ('F_attention_peace', 'Wikipedia pageviews conflict attention'),
]

ARXIV_LIST = [
    ('A_collective_attention', 'all:"collective attention"'),
    ('A_attention_decay', 'all:"attention decay"'),
    ('A_attention_decay', 'all:"attention half-life"'),
    ('B_wikipedia_attention', 'all:"Wikipedia pageviews"'),
    ('B_wikipedia_attention', 'all:"Wikipedia" AND all:"attention"'),
    ('C_conflict_forecasting', 'all:"conflict forecasting"'),
    ('C_conflict_forecasting', 'all:"early warning" AND all:"conflict"'),
    ('F_attention_peace', 'all:"ceasefire" AND all:"attention"'),
    ('F_attention_peace', 'all:"media attention" AND all:"conflict"'),
    ('F_attention_peace', 'all:"attention" AND all:"peace"'),
    ('F_attention_peace', 'all:"news attention" AND all:"war"'),
    ('B_wikipedia_multilingual', 'all:"multilingual Wikipedia"'),
]


def openalex(q):
    url = 'https://api.openalex.org/works'
    params = {'search': q, 'per-page': 25,
              'select': 'id,doi,title,publication_year,cited_by_count,authorships,type,primary_location,abstract_inverted_index'}
    r = requests.get(url, params=params, headers=H, timeout=40)
    r.raise_for_status()
    out = []
    for w in r.json().get('results', []):
        auth = [a.get('author', {}).get('display_name') for a in w.get('authorships', [])][:6]
        src = ''
        pl = w.get('primary_location') or {}
        if pl.get('source'):
            src = pl['source'].get('display_name', '')
        out.append({'title': w.get('title'), 'year': w.get('publication_year'),
                    'doi': (w.get('doi') or '').replace('https://doi.org/', ''),
                    'cites': w.get('cited_by_count'), 'authors': auth, 'venue': src,
                    'type': w.get('type'), 'openalex_id': w.get('id')})
    return out


def crossref(q):
    url = 'https://api.crossref.org/works'
    params = {'query': q, 'rows': 20, 'select': 'DOI,title,author,issued,container-title,is-referenced-by-count,type'}
    r = requests.get(url, params=params, headers=H, timeout=40)
    r.raise_for_status()
    out = []
    for w in r.json()['message']['items']:
        auth = []
        for a in w.get('author', [])[:6]:
            nm = (a.get('family', '') + (', ' + a.get('given', '') if a.get('given') else '')).strip(', ')
            if nm:
                auth.append(nm)
        issued = w.get('issued', {}).get('date-parts', [[None]])[0][0]
        t = w.get('title', [''])
        out.append({'title': t[0] if t else '', 'year': issued,
                    'doi': w.get('DOI'), 'cites': w.get('is-referenced-by-count'),
                    'authors': auth, 'venue': (w.get('container-title') or [''])[0],
                    'type': w.get('type')})
    return out


def arxiv(q):
    url = 'http://export.arxiv.org/api/query'
    params = {'search_query': q, 'max_results': 20, 'sortBy': 'relevance'}
    r = requests.get(url, params=params, headers=H, timeout=40)
    r.raise_for_status()
    import xml.etree.ElementTree as ET
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    root = ET.fromstring(r.content)
    out = []
    for e in root.findall('a:entry', ns):
        title = ' '.join((e.find('a:title', ns).text or '').split())
        summ = ' '.join((e.find('a:summary', ns).text or '').split())
        pub = e.find('a:published', ns)
        auth = [a.find('a:name', ns).text for a in e.findall('a:author', ns)][:6]
        out.append({'title': title, 'year': (pub.text[:4] if pub is not None else None),
                    'doi': None, 'cites': None, 'authors': auth,
                    'venue': 'arXiv', 'abstract': summ[:400],
                    'arxiv_id': e.find('a:id', ns).text})
    return out


def s2(q):
    url = 'https://api.semanticscholar.org/graph/v1/paper/search'
    params = {'query': q, 'fields': 'title,year,authors,externalIds,citationCount,venue',
              'limit': 20}
    for attempt in range(4):
        r = requests.get(url, params=params, headers=H, timeout=40)
        if r.status_code == 200:
            out = []
            for p in r.json().get('data', []):
                ext = p.get('externalIds') or {}
                out.append({'title': p.get('title'), 'year': p.get('year'),
                            'doi': ext.get('DOI'), 'cites': p.get('citationCount'),
                            'authors': [a.get('name') for a in p.get('authors', [])][:6],
                            'venue': p.get('venue'),
                            's2_id': p.get('paperId')})
            return out
        if r.status_code == 429:
            time.sleep(4 * (attempt + 1))
            continue
        r.raise_for_status()
    return None


def main():
    results = {'queries': [], 'generated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    for thread, q, src in QUERIES:
        entry = {'thread': thread, 'query': q, 'source': src}
        try:
            if src == 'openalex':
                entry['results'] = openalex(q)
            elif src == 'crossref':
                entry['results'] = crossref(q)
            print(f'OK  {src:9s} {thread:28s} {q[:60]:60s} n={len(entry["results"])}', flush=True)
        except Exception as e:
            entry['error'] = repr(e)
            print(f'ERR {src:9s} {q[:50]} -> {e!r}', flush=True)
        results['queries'].append(entry)
        time.sleep(0.35)

    for thread, q in S2_QUERIES:
        entry = {'thread': thread, 'query': q, 'source': 'semanticscholar'}
        try:
            res = s2(q)
            entry['results'] = res
            print(f'OK  s2        {q[:60]:60s} n={0 if res is None else len(res)}', flush=True)
        except Exception as e:
            entry['error'] = repr(e)
            print(f'ERR s2 {q[:50]} -> {e!r}', flush=True)
        results['queries'].append(entry)
        time.sleep(2.0)

    for thread, q in ARXIV_LIST:
        entry = {'thread': thread, 'query': q, 'source': 'arxiv'}
        try:
            entry['results'] = arxiv(q)
            print(f'OK  arxiv     {q[:60]:60s} n={len(entry["results"])}', flush=True)
        except Exception as e:
            entry['error'] = repr(e)
            print(f'ERR arxiv {q[:50]} -> {e!r}', flush=True)
        results['queries'].append(entry)
        time.sleep(2.0)

    with open(OUT, 'w') as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    print('\nWrote', OUT, 'with', len(results['queries']), 'queries')


if __name__ == '__main__':
    main()
