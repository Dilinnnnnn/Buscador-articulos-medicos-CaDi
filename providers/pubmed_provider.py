import os
import requests
import xml.etree.ElementTree as ET
from .base import ArticleProvider, SearchResult

API_KEY = "2f850568e99e0a6f818fb945bc1ebbaec309"
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


class PubMedProvider(ArticleProvider):
    source = "pubmed"
    source_label = "PubMed (NIH)"

    def buscar(self, query, page=1):
        retmax = 20
        retstart = (page - 1) * retmax

        try:
            search_resp = requests.get(f"{BASE_URL}esearch.fcgi", params={
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": retmax,
                "retstart": retstart,
                "api_key": API_KEY,
                "sort": "relevance",
            }, timeout=15)
            search_resp.raise_for_status()
            search_data = search_resp.json()
        except Exception as e:
            return SearchResult([], 0, page, 0, self.source, self.source_label,
                                error=f"Error en PubMed: {e}")

        total = int(search_data["esearchresult"]["count"])
        pmids = [p for p in search_data["esearchresult"]["idlist"] if p]

        if not pmids:
            return SearchResult([], total, page, max(1, (total + 19) // 20),
                                self.source, self.source_label)

        try:
            summary_resp = requests.get(f"{BASE_URL}esummary.fcgi", params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json",
                "api_key": API_KEY,
            }, timeout=15)
            summary_resp.raise_for_status()
            summary_data = summary_resp.json()["result"]
        except Exception as e:
            return SearchResult([], total, page, max(1, (total + 19) // 20),
                                self.source, self.source_label,
                                error=f"Error al obtener detalles: {e}")

        try:
            fetch_resp = requests.get(f"{BASE_URL}efetch.fcgi", params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "api_key": API_KEY,
            }, timeout=15)
            fetch_resp.raise_for_status()
            root = ET.fromstring(fetch_resp.content)
        except Exception:
            root = None

        abstracts = {}
        if root is not None:
            for article in root.findall(".//PubmedArticle"):
                pmid_elem = article.find(".//PMID")
                if pmid_elem is None or not pmid_elem.text:
                    continue
                pmid = pmid_elem.text
                abstract_el = article.find(".//Abstract")
                if abstract_el is None:
                    continue
                parts = []
                for at in abstract_el.findall("AbstractText"):
                    text = "".join(at.itertext()).strip()
                    if text:
                        parts.append(text)
                abstracts[pmid] = " ".join(parts)

        articles = []
        for pmid in pmids:
            paper = summary_data.get(str(pmid)) or summary_data.get(pmid)
            if not paper:
                continue
            authors = paper.get("authors") or []
            author_names = [a.get("name", "") for a in authors[:3]]
            author_str = ", ".join(author_names)
            if len(authors) > 3:
                author_str += " et al."

            articles.append({
                "title": paper.get("title", "Sin título"),
                "authors": author_str or "Autores no disponibles",
                "journal": paper.get("source", "Journal no disponible"),
                "pubdate": paper.get("pubdate", ""),
                "abstract": abstracts.get(pmid, "Resumen no disponible"),
                "doi": paper.get("elocationid", ""),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "source_label": self.source_label,
            })

        total_pages = max(1, (total + retmax - 1) // retmax)
        return SearchResult(articles, total, page, total_pages,
                            self.source, self.source_label)
