from abc import ABC, abstractmethod


class SearchResult:
    def __init__(self, articles, total, page, pages, source, source_label, error=None):
        self.articles = articles
        self.total = total
        self.page = page
        self.pages = pages
        self.source = source
        self.source_label = source_label
        self.error = error


class ArticleProvider(ABC):
    source = ""
    source_label = ""

    @abstractmethod
    def buscar(self, query: str, page: int = 1) -> SearchResult:
        pass
