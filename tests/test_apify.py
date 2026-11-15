"""Fontes pelo Apify, sem rede e sem gastar: um Apify falso devolve itens no formato
documentado de cada coletor."""
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from radar_de_demanda.fontes import apify_fontes as apify  # noqa: E402
import importlib  # noqa: E402

scout_mod = importlib.import_module("radar_de_demanda.agents.scout")

ITENS = {
    "reddit": [
        {"dataType": "post", "title": "Contador cobra caro pra MEI?", "body": "Pago 300 por mês e não sei se vale",
         "url": "https://www.reddit.com/r/brdev/comments/1/x", "communityName": "r/brdev", "upVotes": 12,
         "numberOfComments": 4},
        {"dataType": "comment", "body": "Eu faço tudo sozinho no portal", "url": "https://www.reddit.com/r/brdev/c/2",
         "parsedCommunityName": "brdev"},
        {"dataType": "post", "title": "", "body": ""},
    ],
    "reclame_aqui": [
        {"recordType": "company", "name": "Empresa X"},
        {"recordType": "complaint", "title": "Cobrança indevida", "description": "Cancelei e continuam cobrando",
         "url": "https://www.reclameaqui.com.br/x/cobranca", "companySlug": "x", "statusLabel": "Não respondida",
         "created": "2026-10-01"},
    ],
    "mercado_livre": [
        {"eTituloProduto": "Planner Digital 2027", "novoPreco": "29,90", "quantidadeVendida": 150,
         "zProdutoLink": "https://produto.mercadolivre.com.br/MLB-1", "palavraChave": "planner digital"},
        {"eTituloProduto": "Planner Digital Premium", "novoPreco": "1.299,00", "quantidadeVendida": None,
         "zProdutoLink": "https://produto.mercadolivre.com.br/MLB-2"},
    ],
    "google_trends": [
        {"searchTerm": "contador mei", "interestOverTime_timelineData": [
            {"value": [10]}, {"value": [12]}, {"value": [30]}, {"value": [40]}]},
        {"searchTerm": "sem dado", "interestOverTime_timelineData": []},
    ],
    "meta_ads": [
        {"ad_archive_id": "99", "page_name": "Pagina Exemplo", "is_active": True, "start_date": "2026-09-01",
         "snapshot": {"body": {"text": "Abra sua empresa em 7 dias"}, "link_url": "https://exemplo.invalid"}},
        {"ad_archive_id": "98", "page_name": "Outra", "is_active": False, "start_date": 1756684800,
         "end_date": 1757289600, "snapshot": {"body": {"text": "{{product.brand}}"}, "cards": [{"body": "Card"}]}},
    ],
}


class Resp:
    def __init__(self, dados, status=200):
        self._d, self.status_code = dados, status

    def json(self):
        return self._d

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class ApifyFalso:
    """Imita os 3 pedidos: iniciar o coletor, ler o status e baixar os itens."""

    def __init__(self, fonte, status=200, custo=0.0123):
        self.fonte, self.status, self.custo, self.pedidos = fonte, status, custo, []

    def post(self, url, params=None, json=None, headers=None, timeout=None):
        self.pedidos.append(("post", url, params, json, headers))
        return Resp({"data": {"id": "run1", "status": "SUCCEEDED", "defaultDatasetId": "ds1",
                              "usageTotalUsd": self.custo}}, self.status)

    def get(self, url, params=None, headers=None, timeout=None):
        self.pedidos.append(("get", url, params, None, headers))
        if "/datasets/" in url:
            return Resp(ITENS[self.fonte])
        return Resp({"data": {"id": "run1", "status": "SUCCEEDED", "defaultDatasetId": "ds1",
                              "usageTotalUsd": self.custo}})


