import pytest


@pytest.mark.django_db
class TestSeoUsaElDominioPropio:
    def test_robots_apunta_al_sitemap_del_dominio_propio(self, client):
        response = client.get("/robots.txt")
        assert "Sitemap: https://controldegastos.ar/sitemap.xml" in response.content.decode()

    def test_sitemap_lista_urls_del_dominio_propio(self, client):
        content = client.get("/sitemap.xml").content.decode()
        assert "<loc>https://controldegastos.ar/</loc>" in content
        assert "onrender.com" not in content

    def test_landing_declara_el_dominio_propio_como_canonico(self, client):
        content = client.get("/").content.decode()
        assert '<link rel="canonical" href="https://controldegastos.ar">' in content
        assert "onrender.com" not in content
