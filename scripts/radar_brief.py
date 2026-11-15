"""Brief conversacional V2 do Radar de Demanda.

6 perguntas guiadas + 1 opcional. Haiku enriquece e completa lacunas.
Salva em data/brief.json.

Uso:
    python scripts/radar_brief.py
"""
from __future__ import annotations
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
BRIEF_PATH = ROOT / "data" / "brief.json"

env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.strip().partition("=")
            os.environ.setdefault(k, v.strip().strip('"').strip("'"))

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("❌ ANTHROPIC_API_KEY não setada. Configure no .env primeiro.")
    sys.exit(1)


CAMINHOS = {
    "a": ("ja_tem_oferta", "Já tenho oferta — quero melhorar e vender mais"),
    "b": ("quer_diversificar", "Já tenho cliente — quero criar nova oferta pra ele"),
    "c": ("comecando_zero", "Estou começando do zero"),
}

FATURAMENTO_ATUAL = {
    "1": "R$0 — tô começando agora",
    "2": "R$1-3.000/mês — primeiras vendas saindo",
    "3": "R$3-10.000/mês — operação inicial",
    "4": "R$10-30.000/mês — estabilizada",
    "5": "R$30-100.000/mês — escalando",
    "6": "R$100.000+/mês — alta escala",
    "7": "Outro (digito o valor)",
}

FATURAMENTO_META = {
    "1": "Meu primeiro R$1.000-3.000/mês (saindo do zero)",
    "2": "R$3.000-10.000/mês (low-ticket digital)",
    "3": "R$10.000-30.000/mês (sweet spot infoproductor)",
    "4": "R$30.000-100.000/mês (escalar)",
    "5": "R$100.000+/mês (high-ticket ou lançamento)",
    "6": "Outro (digito o valor)",
}

CANAIS = {
    "1": "Instagram",
    "2": "YouTube",
    "3": "Lista de email",
    "4": "Anúncio pago (Meta/Google)",
    "5": "WhatsApp",
    "6": "Não sei ainda",
}

DUVIDAS = {
    "1": "Validar se a oferta vende",
    "2": "Achar o nicho certo",
    "3": "Escalar tráfego",
    "4": "Subir o ticket",
    "5": "Criar a primeira oferta",
    "6": "Outro",
}


PROMPT_ENRIQUECER = """Você é Brief Normalizer do Radar de Demanda. ATENÇÃO: você NÃO inventa nada. Apenas normaliza e estrutura o que o cliente disse.

REGRA DE OURO: se o cliente NÃO disse algo (respondeu "não sei", deixou vazio, ou está começando do zero), o campo correspondente DEVE ficar como "a_descobrir_apos_pesquisa". Pesquisa de mercado vem PRIMEIRO, decisões depois.

Cliente respondeu (BRUTO):
- Caminho: {caminho}
- O que faz / quer fazer: {o_que_faz}
- Nicho amplo: {nicho}
- Cliente alvo: {cliente_alvo}
- Faturamento HOJE/mês: {faturamento_atual}
- Faturamento META/mês: {faturamento_meta}
- Canal principal: {canal}
- Dúvida principal: {duvida}

Sua tarefa: gerar JSON com SOMENTE 3 tipos de campo:
1. Cópia normalizada do que ele disse (sem mudar sentido)
2. Cálculos derivados de duas respostas dele (ex: salto = meta - atual)
3. "a_descobrir_apos_pesquisa" pra TUDO que não veio dele

PROIBIDO: inventar produtos/cursos/mentorias que ele não citou. Inventar perfil de cliente que ele não descreveu. Inventar nicho específico que ele não definiu. Inventar termos de busca além dos óbvios extraídos do que ele disse.

```json
{{
  "caminho": "{caminho}",
  "negocio": "frase clara MAS APENAS com palavras que o cliente usou — se ele disse pouco, escreva pouco. Se ele só deu o nicho amplo, repita o nicho amplo aqui. NUNCA expanda pra 'cursos online, mentorias, consultoria' se ele não citou esses formatos.",
  "o_que_vende": "se caminho='c' (começando do zero) OU cliente não citou produto específico → 'a_descobrir_apos_pesquisa'. Caso contrário: copie literal o que ele disse.",
  "faturamento_atual": "valor normalizado preservando o que ele disse (ex: 'R$3.500/mês' ou 'R$0 — começando')",
  "faturamento_meta": "valor normalizado preservando o que ele disse",
  "salto_necessario": "categoria derivada da matemática meta-atual: 'criar primeira oferta' | 'subir ticket' | 'escalar tráfego' | 'estruturar lançamento' | 'manter e otimizar'",
  "ticket_sugerido_para_meta": "a_descobrir_apos_pesquisa (depende do que vai vender, que ainda não foi pesquisado)",
  "cliente_alvo": "se ele disse 'não sei' ou deixou vazio → 'a_descobrir_apos_pesquisa'. Caso contrário: copie literal o que ele disse.",
  "nicho_especifico": "se ele disse 'não sei' ou só citou nicho amplo → 'a_descobrir_apos_pesquisa'. Caso contrário: copie literal.",
  "gargalo": "se cliente disse explicitamente o gargalo → copie. Senão → 'a_descobrir_apos_pesquisa'.",
  "termos_busca": "extraia 2-4 substantivos/expressões LITERAIS do que o cliente disse no campo nicho + o que faz. NUNCA invente termo que ele não usou. Se ele só disse 'marketing digital com IA' → termos='marketing digital, IA, automação' (substantivos contidos na frase dele).",
  "concorrentes": "a_descobrir_apos_pesquisa",
  "canal_principal": "canal que ele escolheu (cópia)",
  "duvida_principal": "dúvida que ele escolheu (cópia) ou '(não informado)'",
  "estagio": "derive APENAS do faturamento atual: 'iniciante' (R$0-3k) | 'intermediario' (R$3-30k) | 'avancado' (R$30k+)"
}}
```

Retorne SOMENTE o JSON."""


