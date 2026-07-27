import requests
from .base import ArticleProvider, SearchResult

BASE_URL = "https://api.openalex.org/works"


def _inverted_index_to_text(inverted_index):
    if not inverted_index:
        return ""
    words = []
    for word, positions in inverted_index.items():
        for pos in positions:
            words.append((pos, word))
    words.sort(key=lambda x: x[0])
    return " ".join(w for _, w in words)


class OpenAlexProvider(ArticleProvider):
    source = "openalex"
    source_label = "OpenAlex"

    def buscar(self, query, page=1):
        limit = 20

        try:
            resp = requests.get(BASE_URL, params={
                "search": query,
                "per_page": limit,
                "page": page,
                "sort": "cited_by_count:desc",
                "select": "id,title,authorships,primary_location,publication_date,"
                          "abstract_inverted_index,doi,open_access",
            }, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return SearchResult([], 0, page, 0, self.source, self.source_label,
                                error=f"Error en OpenAlex: {e}")

        total = data.get("meta", {}).get("count", 0) or 0
        results = data.get("results", [])

        articles = []
        for work in results:
            authorships = work.get("authorships") or []
            author_names = [a.get("author", {}).get("display_name", "")
                           for a in authorships[:3]]
            author_str = ", ".join(n for n in author_names if n)
            if len(authorships) > 3:
                author_str += " et al."

            primary_loc = work.get("primary_location") or {}
            source_info = primary_loc.get("source") or {}
            journal = source_info.get("display_name", "Journal no disponible")

            landing = primary_loc.get("landing_page_url", "")

            abstract = _inverted_index_to_text(
                work.get("abstract_inverted_index"))

            doi = work.get("doi", "") or ""
            if doi.startswith("https://doi.org/"):
                doi = doi[16:]

            articles.append({
                "title": work.get("title", "Sin título"),
                "authors": author_str or "Autores no disponibles",
                "journal": journal,
                "pubdate": (work.get("publication_date") or "")[:10],
                "abstract": abstract or "Resumen no disponible",
                "doi": f"DOI: {doi}" if doi else "",
                "url": landing or f"https://openalex.org/{work.get('id', '')}",
                "source_label": self.source_label,
            })

        total_pages = max(1, (total + limit - 1) // limit) if total else 1
        return SearchResult(articles, total, page, total_pages,
                            self.source, self.source_label)
