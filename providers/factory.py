from .pubmed_provider import PubMedProvider
from .semantic_scholar_provider import SemanticScholarProvider
from .springer_provider import SpringerNatureProvider
from .openalex_provider import OpenAlexProvider
from .europe_pmc_provider import EuropePMCProvider
from .arxiv_provider import ArXivProvider
from .core_provider import COREProvider


class ProviderFactory:
    _instances = {}

    @classmethod
    def get(cls, source):
        if not cls._instances:
            cls._instances["pubmed"] = PubMedProvider()
            cls._instances["semantic"] = SemanticScholarProvider()
            cls._instances["springer"] = SpringerNatureProvider()
            cls._instances["openalex"] = OpenAlexProvider()
            cls._instances["europepmc"] = EuropePMCProvider()
            cls._instances["arxiv"] = ArXivProvider()
            cls._instances["core"] = COREProvider()
        return cls._instances.get(source, cls._instances["pubmed"])