def pergunta_aberta(label: str, exemplos: str | None = None) -> str:
    print(f"\n{label}")
    if exemplos:
        print(f"  {exemplos}")
    return input("> ").strip()


def pergunta_escolha(label: str, opcoes: dict[str, str], opcional: bool = False, multipla: bool = False) -> tuple[str, str]:
    print(f"\n{label}")
    for k, v in opcoes.items():
        print(f"  {k}) {v}")
    if multipla:
        print("  💡 Pode escolher MAIS DE UMA — separa com vírgula (ex: 1,4)")
    if opcional:
        print("  (enter pra pular)")
    while True:
        r = input("> ").strip().lower()
        if not r and opcional:
            return ("", "")
        if multipla:
            keys = [k.strip() for k in r.split(",") if k.strip()]
            if keys and all(k in opcoes for k in keys):
                labels = " + ".join(opcoes[k] for k in keys)
                return (",".join(keys), labels)
            print("⚠ opção inválida — escolha entre", ", ".join(opcoes.keys()), "(múltiplas separadas por vírgula)")
            continue
        if r in opcoes:
            return (r, opcoes[r])
        print("⚠ opção inválida — escolha entre", ", ".join(opcoes.keys()))


def _detecta_modo_discovery(respostas: dict) -> bool:
    """Ativa discovery se o brief é vago — cliente ainda procurando o caminho."""
    nicho = (respostas.get("nicho") or "").lower().strip()
    cliente = (respostas.get("cliente_alvo") or "").lower().strip()
    fat_atual = (respostas.get("faturamento_atual") or "").lower().strip()
    duvida = respostas.get("duvida_key", "")
    caminho = respostas.get("caminho_key", "")

    sinais_vago = 0
    if not nicho or len(nicho.split()) < 2 or "não sei" in nicho or "nao sei" in nicho:
        sinais_vago += 1
    if not cliente or "não sei" in cliente or "nao sei" in cliente or len(cliente) < 20:
        sinais_vago += 1
    if "0" in fat_atual or "começ" in fat_atual or "comec" in fat_atual or "não sei" in fat_atual:
        sinais_vago += 1
    if duvida in ("2", "5"):  # achar nicho / criar primeira oferta
        sinais_vago += 1
    if caminho == "c":  # começando do zero
        sinais_vago += 1
    return sinais_vago >= 2


