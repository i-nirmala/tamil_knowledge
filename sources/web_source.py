"""Live web source: Tavily when configured, otherwise public Wikipedia + DuckDuckGo HTML."""
from typing import List
import html as html_lib
import re
import requests
from bs4 import BeautifulSoup
from sources.base_source import BaseSource, SourceSearchResult
from src.config import TAVILY_API_KEY, WEB_MAX_RESULTS, WEB_TIMEOUT


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(text or "")).strip()


def _duckduckgo(query: str, top_k: int) -> List[dict]:
    r = requests.get("https://html.duckduckgo.com/html/", params={"q": query},
                     headers={"User-Agent": "CodeBloom/1.0"}, timeout=WEB_TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for result in soup.select(".result")[:top_k]:
        a = result.select_one("a.result__a")
        sn = result.select_one(".result__snippet")
        if not a:
            continue
        out.append({"title": _clean(a.get_text(" ", strip=True)), "url": a.get("href", ""),
                    "snippet": _clean(sn.get_text(" ", strip=True) if sn else "")})
    return out


def _tavily(query: str, top_k: int) -> List[dict]:
    if not TAVILY_API_KEY:
        return []
    r = requests.post("https://api.tavily.com/search",
        json={"api_key": TAVILY_API_KEY, "query": query, "search_depth": "advanced",
              "max_results": top_k, "include_answer": False}, timeout=WEB_TIMEOUT)
    r.raise_for_status()
    return r.json().get("results", [])


def _fetch_page(url: str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent": "CodeBloom/1.0"}, timeout=WEB_TIMEOUT,
                         allow_redirects=True)
        if "text/html" not in r.headers.get("content-type", ""):
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        text = _clean(soup.get_text(" ", strip=True))
        return text[:6000]
    except Exception:
        return ""


def _wikipedia(query: str, top_k: int) -> List[dict]:
    lang = "ta" if re.search(r"[\u0B80-\u0BFF]", query) else "en"
    try:
        r = requests.get(f"https://{lang}.wikipedia.org/w/api.php", params={
            "action":"query", "list":"search", "srsearch":query,
            "format":"json", "utf8":1, "srlimit":top_k}, timeout=WEB_TIMEOUT)
        r.raise_for_status()
        results=[]
        for x in r.json().get("query", {}).get("search", []):
            title=x.get("title", "")
            url=f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
            results.append({"title":title, "url":url, "snippet":_clean(re.sub("<.*?>", " ", x.get("snippet", "")))})
        return results
    except Exception:
        return []


class WebAdapter(BaseSource):
    name = "Live Web"
    key = "web"

    def is_available(self) -> bool:
        return True

    def search(self, query: str, query_vector, top_k: int) -> List[SourceSearchResult]:
        raw = []
        try:
            raw.extend(_tavily(query, min(top_k, WEB_MAX_RESULTS)))
        except Exception:
            pass
        if not raw:
            try:
                raw.extend(_wikipedia(query, min(top_k, 4)))
            except Exception:
                pass
            try:
                raw.extend(_duckduckgo(query, min(top_k, 4)))
            except Exception:
                pass

        results=[]
        seen=set()
        for item in raw:
            url=item.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            body=item.get("content") or item.get("snippet") or ""
            if not body:
                body=_fetch_page(url)
            else:
                body=_clean(body)
            if not body:
                continue
            # Metadata matches the existing evidence/citation schema.
            meta={
                "chunk_id":"web:"+str(abs(hash(url))),
                "doc_id":"web:"+str(abs(hash(url))),
                "book_title":item.get("title") or url,
                "author":item.get("author") or "Web source",
                "chapter":"",
                "page_number":1,
                "source_filename":url,
                "source_url":url,
                "source_type":"web",
                "text":body[:6000],
            }
            # Simple score: title/snippet hits + baseline. Reranker handles lexical overlap.
            qwords=set(re.findall(r"[\w\u0B80-\u0BFF]+", query.lower()))
            twords=set(re.findall(r"[\w\u0B80-\u0BFF]+", (meta["book_title"]+" "+body[:2000]).lower()))
            overlap=len(qwords & twords)/max(1,len(qwords))
            score=min(0.9, 0.35 + 0.55*overlap)
            results.append(SourceSearchResult(metadata=meta, score=score))
            if len(results)>=top_k:
                break
        return results

    def status_message(self) -> str:
        return "✓ Live search enabled (Tavily optional; Wikipedia + DuckDuckGo fallback)"
