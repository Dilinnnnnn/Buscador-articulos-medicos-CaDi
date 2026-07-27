import os
import requests
from .base import ArticleProvider, SearchResult

BASE_URL = "https://api.core.ac.uk/v3/search/works"


class COREProvider(ArticleProvider):
    source = "core"
    source_label = "CORE (Open Access)"

    def __init__(self):
        self.api_key = os.environ.get("CORE_API_KEY", "")

    def buscar(self, query, page=1):
        if not self.api_key:
            return SearchResult([], 0, page, 0, self.source, self.source_label,
                                error="CORE API requiere API key. "
                                      "Regístrate gratis en https://core.ac.uk/services/api "
                                      "y configura CORE_API_KEY en tus variables de entorno.")

        limit = 20
        offset = (page - 1) * limit

        try:
            resp = requests.get(BASE_URL, params={
                "q": query,
                "limit": limit,
                "offset": offset,
            }, headers={
                "Authorization": f"Bearer {self.api_key}",
            }, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return SearchResult([], 0, page, 0, self.source, self.source_label,
                                error=f"Error en CORE: {e}")

        results = data.get("results", [])
        total = data.get("total", 0) or len(results)

        articles = []
        for work in results:
            authors = work.get("authors", []) or []
            author_names = [a.get("name", "") for a in authors[:3]]
            author_str = ", ".join(n for n in author_names if n)
            if len(authors) > 3:
                author_str += " et al."

            full_text = work.get("fullText", "") or ""
            abstract = work.get("abstract", "") or full_text[:500] or "Resumen no disponible"

            doi = work.get("doi", "") or ""

            articles.append({
                "title": work.get("title", "Sin título"),
                "authors": author_str or "Autores no disponibles",
                "journal": work.get("journalName", work.get("publisher", "Journal no disponible")),
                "pubdate": work.get("publishedDate", work.get("year", ""))[:10],
                "abstract": abstract,
                "doi": f"DOI: {doi}" if doi else "",
                "url": work.get("sourceUrl", work.get("doi", "")) or "",
                "source_label": self.source_label,
            })

        total_pages = max(1, (total + limit - 1) // limit) if total else 1
        return SearchResult(articles, total, page, total_pages,
                            self.source, self.source_label)