def enriquecer_brief(respostas: dict) -> dict:
    from anthropic import Anthropic
    print("\n🧠 Completando brief com conhecimento de mercado...")

    prompt = PROMPT_ENRIQUECER.format(
        caminho=respostas.get("caminho_label", "?"),
        o_que_faz=respostas.get("o_que_faz", "?"),
        nicho=respostas.get("nicho", "?"),
        cliente_alvo=respostas.get("cliente_alvo", "?"),
        faturamento_atual=respostas.get("faturamento_atual", "?"),
        faturamento_meta=respostas.get("faturamento_meta", "?"),
        canal=respostas.get("canal_label", "?"),
        duvida=respostas.get("duvida_label", "(não informado)"),
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()
    return json.loads(raw)


def mostra_brief(brief: dict) -> None:
    print("\n" + "=" * 60)
    print("📋 BRIEF FINAL")
    print("=" * 60)
    print(f"\n🛤  Caminho: {brief.get('caminho', '?')}")
    print(f"\n🏢 Negócio: {brief.get('negocio', '?')}")
    print(f"\n💼 O que vende: {brief.get('o_que_vende', '?')}")
    print(f"\n🎯 Nicho específico: {brief.get('nicho_especifico', '?')}")
    print(f"\n👥 Cliente alvo: {brief.get('cliente_alvo', '?')}")
    print(f"\n💰 Faturamento HOJE: {brief.get('faturamento_atual', '?')}")
    print(f"🎯 Faturamento META: {brief.get('faturamento_meta', '?')}")
    print(f"⚡ Salto necessário: {brief.get('salto_necessario', '?')}")
    print(f"💡 Ticket sugerido pra meta: {brief.get('ticket_sugerido_para_meta', '?')}")
    print(f"\n📱 Canal principal: {brief.get('canal_principal', '?')}")
    print(f"\n❓ Dúvida principal: {brief.get('duvida_principal', '(não informado)')}")
    print(f"\n🔥 Gargalo derivado: {brief.get('gargalo', '?')}")
    print(f"\n🔍 Termos a pesquisar: {brief.get('termos_busca', '?')}")
    print("\n" + "=" * 60)


def main():
    print("\n" + "=" * 60)
    print("📋 RADAR DE DEMANDA — Brief: 6 perguntas pra te entregar dossiê sob medida")
    print("=" * 60)
    print("\nResponda com calma. Quanto mais específico, melhor o dossiê.")

    # 1 — caminho do dossiê
    caminho_key, caminho_label = pergunta_escolha(
        "🎯 1. Você já tem oferta no ar ou está começando?",
        {
            "a": "Já tenho oferta — quero melhorar e vender mais",
            "b": "Já tenho cliente — quero criar nova oferta pra ele",
            "c": "Estou começando do zero",
        },
    )

    # 2 — o que faz
    o_que_faz = pergunta_aberta(
        "💬 2. Me conta em 1-2 frases o que você faz (ou quer fazer):",
        "Ex: 'crio cursos online de emagrecimento pra mulheres na menopausa'\n  💡 Se ainda não sabe, digite: não sei",
    )

    # 3 — nicho específico
    nicho = pergunta_aberta(
        "🎯 3. Qual seu nicho ou sub-nicho específico?",
        "Ex: 'emagrecimento mulheres 40+', 'yoga pra ansiedade', 'finanças pra MEI'\n  💡 Se ainda não escolheu nicho, digite: não sei (Radar de Demanda vai te ajudar a descobrir)",
    )

    # 3b — se "não sei", pede ÁREA AMPLA pro Scout começar a buscar
    _nicho_vazio = (nicho or "").strip().lower() in ("", "não sei", "nao sei", "?", "-")
    if _nicho_vazio:
        print("\n   ✋ Tudo bem não saber o sub-nicho ainda — Radar de Demanda vai descobrir.")
        print("   Mas pra começar a pesquisar, preciso de UMA ÁREA AMPLA (chapéu grande).")
        area_ampla = pergunta_escolha(
            "🧭 3b. Qual ÁREA AMPLA te chama atenção? (Radar de Demanda descobre o sub-nicho depois)",
            {
                "1": "Marketing digital / vendas / IA pra negócios",
                "2": "Saúde feminina / bem-estar / emagrecimento",
                "3": "Produtividade / desenvolvimento pessoal",
                "4": "Finanças pessoais / investimentos / MEI",
                "5": "Fitness / esporte / treino em casa",
                "6": "Educação infantil / parentalidade",
                "7": "Negócios online / empreendedorismo",
                "8": "Relacionamento / desenvolvimento espiritual",
                "9": "Outra",
            },
        )[1]
        if "Outra" in area_ampla:
            area_ampla = pergunta_aberta(
                "   Digite a área ampla:",
                "Ex: 'pets', 'culinária saudável', 'tecnologia para idosos'",
            )
        nicho = area_ampla  # usado como seed pelo Scout

    # 4 — cliente alvo
    cliente_alvo = pergunta_aberta(
        "👥 4. Quem é seu cliente? (idade, gênero, contexto)",
        "Ex: 'mulheres 40-60 anos, classe B/C, frustradas com dietas que não funcionam'\n  💡 Se ainda não sabe, digite: não sei",
    )

    # 5 — faturamento HOJE (escolha + abertura pra "outro")
    fat_atual_key, fat_atual_label = pergunta_escolha(
        "💰 5. Quanto você fatura HOJE por mês?",
        FATURAMENTO_ATUAL,
    )
    if fat_atual_key == "7":
        faturamento_atual = pergunta_aberta(
            "   Digite quanto fatura:",
            "Ex: 'R$5.500 mês passado', 'oscila entre R$8-12k'",
        )
    else:
        faturamento_atual = fat_atual_label

    # 6 — faturamento META (escolha + abertura pra "outro")
    fat_meta_key, fat_meta_label = pergunta_escolha(
        "🎯 6. Pra quanto quer faturar por mês?",
        FATURAMENTO_META,
    )
    if fat_meta_key == "6":
        faturamento_meta = pergunta_aberta(
            "   Digite quanto quer faturar:",
            "Ex: 'R$50.000/mês', 'R$500k em 12 meses'",
        )
    else:
        faturamento_meta = fat_meta_label

    # 7 — canal (múltipla escolha)
    canal_key, canal_label = pergunta_escolha(
        "📱 7. Onde você vende (ou quer vender)?",
        CANAIS,
        multipla=True,
    )

    # 8 — dúvida (opcional, múltipla)
    duvida_key, duvida_label = pergunta_escolha(
        "⭐ 8. Qual sua maior dúvida AGORA? (opcional)",
        DUVIDAS,
        opcional=True,
        multipla=True,
    )

    # Ticket é derivado das 2 perguntas anteriores
    ticket = f"hoje: {faturamento_atual} | meta: {faturamento_meta}"

    respostas = {
        "caminho_key": caminho_key,
        "caminho_label": caminho_label,
        "o_que_faz": o_que_faz,
        "nicho": nicho,
        "cliente_alvo": cliente_alvo,
        "faturamento_atual": faturamento_atual,
        "faturamento_atual_faixa": fat_atual_key,
        "faturamento_meta": faturamento_meta,
        "faturamento_meta_faixa": fat_meta_key,
        "ticket": ticket,
        "canal_key": canal_key,
        "canal_label": canal_label,
        "duvida_key": duvida_key,
        "duvida_label": duvida_label,
    }

    brief = enriquecer_brief(respostas)

    while True:
        mostra_brief(brief)
        escolha = input("\n✅ Tá certo? [s = salvar / r = refazer do zero] > ").strip().lower()
        if escolha in ("s", "sim", ""):
            break
        elif escolha in ("r", "refazer"):
            print("\nReiniciando...")
            return main()

    brief["caminho_codigo"] = CAMINHOS.get(caminho_key, ("?", "?"))[0]
    brief["respostas_brutas"] = respostas
    brief["criado_em"] = datetime.now().isoformat()
    brief["discovery_mode"] = _detecta_modo_discovery(respostas)
    if brief["discovery_mode"]:
        print("\n🔍 MODO DISCOVERY ativado — você ainda tá explorando.")
        print("   Quando rodar o dossiê, Radar de Demanda vai pausar antes das ofertas")
        print("   pra te mostrar as oportunidades quentes e deixar VOCÊ escolher.")

    BRIEF_PATH.parent.mkdir(parents=True, exist_ok=True)
    BRIEF_PATH.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ Brief salvo em: {BRIEF_PATH}")
    print("\n" + "─" * 60)
    print("📊 PRÓXIMO PASSO — gerar seu primeiro dossiê:")

    # Detecta se nicho é vago/ausente e sugere área ampla pra Scout começar
    nicho_para_busca = (nicho or "").strip().lower()
    nicho_invalido = (
        not nicho_para_busca
        or nicho_para_busca in ("não sei", "nao sei", "?", "-")
        or len(nicho_para_busca.split()) < 2
    )
    if nicho_invalido:
        print('\n⚠ Você marcou "não sei" no nicho. Mesmo assim, o Radar de Demanda precisa de uma')
        print("   ÁREA AMPLA pra começar a pesquisar (Scout precisa de palavra-chave).")
        print("\n   Escolha o chapéu grande mais próximo do que te chama atenção:")
        print('     python scripts/radar_run.py "marketing digital"')
        print('     python scripts/radar_run.py "saúde feminina"')
        print('     python scripts/radar_run.py "produtividade"')
        print('     python scripts/radar_run.py "finanças pessoais"')
        print('     python scripts/radar_run.py "fitness"')
        print('     python scripts/radar_run.py "negócios online"')
        print("\n   💡 Radar de Demanda vai descobrir os SUB-nichos quentes dentro da área e te")
        print("      mostrar antes de propor ofertas (modo Discovery).")
    else:
        print(f'\n   python scripts/radar_run.py "{nicho}"')
    print("\n⏱  Pode levar vários minutos. Custo: 2 chamadas ao Claude Sonnet e de 1 a 4 ao Haiku;")
    print("   confira o gasto real no painel da Anthropic (console.anthropic.com, em Usage).")
    print("   Não é o computador travando — são os agentes trabalhando.")
    print("\n💡 Dica: rode de novo a cada 14-21 dias pra acompanhar mudanças")
    print("   do mercado. Demanda BR muda rápido — quem roda mensal sai na")
    print("   frente da concorrência.")
    print("─" * 60)


if __name__ == "__main__":
    main()
