import os
import time
import requests
from .base import ArticleProvider, SearchResult

BASE_URL = "https://api.semanticscholar.org/graph/v1"


class SemanticScholarProvider(ArticleProvider):
    source = "semantic"
    source_label = "Semantic Scholar"

    def __init__(self):
        self.api_key = os.environ.get("SEMANTIC_SCHOLAR_KEY") or None

    def buscar(self, query, page=1):
        limit = 20
        offset = (page - 1) * limit

        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        for attempt in range(3):
            try:
                resp = requests.get(f"{BASE_URL}/paper/search", params={
                    "query": query,
                    "limit": limit,
                    "offset": offset,
                    "fields": "title,authors,abstract,publicationDate,venue,externalIds,url,tldr",
                }, headers=headers, timeout=15)

                if resp.status_code == 429 and attempt < 2:
                    time.sleep(2)
                    continue

                resp.raise_for_status()
                data = resp.json()
                break
            except Exception as e:
                if attempt == 2:
                    msg = ("Demasiadas solicitudes anónimas. "
                           "Consigue una API key GRATIS en "
                           "https://www.semanticscholar.org/product/api "
                           "y configúrala como SEMANTIC_SCHOLAR_KEY"
                           ) if "429" in str(e) else str(e)
                    return SearchResult([], 0, page, 0, self.source, self.source_label,
                                        error=f"Error en Semantic Scholar: {msg}")
                time.sleep(1)

        total = data.get("total", 0) or 0
        raw = data.get("data", [])
        next_offset = data.get("next")

        articles = []
        for paper in raw:
            authors_list = paper.get("authors") or []
            author_names = [a.get("name", "") for a in authors_list[:3]]
            author_str = ", ".join(author_names)
            if len(authors_list) > 3:
                author_str += " et al."

            tldr = paper.get("tldr")
            if tldr and tldr.get("text"):
                abstract = tldr["text"]
            elif paper.get("abstract"):
                abstract = paper["abstract"]
            else:
                abstract = "Resumen no disponible"

            doi = (paper.get("externalIds") or {}).get("DOI", "")

            articles.append({
                "title": paper.get("title", "Sin título"),
                "authors": author_str or "Autores no disponibles",
                "journal": paper.get("venue", "Journal no disponible"),
                "pubdate": paper.get("publicationDate", ""),
                "abstract": abstract,
                "doi": f"DOI: {doi}" if doi else "",
                "url": paper.get("url", ""),
                "source_label": self.source_label,
            })

        if total:
            total_pages = max(1, (total + limit - 1) // limit)
        elif next_offset is not None:
            total_pages = page + 1
        else:
            total_pages = page

        return SearchResult(articles, total, page, total_pages,
                            self.source, self.source_label)
