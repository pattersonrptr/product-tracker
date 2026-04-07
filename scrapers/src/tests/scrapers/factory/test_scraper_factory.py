import json
import os
import tempfile
from unittest.mock import patch

import pytest

from src.scrapers.enjoei import EnjoeiScraper
from src.scrapers.estante_virtual import EstanteVirtualScraper
from src.scrapers.factory.scraper_factory import ScraperFactory
from src.scrapers.interfaces.scraper_interface import ScraperInterface
from src.scrapers.mercado_livre import MercadoLivreScraper
from src.scrapers.mixins.rotating_user_agent_mixin import (
    RotatingUserAgentMixin,
)
from src.scrapers.olx import OLXScraper

# ---------------------------------------------------------------------------
# ScraperFactory
# ---------------------------------------------------------------------------


def test_factory_creates_enjoei():
    scraper = ScraperFactory.create_scraper("enjoei")
    assert isinstance(scraper, EnjoeiScraper)


def test_factory_creates_olx():
    scraper = ScraperFactory.create_scraper("olx")
    assert isinstance(scraper, OLXScraper)


def test_factory_creates_mercado_livre():
    scraper = ScraperFactory.create_scraper("mercado_livre")
    assert isinstance(scraper, MercadoLivreScraper)


def test_factory_creates_estante_virtual():
    scraper = ScraperFactory.create_scraper("estante_virtual")
    assert isinstance(scraper, EstanteVirtualScraper)


def test_factory_is_case_insensitive():
    scraper = ScraperFactory.create_scraper("ENJOEI")
    assert isinstance(scraper, EnjoeiScraper)


def test_factory_raises_for_unknown_scraper():
    with pytest.raises(ValueError, match="Not supported scraper"):
        ScraperFactory.create_scraper("unknown_site")


def test_factory_all_scrapers_implement_interface():
    for name in ["enjoei", "olx", "mercado_livre", "estante_virtual"]:
        scraper = ScraperFactory.create_scraper(name)
        assert isinstance(scraper, ScraperInterface)


# ---------------------------------------------------------------------------
# ScraperInterface — abstract contract
# ---------------------------------------------------------------------------


def test_scraper_interface_cannot_be_instantiated():
    with pytest.raises(TypeError):
        ScraperInterface()  # type: ignore[abstract]


def test_scraper_interface_concrete_subclass_must_implement_all_methods():
    class Incomplete(ScraperInterface):
        def search(self, search_term):
            return []

        # Missing scrape_data and update_data

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_scraper_interface_concrete_subclass_works_when_complete():
    class Complete(ScraperInterface):
        def search(self, search_term):
            return []

        def scrape_data(self, url):
            return {}

        def update_data(self, product):
            return product

    obj = Complete()
    assert obj.search("x") == []
    assert obj.scrape_data("http://x.com") == {}
    assert obj.update_data({"id": 1}) == {"id": 1}


# ---------------------------------------------------------------------------
# RotatingUserAgentMixin
# ---------------------------------------------------------------------------


class _ConcreteRotating(RotatingUserAgentMixin):
    """Minimal concrete class to test the mixin."""

    pass


def test_get_random_user_agent_returns_string_when_file_exists():
    agents = ["Agent/1.0", "Agent/2.0", "Agent/3.0"]
    with patch.object(_ConcreteRotating, "_load_user_agents", return_value=agents):
        obj = _ConcreteRotating()
        result = obj.get_random_user_agent()
        assert result in agents


def test_get_random_user_agent_returns_none_when_no_agents():
    with patch.object(_ConcreteRotating, "_load_user_agents", return_value=[]):
        obj = _ConcreteRotating()
        assert obj.get_random_user_agent() is None


def test_load_user_agents_from_valid_file():
    agents = ["Mozilla/5.0", "Chrome/90"]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(agents, f)
        tmp_path = f.name

    try:
        with patch.object(
            _ConcreteRotating, "_get_user_agents_file_path", return_value=tmp_path
        ):
            obj = _ConcreteRotating()
            assert obj._user_agents == agents
    finally:
        os.unlink(tmp_path)


def test_load_user_agents_file_not_found_returns_empty():
    with patch.object(
        _ConcreteRotating,
        "_get_user_agents_file_path",
        return_value="/nonexistent/path/agents.json",
    ):
        obj = _ConcreteRotating()
        assert obj._user_agents == []


def test_load_user_agents_invalid_json_returns_empty():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not valid json {{{{")
        tmp_path = f.name

    try:
        with patch.object(
            _ConcreteRotating, "_get_user_agents_file_path", return_value=tmp_path
        ):
            obj = _ConcreteRotating()
            assert obj._user_agents == []
    finally:
        os.unlink(tmp_path)