@mock.patch.dict(os.environ, {"APIFY_TOKEN": "tk-teste", "APIFY_TETO_USD": "1"})
class TestApify(unittest.TestCase):
    def setUp(self):
        apify.GASTOS.clear()

    def test_reddit_converte_e_descarta_vazio(self):
        s = apify.reddit(["contador mei"], http=ApifyFalso("reddit"))
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0]["fonte"], "reddit:r/brdev")
        self.assertIn("Pago 300", s[0]["texto"])
        self.assertEqual(s[1]["fonte"], "reddit-comment:r/brdev")

    def test_reclame_aqui_so_reclamacao(self):
        s = apify.reclame_aqui(["contabilidade"], http=ApifyFalso("reclame_aqui"))
        self.assertEqual(len(s), 1)
        self.assertTrue(s[0]["texto"].startswith("Cobrança indevida"))

    def test_mercado_livre_preco_brasileiro(self):
        s = apify.mercado_livre(["planner digital"], http=ApifyFalso("mercado_livre"))
        self.assertEqual([x["metadata"]["preco"] for x in s], [29.9, 1299.0])
        est = apify.estatisticas_ml(s)
        self.assertEqual(est["total_vendidos_amostra"], 150)
        self.assertEqual(est["preco_min"], 29.9)

    def test_trends_tendencia(self):
        t = apify.google_trends(["contador mei", "sem dado"], http=ApifyFalso("google_trends"))
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["termo"], "contador mei")
        self.assertEqual(t[0]["tendencia"], "subindo")

    def test_meta_dias_e_card(self):
        a = apify.anuncio_meta(ITENS["meta_ads"][0], hoje=date(2026, 11, 15))
        self.assertEqual(a["dias_rodando"], 75)
        b = apify.anuncio_meta(ITENS["meta_ads"][1], hoje=date(2026, 11, 15))
        self.assertEqual(b["texto"], "Card")
        self.assertEqual(b["dias_rodando"], 7)

    def test_teto_e_token_no_cabecalho(self):
        http = ApifyFalso("reddit")
        apify.reddit(["x"], http=http)
        _, url, params, _, headers = http.pedidos[0]
        self.assertEqual(params["maxTotalChargeUsd"], 0.15)
        self.assertNotIn("token", params)
        self.assertNotIn("tk-teste", url)
        self.assertEqual(headers["Authorization"], "Bearer tk-teste")
        self.assertEqual(apify.GASTOS["reddit"], 0.0123)

    def test_soma_das_fatias_e_o_teto(self):
        self.assertAlmostEqual(sum(f for _, f in apify.ATORES.values()), 1.0)

    def test_token_recusado(self):
        with self.assertRaisesRegex(RuntimeError, "recusou o token"):
            apify.reddit(["x"], http=ApifyFalso("reddit", status=401))


class TestScoutComESemToken(unittest.TestCase):
    def _sem_rede(self):
        return [
            mock.patch.object(scout_mod, "scrape_google_signals", return_value=[]),
            mock.patch.object(scout_mod, "scrape_reddit", return_value=[]),
            mock.patch.object(scout_mod, "scrape_reclame_aqui", return_value=[]),
            mock.patch.object(scout_mod, "buscar_produtos", return_value=[]),
            mock.patch.object(scout_mod, "volume_e_tendencia", return_value=[]),
        ]

    def test_sem_token_vira_link(self):
        with mock.patch.dict(os.environ, {"APIFY_TOKEN": ""}):
            ps = self._sem_rede()
            for p in ps:
                p.start()
            try:
                out = scout_mod.scout(["contador mei"])
            finally:
                for p in ps:
                    p.stop()
        self.assertIsNone(out["apify"])
        self.assertFalse(out["fontes_status"]["reddit"]["ok"])
        self.assertTrue(out["fontes_status"]["reddit"]["links"])

    def test_com_token_usa_apify(self):
        def falso(fonte):
            return lambda *a, **k: apify._converte(ITENS[fonte], {
                "reddit": apify.sinal_reddit, "reclame_aqui": apify.sinal_reclame_aqui,
                "mercado_livre": apify.sinal_mercado_livre, "google_trends": apify.tendencia_trends}[fonte])

        with mock.patch.dict(os.environ, {"APIFY_TOKEN": "tk"}):
            ps = self._sem_rede() + [
                mock.patch.object(apify, "reddit", side_effect=falso("reddit")),
                mock.patch.object(apify, "reclame_aqui", side_effect=falso("reclame_aqui")),
                mock.patch.object(apify, "mercado_livre", side_effect=falso("mercado_livre")),
                mock.patch.object(apify, "google_trends", side_effect=falso("google_trends")),
            ]
            for p in ps:
                p.start()
            try:
                out = scout_mod.scout(["contador mei"])
            finally:
                for p in ps:
                    p.stop()
        st = out["fontes_status"]
        for f in ("reddit", "reclame_aqui", "mercado_livre", "google_trends"):
            self.assertTrue(st[f]["ok"], f)
            self.assertEqual(st[f]["via"], "apify")
        self.assertEqual(out["market"]["total_anuncios_amostra"], 2)
        self.assertIn("contador mei", out["trends"])
        self.assertIsNotNone(out["apify"])


if __name__ == "__main__":
    unittest.main()
