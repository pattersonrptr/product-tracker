from src.scrapers.enjoei import EnjoeiScraper
from src.scrapers.estante_virtual import EstanteVirtualScraper
from src.scrapers.interfaces.scraper_interface import ScraperInterface
from src.scrapers.mercado_livre import MercadoLivreScraper
from src.scrapers.olx import OLXScraper


class ScraperFactory:
    @staticmethod
    def create_scraper(name: str) -> ScraperInterface:
        match name.lower():
            case "olx":
                return OLXScraper()
            case "enjoei":
                return EnjoeiScraper()
            case "estante_virtual":
                return EstanteVirtualScraper()
            case "mercado_livre":
                return MercadoLivreScraper()
            case _:
                raise ValueError(f"Error: Not supported scraper '{name}'.")
