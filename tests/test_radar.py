"""Testes sem rede e sem gastar com modelo.

Rodar da raiz do repositório:
    python -m unittest discover -s tests
"""
from __future__ import annotations

import builtins
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
DADOS = Path(__file__).resolve().parent / "dados"
sys.path.insert(0, str(ROOT))

import radar_de_demanda.agents  # noqa: E402,F401
analyst_mod = sys.modules["radar_de_demanda.agents.analyst"]  # o pacote exporta a função com o mesmo nome
from radar_de_demanda.agents.analyst import (  # noqa: E402
    MIN_FRASES,
    SinaisInsuficientes,
    frases_reais,
)


def _scout_gravado() -> dict:
    """Coleta real gravada em 15/11/2026: Google trouxe 22 sinais, o resto falhou."""
    return json.loads((DADOS / "scout_advocacia_tributaria.json").read_text(encoding="utf-8"))


def _carrega_radar_run():
    """Importa scripts/radar_run.py como módulo, com chave falsa (nada é chamado de verdade)."""
    os.environ.setdefault("ANTHROPIC_API_KEY", "chave-falsa-de-teste")
    spec = importlib.util.spec_from_file_location("radar_run", ROOT / "scripts" / "radar_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCampoSinal(unittest.TestCase):
    def test_google_grava_em_sinal_e_o_analyst_le(self):
        sinais = [{"sinal": "como abrir escritório de advocacia", "seed": "advocacia",
                   "fonte": "autocomplete:como advocacia"}]
        linhas = frases_reais(sinais)
        self.assertEqual(len(linhas), 1)
        self.assertIn("como abrir escritório de advocacia", linhas[0])
        self.assertTrue(linhas[0].startswith("[autocomplete:"))

    def test_aceita_texto_text_e_sinal_e_ignora_vazio(self):
        sinais = [
            {"texto": "reclamação do reclame aqui", "fonte": "reclame_aqui"},
            {"text": "comentário antigo", "fonte": "youtube"},
            {"sinal": "busca do google", "fonte": "autocomplete:x"},
            {"texto": "   ", "fonte": "reddit"},
            {"fonte": "mercado_livre"},
        ]
        self.assertEqual(len(frases_reais(sinais)), 3)

    def test_coleta_gravada_do_google_vira_frase(self):
        scout = _scout_gravado()
        self.assertTrue(all("sinal" in s for s in scout["signals"]))
        self.assertEqual(len(frases_reais(scout["signals"])), len(scout["signals"]))


class TestTravaMinimoDeFrases(unittest.TestCase):
    def test_abaixo_do_minimo_para_antes_do_modelo(self):
        scout = _scout_gravado()
        scout["signals"] = scout["signals"][: MIN_FRASES - 1]
        with mock.patch.object(analyst_mod, "Anthropic") as anthropic, redirect_stdout(io.StringIO()):
            with self.assertRaises(SinaisInsuficientes) as ctx:
                analyst_mod.analyst(scout)
        anthropic.assert_not_called()
        msg = str(ctx.exception)
        self.assertIn(f"Só {MIN_FRASES - 1} frase", msg)
        for fonte in ("Reddit", "Reclame Aqui", "Mercado Livre", "Google Trends"):
            self.assertIn(fonte, msg)
        self.assertIn("Google Autocomplete", msg)  # fonte que funcionou também aparece

    def test_sem_sinal_nenhum_para(self):
        with mock.patch.object(analyst_mod, "Anthropic") as anthropic, redirect_stdout(io.StringIO()):
            with self.assertRaises(SinaisInsuficientes):
                analyst_mod.analyst({"signals": [], "fontes_status": {}})
        anthropic.assert_not_called()

    def test_com_dado_suficiente_chama_o_modelo_com_as_frases(self):
        scout = _scout_gravado()
        resposta = mock.Mock()
        resposta.content = [mock.Mock(text=json.dumps({"dores": [], "personas": []}))]
        with mock.patch.object(analyst_mod, "Anthropic") as anthropic, redirect_stdout(io.StringIO()):
            anthropic.return_value.messages.create.return_value = resposta
            analyst_mod.analyst(scout)
        prompt = anthropic.return_value.messages.create.call_args.kwargs["messages"][0]["content"]
        self.assertIn(scout["signals"][0]["sinal"], prompt)


class TestSemPausa(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with redirect_stdout(io.StringIO()):
            cls.rr = _carrega_radar_run()

    def test_deve_pausar(self):
        tty = mock.Mock(isatty=mock.Mock(return_value=True))
        nao_tty = mock.Mock(isatty=mock.Mock(return_value=False))
        brief = {"discovery_mode": True}
        self.assertTrue(self.rr.deve_pausar(brief, False, tty))
        self.assertFalse(self.rr.deve_pausar(brief, True, tty))       # --sem-pausa
        self.assertFalse(self.rr.deve_pausar(brief, False, nao_tty))  # Claude Code / pipe
        self.assertFalse(self.rr.deve_pausar({"discovery_mode": False}, False, tty))

    def _roda_main(self, argv, stdin_tty: bool):
        rr = self.rr
        scout_out = _scout_gravado()
        analyst_out = {"dores": [{"rank": 1, "dor": "x", "pain_score": 70}],
                       "personas": [{"id": "P1", "nome": "Persona", "dores_relacionadas_ranks": [1]}],
                       "vocabulario_real": []}
        brief = {"negocio": "teste", "discovery_mode": True, "faturamento_atual": "R$0",
                 "faturamento_meta": "R$10k", "salto_necessario": "criar"}
        fake_stdin = mock.Mock(isatty=mock.Mock(return_value=stdin_tty))

        def input_proibido(*a, **k):
            raise AssertionError("input() foi chamado com --sem-pausa")

        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(rr, "ROOT", Path(tmp)), \
                mock.patch.object(rr, "HIST_DIR", Path(tmp) / "data" / "historico"), \
                mock.patch.object(rr, "carrega_brief", return_value=brief), \
                mock.patch.object(rr, "router", return_value={"fontes_ativas": {}}), \
                mock.patch.object(rr, "scout", return_value=scout_out), \
                mock.patch.object(rr, "analyst", return_value=analyst_out), \
                mock.patch.object(rr, "hunter", return_value={}), \
                mock.patch.object(rr, "info_hunter", return_value={}), \
                mock.patch.object(rr, "spy", return_value={}), \
                mock.patch.object(rr, "strategist", return_value={}), \
                mock.patch.object(rr, "validator", return_value={"ofertas": []}), \
                mock.patch.object(rr, "gerar_landing_agent", return_value={"markdown": "# landing"}) as landing, \
                mock.patch.object(rr, "discovery_pause", wraps=rr.discovery_pause) as pausa, \
                mock.patch.object(builtins, "input", side_effect=input_proibido) as inp, \
                mock.patch.object(sys, "stdin", fake_stdin), \
                redirect_stdout(io.StringIO()):
            rr.main(argv)
            md = next((Path(tmp) / "data" / "dossies").glob("*.md")).read_text(encoding="utf-8")
        return inp, pausa, landing, md

    def test_sem_pausa_nao_chama_input(self):
        inp, pausa, landing, _ = self._roda_main(["advocacia tributária", "--sem-pausa"], stdin_tty=True)
        inp.assert_not_called()
        pausa.assert_not_called()
        landing.assert_not_called()  # landing desligada por padrão

    def test_terminal_nao_interativo_nao_chama_input(self):
        inp, pausa, _, _ = self._roda_main(["advocacia tributária"], stdin_tty=False)
        inp.assert_not_called()
        pausa.assert_not_called()

    def test_dossie_lista_fontes_indisponiveis_com_links(self):
        _, _, _, md = self._roda_main(["advocacia tributária", "--sem-pausa"], stdin_tty=False)
        self.assertIn("Fontes indisponíveis hoje", md)
        self.assertIn("https://www.reclameaqui.com.br/busca/?q=", md)
        self.assertIn("https://www.reddit.com/search/?q=", md)
        self.assertNotIn("Pare de adivinhar", md)
        self.assertIn("**Negócio:**", md)

    def test_landing_so_com_flag(self):
        _, _, landing, _ = self._roda_main(["advocacia tributária", "--sem-pausa", "--landing"], stdin_tty=False)
        landing.assert_called_once()


if __name__ == "__main__":
    unittest.main()
