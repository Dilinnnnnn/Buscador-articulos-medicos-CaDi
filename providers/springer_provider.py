import os
import requests
from .base import ArticleProvider, SearchResult

BASE_URL = "https://api.springernature.com/meta/v1/json"


class SpringerNatureProvider(ArticleProvider):
    source = "springer"
    source_label = "Springer Nature"

    def __init__(self):
        self.api_key = os.environ.get("SPRINGER_NATURE_KEY", "")

    def buscar(self, query, page=1):
        if not self.api_key:
            return SearchResult([], 0, page, 0, self.source, self.source_label,
                                error="Springer Nature requiere API key. "
                                      "Regístrate gratis en https://dev.springernature.com/ "
                                      "y configura SPRINGER_NATURE_KEY en tus variables de entorno.")

        limit = 20
        start = (page - 1) * limit + 1

        try:
            resp = requests.get(BASE_URL, params={
                "q": query,
                "api_key": self.api_key,
                "s": start,
                "p": limit,
            }, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return SearchResult([], 0, page, 0, self.source, self.source_label,
                                error=f"Error en Springer Nature: {e}")

        records = data.get("records", [])
        result_info = data.get("result", [])
        if isinstance(result_info, list) and result_info:
            total = int(result_info[0].get("total", 0) or 0)
        elif isinstance(result_info, dict):
            total = int(result_info.get("total", 0) or 0)
        else:
            total = 0

        articles = []
        for record in records:
            creators = record.get("creators") or []
            author_names = [c.get("creator", "") for c in creators[:3]]
            author_str = ", ".join(author_names)
            if len(creators) > 3:
                author_str += " et al."

            doi = record.get("doi", "")
            urls = record.get("url") or []
            article_url = ""
            for u in urls:
                if u.get("format") == "html":
                    article_url = u.get("value", "")
                    break
            if not article_url and urls:
                article_url = urls[0].get("value", "")

            articles.append({
                "title": record.get("title", "Sin título"),
                "authors": author_str or "Autores no disponibles",
                "journal": record.get("publicationName", "Journal no disponible"),
                "pubdate": record.get("publicationDate", record.get("year", "")),
                "abstract": record.get("abstract", "Resumen no disponible"),
                "doi": f"DOI: {doi}" if doi else "",
                "url": article_url,
                "source_label": self.source_label,
            })

        total_pages = max(1, (total + limit - 1) // limit) if total else 1
        return SearchResult(articles, total, page, total_pages,
                            self.source, self.source_label)
