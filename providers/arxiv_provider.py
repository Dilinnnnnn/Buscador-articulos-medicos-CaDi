import requests
import xml.etree.ElementTree as ET
from .base import ArticleProvider, SearchResult

BASE_URL = "http://export.arxiv.org/api/query"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}

MEDICAL_CATS = (
    "cat:q-bio.* OR cat:physics.med-ph OR cat:eess.IV OR "
    "cat:cs.AI OR cat:cs.LG OR cat:stat.ML"
)


class ArXivProvider(ArticleProvider):
    source = "arxiv"
    source_label = "arXiv (Médico/Biología)"

    def buscar(self, query, page=1):
        limit = 20
        start = (page - 1) * limit

        search_query = f'all:"{query}" AND ({MEDICAL_CATS})'

        try:
            resp = requests.get(BASE_URL, params={
                "search_query": search_query,
                "start": start,
                "max_results": limit,
                "sortBy": "relevance",
            }, timeout=15)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except Exception as e:
            return SearchResult([], 0, page, 0, self.source, self.source_label,
                                error=f"Error en arXiv: {e}")

        total_el = root.find(".//opensearch:totalResults", NS)
        total = int(total_el.text) if total_el is not None else 0
        entries = root.findall("atom:entry", NS)

        articles = []
        for entry in entries:
            title_el = entry.find("atom:title", NS)
            title = "".join(title_el.itertext()).strip() if title_el is not None else "Sin título"

            author_els = entry.findall("atom:author", NS)
            author_names = []
            for a in author_els[:3]:
                name_el = a.find("atom:name", NS)
                if name_el is not None:
                    author_names.append(name_el.text)
            author_str = ", ".join(author_names)
            if len(author_els) > 3:
                author_str += " et al."

            summary_el = entry.find("atom:summary", NS)
            summary = "".join(summary_el.itertext()).strip() if summary_el is not None else ""

            published_el = entry.find("atom:published", NS)
            pubdate = ""
            if published_el is not None and published_el.text:
                pubdate = published_el.text[:10]

            id_el = entry.find("atom:id", NS)
            arxiv_id = ""
            url = ""
            if id_el is not None and id_el.text:
                arxiv_id = id_el.text.strip().split("/")[-1]
                url = id_el.text.strip()

            doi_el = entry.find("arxiv:doi", NS)
            doi = doi_el.text if doi_el is not None else ""

            journal_el = entry.find("arxiv:journal_ref", NS)
            journal = journal_el.text if journal_el is not None else "arXiv Preprint"

            articles.append({
                "title": title,
                "authors": author_str or "Autores no disponibles",
                "journal": journal,
                "pubdate": pubdate,
                "abstract": summary or "Resumen no disponible",
                "doi": f"DOI: {doi}" if doi else f"arXiv: {arxiv_id}" if arxiv_id else "",
                "url": url or f"https://arxiv.org/abs/{arxiv_id}",
                "source_label": self.source_label,
            })

        total_pages = max(1, (total + limit - 1) // limit) if total else 1
        return SearchResult(articles, total, page, total_pages,
                            self.source, self.source_label)
