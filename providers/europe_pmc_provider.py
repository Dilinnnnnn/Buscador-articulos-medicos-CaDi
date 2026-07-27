import re
import requests
from .base import ArticleProvider, SearchResult


def _strip_html(text):
    return re.sub(r"<[^>]+>", "", text).strip()

BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


class EuropePMCProvider(ArticleProvider):
    source = "europepmc"
    source_label = "Europe PMC"

    def buscar(self, query, page=1):
        limit = 20

        try:
            resp = requests.get(BASE_URL, params={
                "query": query,
                "resultType": "core",
                "pageSize": limit,
                "page": page,
                "format": "json",
            }, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return SearchResult([], 0, page, 0, self.source, self.source_label,
                                error=f"Error en Europe PMC: {e}")

        result_list = data.get("resultList", {}) or {}
        results = result_list.get("result", [])
        total = data.get("hitCount", len(results)) or 0

        articles = []
        for paper in results:
            authors = paper.get("authorString", "") or ""
            author_str = ", ".join(
                a.strip() for a in authors.split(",")[:3])
            if authors.count(",") >= 3:
                author_str += " et al."

            doi = paper.get("doi", "") or ""
            pmid = paper.get("pmid", "") or ""
            pmcid = paper.get("pmcid", "") or ""

            url = ""
            if doi:
                url = f"https://doi.org/{doi}"
            elif pmcid:
                url = f"https://europepmc.org/article/PMC/{pmcid}"
            elif pmid:
                url = f"https://europepmc.org/article/MED/{pmid}"

            articles.append({
                "title": paper.get("title", "Sin título"),
                "authors": author_str or "Autores no disponibles",
                "journal": paper.get("journalTitle", "Journal no disponible"),
                "pubdate": paper.get("pubYear", paper.get("firstPublicationDate", ""))[:10],
                "abstract": _strip_html(paper.get("abstractText", "Resumen no disponible")) or "Resumen no disponible",
                "doi": f"DOI: {doi}" if doi else "",
                "url": url,
                "source_label": self.source_label,
            })

        total_pages = max(1, (total + limit - 1) // limit) if total else 1
        return SearchResult(articles, total, page, total_pages,
                            self.source, self.source_label)
