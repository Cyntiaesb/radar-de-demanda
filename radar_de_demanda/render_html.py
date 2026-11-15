"""Renderiza dossiê Radar de Demanda como HTML standalone (dark theme, sem JS externo).

Mesmo conteúdo do .md, mas com cards, tabelas estilizadas e barras CSS pra scores.
Cliente abre o .html em qualquer navegador, vê visual de dashboard, imprime se quiser.
"""
from __future__ import annotations
from datetime import datetime
from html import escape


def _bar(value: int, max_value: int = 100, color: str = "#ef4444") -> str:
    pct = max(0, min(100, int((value / max_value) * 100)))
    return (
        f'<div class="bar"><div class="bar-fill" style="width:{pct}%;background:{color}">'
        f'<span class="bar-label">{value}</span></div></div>'
    )


def _semaforo(score: int) -> str:
    if score >= 75:
        return "🟢"
    if score >= 50:
        return "🟡"
    return "🔴"


def _intensidade(s: str) -> tuple[str, str]:
    s = (s or "").lower()
    return {
        "alta": ("🩸", "#ef4444"),
        "media": ("🔥", "#f59e0b"),
        "baixa": ("🟡", "#eab308"),
    }.get(s, ("•", "#6b7280"))


def render_html(
    nicho: str,
    brief: dict,
    routing: dict,
    analyst_out: dict,
    hunter_out: dict,
    info_hunter_out: dict,
    spy_out: dict,
    strategist_out: dict,
    validator_out: dict,
    scout_meta: dict,
    landing_out: dict | None = None,
) -> str:
    e = escape
    fat_atual = brief.get("faturamento_atual", "?")
    fat_meta = brief.get("faturamento_meta", "?")
    salto = brief.get("salto_necessario", "?")
    persona_escolhida = brief.get("persona_escolhida") or {}
    fontes_ativas = [k for k, v in routing.get("fontes_ativas", {}).items() if v]

    parts: list[str] = []
    parts.append("<!doctype html><html lang='pt-BR'><head>")
    parts.append("<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>")
    parts.append(f"<title>Dossiê Radar de Demanda — {e(nicho.title())}</title>")
    parts.append("<link rel='preconnect' href='https://fonts.googleapis.com'>")
    parts.append("<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>")
    parts.append("<link href='https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap' rel='stylesheet'>")
    parts.append("<style>" + _CSS + "</style>")
    parts.append("</head><body>")

    # ---- Header ----
    parts.append("<header class='hero'>")
    parts.append(f"<div class='brand'>RADAR DE DEMANDA</div>")
    parts.append(f"<h1>Dossiê — {e(nicho.title())}</h1>")
    parts.append(f"<p class='subtitle'>{e(brief.get('negocio', '?'))}</p>")
    parts.append("<div class='meta-grid'>")
    parts.append(f"<div class='meta-card'><label>Gerado em</label><span>{datetime.now().strftime('%d/%m/%Y %H:%M')}</span></div>")
    parts.append(f"<div class='meta-card'><label>Categoria</label><span>{e(routing.get('categoria', '?'))}</span></div>")
    parts.append(f"<div class='meta-card'><label>Sinais coletados</label><span>{scout_meta.get('total_signals', '?')}</span></div>")
    parts.append(f"<div class='meta-card'><label>Fontes ativas</label><span>{len(fontes_ativas)}</span></div>")
    parts.append("</div>")
    parts.append("<div class='salto-card'>")
    parts.append(f"<span class='salto-label'>💰 Salto financeiro</span>")
    parts.append(f"<span class='salto-from'>{e(fat_atual)}</span>")
    parts.append(f"<span class='salto-arrow'>→</span>")
    parts.append(f"<span class='salto-to'>{e(fat_meta)}</span>")
    parts.append(f"<span class='salto-tag'>{e(salto)}</span>")
    parts.append("</div>")
    parts.append("</header>")

    parts.append("<main>")

    # ---- Metodologia ----
    parts.append(_section("🧭 Como o Radar de Demanda chegou nessas conclusões", _metodologia_html(scout_meta, fontes_ativas, fat_atual, fat_meta)))

    if persona_escolhida:
        parts.append("<div class='banner-persona'>")
        parts.append(f"🎯 <strong>Você escolheu atacar a persona:</strong> {e(persona_escolhida.get('nome', '?'))}. ")
        parts.append("Todas as ofertas abaixo estão calibradas pra ELA.")
        parts.append("</div>")

    # ---- Personas ----
    personas = analyst_out.get("personas", []) or []
    if personas:
        cards = []
        for p in personas:
            emoji, color = _intensidade(p.get("intensidade_dor", ""))
            picked = persona_escolhida.get("id") == p.get("id")
            badge = "<span class='picked'>★ ESCOLHIDA</span>" if picked else ""
            cards.append(f"""
            <div class='persona-card {'picked-card' if picked else ''}' style='border-left-color:{color}'>
                <div class='persona-header'>
                    <span class='persona-id'>{e(p.get('id','?'))}</span>
                    <span class='persona-intensity'>{emoji} {e(p.get('intensidade_dor','?'))}</span>
                    {badge}
                </div>
                <h3>{e(p.get('nome','?'))}</h3>
                <p class='persona-desc'>{e(p.get('descricao_uma_linha','?'))}</p>
                <div class='persona-stats'>
                    <span>💰 {e(p.get('ticket_alvo_estimado','?'))}</span>
                    <span>🎯 {len(p.get('dores_relacionadas_ranks',[]))} dor(es)</span>
                </div>
                <p class='persona-opp'>💡 {e(p.get('oportunidade_sintese','?'))}</p>
            </div>""")
        parts.append(_section("👥 Personas detectadas", f"<div class='persona-grid'>{''.join(cards)}</div>"))

    # ---- Dores ----
    dores = analyst_out.get("dores", [])[:10]
    if dores:
        rows = []
        for d in dores:
            pain = d.get("pain_score", 0)
            color = "#ef4444" if pain >= 80 else "#f59e0b" if pain >= 60 else "#eab308" if pain >= 40 else "#6b7280"
            emoji = "🩸" if pain >= 80 else "🔥" if pain >= 60 else "🟡"
            rows.append(f"""
            <tr>
                <td>{d.get('rank','?')}</td>
                <td><strong>{e(d.get('dor','?'))}</strong><br><span class='muted'>"{e((d.get('frase_real_publico') or '')[:120])}"</span></td>
                <td>{_bar(pain, 100, color)}</td>
                <td>{emoji} {e(d.get('categoria','?'))}</td>
            </tr>""")
        table = f"""<table class='data-table'>
            <thead><tr><th>#</th><th>Dor + frase real</th><th>Pain Score 0-100</th><th>Categoria</th></tr></thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
        <p class='note'><strong>Resumo:</strong> {e(analyst_out.get('resumo_executivo',''))}</p>"""
        parts.append(_section("🩸 Bleeding Neck — Dores mais quentes", table))

    # ---- Math da meta ----
    math = strategist_out.get("math_da_meta") or {}
    if math.get("caminhos"):
        cards = []
        recomendado = math.get("caminho_recomendado", "")
        for c in math.get("caminhos", []):
            opc = c.get("opcao", "?")
            destaque = "destaque" if recomendado == opc else ""
            via_color = {"alta": "#10b981", "media": "#f59e0b", "baixa": "#ef4444"}.get((c.get("viabilidade") or "").lower(), "#6b7280")
            cards.append(f"""
            <div class='math-card {destaque}'>
                <div class='math-opt'>Opção {e(opc)}</div>
                <div class='math-headline'>{e(c.get('descricao','?'))}</div>
                <div class='math-numbers'>
                    <span>Ticket <strong>{e(c.get('ticket','?'))}</strong></span>
                    <span>Vendas <strong>{c.get('vendas_por_mes','?')}/mês</strong></span>
                </div>
                <div class='math-via' style='color:{via_color}'>Viabilidade: <strong>{e(c.get('viabilidade','?'))}</strong></div>
                <p class='muted'>{e(c.get('porque','?'))}</p>
            </div>""")
        rec_note = f"<p class='note'>🎯 <strong>Caminho recomendado:</strong> Opção {e(recomendado)} — mais realista pro seu estágio ({e(salto)}).</p>" if recomendado else ""
        parts.append(_section(f"🧮 Math da Meta — Como chegar em {e(fat_meta)}", f"<div class='math-grid'>{''.join(cards)}</div>{rec_note}"))

    # ---- Escalonamento ----
    escal = strategist_out.get("escalonamento_formatos") or {}
    if escal.get("niveis"):
        cards = []
        cores = {"isca": "#3b82f6", "entrada": "#10b981", "core": "#f59e0b", "premium": "#a855f7"}
        for n in escal.get("niveis", []):
            niv = (n.get("nivel") or "?").lower()
            cor = cores.get(niv, "#6b7280")
            cards.append(f"""
            <div class='escal-card' style='border-top:4px solid {cor}'>
                <div class='escal-niv' style='color:{cor}'>{e(niv.upper())}</div>
                <h4>{e(n.get('nome','?'))}</h4>
                <div class='escal-ticket'>{e(n.get('ticket','?'))}</div>
                <p class='muted'><strong>{e(n.get('formato','?'))}</strong></p>
                <p>{e(n.get('promessa','?'))}</p>
                <p class='muted'>👤 {e(n.get('perfil_comprador','?'))}</p>
                <p class='muted'>⏱ {e(n.get('tempo_entrega','?'))}</p>
            </div>""")
        parts.append(_section(f"🪜 Escalonamento de formatos — {e(escal.get('dor_focada','?'))}", f"<div class='escal-grid'>{''.join(cards)}</div>"))

    # ---- Escada estratégica ----
    escada = strategist_out.get("escada_estrategica") or {}
    if escada.get("mes_1"):
        steps = []
        for k, emoji in [("mes_1", "1️⃣"), ("mes_2", "2️⃣"), ("mes_3", "3️⃣")]:
            m = escada.get(k) or {}
            steps.append(f"""
            <div class='timeline-step'>
                <div class='timeline-num'>{emoji}</div>
                <div class='timeline-body'>
                    <h4>Mês {k[-1]} — {e(m.get('oferta','?'))}</h4>
                    <p><strong>Motivo:</strong> {e(m.get('motivo','?'))}</p>
                    <p class='timeline-meta'>🎯 Meta: <strong>{e(m.get('meta_faturamento','?'))}</strong></p>
                </div>
            </div>""")
        parts.append(_section("📅 Escada Estratégica — 90 dias", f"<div class='timeline'>{''.join(steps)}</div>"))

    # ---- Ofertas validadas ----
    ofertas = validator_out.get("ofertas", []) or []
    if ofertas:
        # tabela resumo
        rows = []
        for of in ofertas:
            score = of.get("score", 0)
            sem = of.get("semaforo") or _semaforo(score)
            color = "#10b981" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"
            rows.append(f"""
            <tr>
                <td>{of.get('id','?')}</td>
                <td><strong>{e(of.get('nome','?'))}</strong></td>
                <td>{_bar(score, 100, color)}</td>
                <td>{e(of.get('ticket_sugerido','?'))}</td>
                <td>{sem} {e(of.get('veredito',''))}</td>
            </tr>""")
        resumo = f"""<table class='data-table'>
            <thead><tr><th>#</th><th>Oferta</th><th>Score 0-100</th><th>Ticket</th><th>Veredito</th></tr></thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
        <p class='note'>Score combina: <strong>Volume 35%</strong> · <strong>Ticket 25%</strong> · <strong>Saturação 25%</strong> · <strong>Tendência 15%</strong></p>"""
        parts.append(_section("💰 Ofertas Validadas (resumo)", resumo))

        # detalhes
        detail_cards = []
        for of in ofertas:
            score = of.get("score", 0)
            sem = of.get("semaforo") or _semaforo(score)
            color = "#10b981" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"
            b = of.get("score_breakdown", {})
            detail_cards.append(f"""
            <div class='oferta-card' style='border-left:5px solid {color}'>
                <div class='oferta-header'>
                    <span class='oferta-sem'>{sem}</span>
                    <h3>{e(of.get('nome','?'))}</h3>
                    <span class='oferta-score' style='color:{color}'>{score}/100</span>
                </div>
                <div class='oferta-grid'>
                    <div><label>Dor atacada</label>{e(of.get('dor_atacada','?'))}</div>
                    <div><label>Vencedor ref.</label>{e(of.get('vencedor_referencia','?'))}</div>
                    <div><label>Formato</label>{e(of.get('formato','?'))}</div>
                    <div><label>Ticket</label><strong>{e(of.get('ticket_sugerido','?'))}</strong></div>
                </div>
                <p class='oferta-dif'><strong>Diferencial:</strong> {e(of.get('diferencial','?'))}</p>
                <p><strong>Promessa:</strong> {e(of.get('promessa_numerica','?'))}</p>
                <p><strong>Público:</strong> {e(of.get('publico_alvo','?'))}</p>
                <blockquote>{e(of.get('hook_de_venda','?'))}</blockquote>
                <p class='primeiro-passo'>🚀 <strong>Primeiro passo (24h):</strong> {e(of.get('primeiro_passo_amanha','?'))}</p>
                <div class='breakdown'>
                    <span>Vol {b.get('volume','?')}</span>
                    <span>Tkt {b.get('ticket','?')}</span>
                    <span>Sat {b.get('saturacao','?')}</span>
                    <span>Tnd {b.get('tendencia','?')}</span>
                </div>
            </div>""")
        parts.append(_section("📋 Detalhamento das ofertas", "<div class='oferta-list'>" + "".join(detail_cards) + "</div>"))

    # ---- Hunter Mercado Livre ----
    venc_ml = hunter_out.get("top_vencedores", [])[:10]
    if venc_ml:
        rows = "".join(
            f"<tr><td>{v.get('rank','?')}</td><td>{e((v.get('titulo') or '?')[:60])}</td>"
            f"<td>R${v.get('ticket','?')}</td><td>{v.get('vendidos','?')}</td>"
            f"<td>{e(v.get('formato','?'))}</td><td>{e(v.get('angulo','?'))}</td></tr>"
            for v in venc_ml
        )
        formula = hunter_out.get("fórmula_vencedora", {})
        nota = f"<p class='note'><strong>Fórmula vencedora ML:</strong> ticket médio R${formula.get('ticket_medio_top_10','?')} · formato: {e(formula.get('formato_dominante','?'))} · saturação: {e(formula.get('saturacao','?'))}.<br><strong>Oportunidade:</strong> {e(formula.get('oportunidade_de_ataque','?'))}</p>"
        parts.append(_section("🎯 Top vencedores — Mercado Livre BR", f"<table class='data-table'><thead><tr><th>#</th><th>Produto</th><th>Ticket</th><th>Vendidos</th><th>Formato</th><th>Ângulo</th></tr></thead><tbody>{rows}</tbody></table>{nota}"))

    # ---- Infoprodutos (Hotmart, Kiwify, Braip, Monetizze, Eduzz) ----
    venc_hot = info_hunter_out.get("top_vencedores_hotmart", [])[:10]
    if venc_hot:
        rows = "".join(
            f"<tr><td>{v.get('rank','?')}</td><td>{e((v.get('titulo') or '?')[:60])}</td>"
            f"<td>{e(v.get('plataforma','?'))}</td>"
            f"<td>R${v.get('ticket','?')}</td><td>{e(v.get('formato','?'))}</td>"
            f"<td>{e(v.get('angulo','?'))}</td></tr>"
            for v in venc_hot
        )
        fhot = info_hunter_out.get("formula_vencedora_hotmart", {})
        nota = f"<p class='note'><strong>Fórmula vencedora:</strong> ticket sweet spot <strong>{e(fhot.get('ticket_sweet_spot','?'))}</strong> · formato: {e(fhot.get('formato_dominante','?'))} · saturação: {e(fhot.get('saturacao','?'))}.</p>"
        parts.append(_section("🛒 Top infoprodutos — Hotmart, Kiwify, Braip, Monetizze, Eduzz", f"<table class='data-table'><thead><tr><th>#</th><th>Produto</th><th>Plataforma</th><th>Ticket</th><th>Formato</th><th>Ângulo</th></tr></thead><tbody>{rows}</tbody></table>{nota}"))

    # ---- Spy ----
    if spy_out.get("scraping_funcionou") and spy_out.get("top_anuncios"):
        rows = "".join(
            f"<tr><td>{a.get('rank','?')}</td><td>{e(a.get('pagina','?'))}</td>"
            f"<td>{e(a.get('angulo','?'))}</td><td><em>{e((a.get('hook') or '')[:80])}</em></td>"
            f"<td>{a.get('dias_rodando','?')}d</td></tr>"
            for a in spy_out.get("top_anuncios", [])[:10]
        )
        gap = spy_out.get("gap_de_mercado", {})
        gap_card = f"""<div class='gap-card'>
            <h4>🎯 Gap de mercado detectado</h4>
            <p><strong>Ângulo inexplorado:</strong> {e(gap.get('angulo_inexplorado','?'))}</p>
            <p><strong>Por que é oportunidade:</strong> {e(gap.get('porque_oportunidade','?'))}</p>
            <blockquote>{e(gap.get('hook_sugerido','?'))}</blockquote>
        </div>"""
        parts.append(_section("🕵️ Espionagem Meta Ads — Anúncios rodando agora", f"<table class='data-table'><thead><tr><th>#</th><th>Página</th><th>Ângulo</th><th>Hook</th><th>Rodando</th></tr></thead><tbody>{rows}</tbody></table>{gap_card}"))

    # ---- Fontes indisponíveis hoje: links para abrir à mão ----
    indisponiveis = [v for v in (scout_meta.get("fontes_status") or {}).values() if not v.get("ok")]
    if indisponiveis:
        blocos = []
        for v in indisponiveis:
            links = "".join(
                f"<li><a href='{e(l.get('url', ''))}' target='_blank' rel='noopener'>{e(l.get('query', ''))}</a></li>"
                for l in v.get("links", [])
            )
            blocos.append(f"<p><strong>{e(v.get('nome', '?'))}</strong></p><ul>{links}</ul>")
        parts.append(_section(
            "🔗 Fontes indisponíveis hoje — abra à mão",
            "<p class='note'>Estas fontes bloquearam a coleta automática ou não trouxeram resultado nesta rodada. "
            "O Radar não tenta contornar bloqueio: abra as buscas abaixo no navegador.</p>" + "".join(blocos),
        ))

    # ---- Vocabulário real ----
    vocab =analyst_out.get("vocabulario_real", [])[:25]
    if vocab:
        chips = "".join(f"<span class='chip'>{e(t)}</span>" for t in vocab)
        parts.append(_section("🗣️ Vocabulário real do público", f"<div class='chips'>{chips}</div><p class='note'>Use essas palavras EXATAS em hooks, headlines e anúncios — é o que o público fala.</p>"))

    # ---- BÔNUS: Landing page pronta pra Lovable (9 seções + copy filled) ----
    landing_md = (landing_out or {}).get("markdown", "")
    persona_usada = (landing_out or {}).get("persona_usada") or {}
    oferta_usada = (landing_out or {}).get("oferta_usada") or {}
    parts.append("<hr class='next-step-divider'>")
    if landing_md and "(nenhuma" not in landing_md[:50]:
        instrucao_lovable = (
            "Construa essa landing page em HTML + Tailwind, mobile-first. "
            "Use paleta: fundo dark (#1a1614), primária terracota (#cc785c), cream (#f5efe6) pra texto. "
            "Tipografia: Cormorant Garamond nos H1/H2/H3, Inter no corpo. "
            "MANTENHA O TEXTO EXATO de cada seção abaixo — não reescreva, só estruture visualmente. "
            "Cada seção vira um <section>. Botões CTA em terracota com hover. Sem imagens externas — use gradientes e cards.\n\n"
            "===== COPY DA LANDING (use textualmente) =====\n\n"
        )
        lovable_full = instrucao_lovable + landing_md
        # Escape pra JS template literal
        lovable_js = (
            lovable_full
            .replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("$", "\\$")
        )
        # Mantém quebras de linha como \n reais dentro do template literal
        persona_label = e(persona_usada.get("nome", "persona escolhida"))
        oferta_label = e(oferta_usada.get("nome", "oferta principal"))
        parts.append(f"""
    <section class='cta-section next-step'>
        <div class='cta-card next-card'>
            <div class='cta-badge next-badge'>🎯 PRÓXIMO PASSO</div>
            <div class='cta-icon'>🪶</div>
            <h3>Hora de criar sua página de vendas</h3>
            <p class='intro-step'>Você já viu as personas, escolheu uma, e tem a oferta certa. Agora é só publicar a página de vendas pra começar a testar.</p>
            <p>O Radar de Demanda já escreveu sua landing inteira em <strong>9 seções validadas</strong> (headline · agitação da dor · diagnóstico · mecanismo · prova · fit · anti-fit · CTA · P.S.) com a copy específica pra <em>{persona_label}</em> vendendo <em>{oferta_label}</em> — usando o vocabulário real do público.</p>
            <div class='how-it-works'>
                <div class='step'><span class='step-num'>1</span> Clique no botão abaixo (copia o prompt completo pro clipboard)</div>
                <div class='step'><span class='step-num'>2</span> Abra <a href='https://lovable.dev' target='_blank'>lovable.dev</a> em outra aba e cole no campo</div>
                <div class='step'><span class='step-num'>3</span> Lovable monta o visual em ~2min — sua copy estratégica é preservada</div>
                <div class='step'><span class='step-num'>4</span> Publique e direcione tráfego — comece a validar</div>
            </div>
            <button id='copy-lovable' class='cta-btn cta-btn-big' onclick="
                const txt = `{lovable_js}`;
                navigator.clipboard.writeText(txt).then(()=>{{
                    this.innerText='✅ Prompt copiado — cole no Lovable.dev';
                    this.classList.add('copied');
                    setTimeout(()=>{{this.innerText='🚀 Copiar prompt Lovable e criar minha landing';this.classList.remove('copied');}}, 3000);
                }});
            ">🚀 Copiar prompt Lovable e criar minha landing</button>
            <p class='cmd-preview'>Também salvamos a landing no arquivo <code>_landing.md</code> (ao lado deste dashboard) — caso prefira colar em Webflow, WordPress, Notion ou qualquer outro construtor.</p>
        </div>
    </section>""")
    else:
        parts.append("""
    <section class='cta-section next-step'>
        <div class='cta-card next-card'>
            <div class='cta-badge next-badge'>🎯 PRÓXIMO PASSO</div>
            <div class='cta-icon'>🪶</div>
            <h3>Hora de criar sua página de vendas</h3>
            <p class='intro-step'>Você já viu as personas, escolheu uma, e tem a oferta certa. Falta gerar a página de vendas pra começar a testar.</p>
            <div class='how-it-works'>
                <div class='step'><span class='step-num'>1</span> Clique no botão (copia o comando)</div>
                <div class='step'><span class='step-num'>2</span> Cole no terminal do projeto e dê Enter — o Radar de Demanda escreve as 9 seções (~1min, 1 chamada ao Sonnet)</div>
                <div class='step'><span class='step-num'>3</span> Abra o arquivo <code>_landing.md</code> gerado e copie tudo</div>
                <div class='step'><span class='step-num'>4</span> Cole em <a href='https://lovable.dev' target='_blank'>lovable.dev</a> — ele monta o visual mantendo a copy</div>
            </div>
            <button class='cta-btn cta-btn-big' onclick="
                navigator.clipboard.writeText('python scripts/gerar_landing.py').then(()=>{
                    this.innerText='✅ Comando copiado — cole no terminal';
                    this.classList.add('copied');
                    setTimeout(()=>{this.innerText='🚀 Copiar comando — Gerar minha landing das 9 seções';this.classList.remove('copied');}, 3000);
                });
            ">🚀 Copiar comando — Gerar minha landing das 9 seções</button>
            <p class='cmd-preview'><code>python scripts/gerar_landing.py</code></p>
        </div>
    </section>""")

    # ---- Footer ----
    parts.append("""
    <footer class='footer'>
        <p>📅 <strong>Rode de novo em 14-21 dias.</strong> Mercado BR muda toda semana — quem roda mensal pega oportunidade antes da concorrência saturar.</p>
        <p>💰 <em>O custo de cada dossiê depende do modelo e da coleta: 2 chamadas ao Claude Sonnet e de 1 a 4 ao Haiku (mais 1 ao Sonnet com --landing). Confira o gasto real no painel da Anthropic. Sem mensalidade.</em></p>
        <p>🎯 Próximo passo: <code>/radar-copy &lt;prompt-id&gt;</code> ou <code>/radar-ads &lt;prompt-id&gt;</code></p>
    </footer>
    </main>""")

    parts.append("</body></html>")
    return "".join(parts)


def _section(title: str, body: str) -> str:
    return f"<section><h2>{escape(title)}</h2>{body}</section>"


def _metodologia_html(scout_meta: dict, fontes_ativas: list[str], fat_atual: str, fat_meta: str) -> str:
    e = escape
    items = [
        ("🐝", "Scout", f"raspou <strong>{scout_meta.get('total_signals','?')} sinais</strong> de {len(fontes_ativas)} fontes BR ({', '.join(fontes_ativas)})"),
        ("🧠", "Analyst", "ranqueou as <strong>10 dores mais quentes</strong> (Pain Score = freq 40% + emocional 30% + urgência 20% + dinheiro 10%) e agrupou em <strong>personas distintas</strong>"),
        ("🎯", "Hunter", "caçou top vencedores no <strong>Mercado Livre BR</strong>"),
        ("🛒", "InfoHunter", "caçou top infoprodutos em <strong>Hotmart, Kiwify, Braip, Monetizze e Eduzz</strong>"),
        ("🕵️", "Spy", "espionou anúncios rodando <strong>agora</strong> na Meta Ads Library (+60d = oferta lucrativa validada)"),
        ("♟️", "Strategist", f"cruzou tudo com sua meta financeira (<strong>{e(fat_atual)} → {e(fat_meta)}</strong>) pra gerar ofertas calibradas"),
        ("⚖️", "Validator", "atribuiu Market Viability Score 0-100 (🟢 Go / 🟡 cautela / 🔴 não)"),
    ]
    cards = "".join(
        f"<div class='method-card'><div class='method-emoji'>{em}</div><div><strong>{nome}</strong> {desc}</div></div>"
        for em, nome, desc in items
    )
    return f"<div class='method-grid'>{cards}</div>"


_CSS = """
:root{
  --terracota:#cc785c; --terracota-dark:#a85b42; --terracota-light:#e89976;
  --cream:#f5efe6; --paper:#faf7f2; --ink:#2a2422; --ink-soft:#5a4f4a;
  --bg:#1a1614; --surface:#241f1c; --surface2:#2d2724; --border:#3a322e;
  --text:#f5efe6; --muted:#a89890; --accent:var(--terracota); --accent2:#d4a373;
  --danger:#c84a3e; --warning:#e89e3f; --success:#7a9c5e
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',-apple-system,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);line-height:1.65;padding:0}
h1,h2,h3,h4,.serif{font-family:'Cormorant Garamond','Times New Roman',serif;font-weight:600;letter-spacing:-0.5px}
.hero{background:linear-gradient(135deg,#241f1c 0%,#2d2724 50%,#3a2820 100%);padding:64px 32px 48px;border-bottom:3px solid var(--terracota)}
.brand{font-family:'Inter',sans-serif;font-size:13px;letter-spacing:4px;color:var(--terracota);font-weight:700;margin-bottom:20px;text-transform:uppercase}
h1{font-size:56px;font-weight:600;letter-spacing:-1.5px;margin-bottom:12px;line-height:1.1}
.subtitle{font-size:18px;color:var(--muted);margin-bottom:24px}
.meta-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:24px}
.meta-card{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px 16px}
.meta-card label{display:block;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}
.meta-card span{font-size:16px;font-weight:600}
.salto-card{display:flex;align-items:center;gap:16px;flex-wrap:wrap;background:linear-gradient(90deg,var(--surface2),#3a2820);border:1px solid var(--terracota);border-radius:12px;padding:20px 28px}
.salto-label{font-weight:600;font-size:14px;letter-spacing:1px;text-transform:uppercase;color:var(--terracota)}
.salto-from{color:var(--muted);font-size:20px;font-family:'Cormorant Garamond',serif}
.salto-arrow{color:var(--terracota);font-size:28px;font-weight:700}
.salto-to{color:var(--terracota-light);font-size:26px;font-weight:600;font-family:'Cormorant Garamond',serif}
.salto-tag{margin-left:auto;background:var(--terracota);color:var(--cream);padding:6px 16px;border-radius:99px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1.5px}
main{max-width:1280px;margin:0 auto;padding:32px}
section{margin-bottom:48px}
h2{font-size:34px;font-weight:600;margin-bottom:24px;padding-bottom:12px;border-bottom:1px solid var(--terracota);color:var(--cream)}
h3{font-size:22px;font-weight:600;margin:8px 0;color:var(--cream)}
h4{font-size:19px;font-weight:600;margin:8px 0}
.method-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.method-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;display:flex;gap:12px;align-items:flex-start}
.method-emoji{font-size:24px;flex-shrink:0}
.method-card div:last-child{font-size:14px;color:var(--text)}
.banner-persona{background:linear-gradient(90deg,#3a282044,transparent);border-left:4px solid var(--terracota);padding:18px 24px;border-radius:0 8px 8px 0;margin:32px 0;font-size:16px;font-family:'Cormorant Garamond',serif;font-size:18px}
.persona-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.persona-card{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--muted);border-radius:10px;padding:20px;position:relative}
.persona-card.picked-card{box-shadow:0 0 0 2px var(--terracota);background:linear-gradient(180deg,#3a282022,transparent)}
.persona-header{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.persona-id{background:var(--surface2);padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600;color:var(--muted)}
.persona-intensity{font-size:13px}
.picked{margin-left:auto;background:var(--terracota);color:var(--cream);padding:3px 10px;border-radius:4px;font-size:11px;font-weight:700;letter-spacing:0.5px}
.persona-desc{color:var(--muted);font-size:14px;margin:8px 0}
.persona-stats{display:flex;gap:16px;font-size:13px;margin:12px 0;flex-wrap:wrap}
.persona-opp{font-size:13px;background:var(--surface2);padding:10px;border-radius:6px;margin-top:8px}
.data-table{width:100%;border-collapse:collapse;background:var(--surface);border-radius:10px;overflow:hidden;border:1px solid var(--border)}
.data-table th{background:var(--surface2);text-align:left;padding:12px;font-size:12px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);border-bottom:1px solid var(--border)}
.data-table td{padding:12px;border-bottom:1px solid var(--border);font-size:14px;vertical-align:top}
.data-table tr:last-child td{border-bottom:none}
.bar{background:var(--surface2);height:24px;border-radius:4px;overflow:hidden;position:relative;min-width:120px}
.bar-fill{height:100%;display:flex;align-items:center;padding:0 8px;color:#fff;font-size:12px;font-weight:600;transition:width 0.3s}
.bar-label{font-weight:700}
.muted{color:var(--muted);font-size:13px}
.note{margin-top:16px;font-size:14px;color:var(--muted);background:var(--surface);padding:12px 16px;border-radius:6px;border-left:3px solid var(--terracota)}
.math-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
.math-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px}
.math-card.destaque{border-color:var(--terracota);box-shadow:0 0 0 1px var(--terracota);background:linear-gradient(180deg,#3a282011,var(--surface))}
.math-opt{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.math-headline{font-size:22px;font-weight:600;margin-bottom:12px;font-family:'Cormorant Garamond',serif;color:var(--cream)}
.math-numbers{display:flex;gap:16px;margin:12px 0;font-size:13px;flex-wrap:wrap}
.math-via{margin:8px 0;font-size:13px}
.escal-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.escal-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px}
.escal-niv{font-size:11px;font-weight:700;letter-spacing:2px;margin-bottom:8px}
.escal-ticket{font-size:28px;font-weight:600;color:var(--terracota);margin:8px 0;font-family:'Cormorant Garamond',serif}
.timeline{display:flex;flex-direction:column;gap:16px;position:relative}
.timeline-step{display:flex;gap:16px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px}
.timeline-num{font-size:32px;flex-shrink:0}
.timeline-meta{margin-top:8px;font-size:14px;color:var(--terracota)}
.oferta-list{display:flex;flex-direction:column;gap:16px}
.oferta-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:24px}
.oferta-header{display:flex;align-items:center;gap:12px;margin-bottom:16px;flex-wrap:wrap}
.oferta-sem{font-size:24px}
.oferta-header h3{flex:1;font-size:20px}
.oferta-score{font-size:36px;font-weight:600;font-family:'Cormorant Garamond',serif}
.oferta-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:12px 0;font-size:14px}
.oferta-grid label{display:block;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:2px}
.oferta-dif{background:var(--surface2);padding:12px;border-radius:6px;margin:12px 0;font-size:14px}
blockquote{border-left:3px solid var(--terracota);padding:14px 20px;background:var(--surface2);font-family:'Cormorant Garamond',serif;font-style:italic;font-size:18px;margin:12px 0;border-radius:0 6px 6px 0;color:var(--cream)}
.primeiro-passo{background:#3a28201a;border:1px solid var(--terracota);padding:14px 16px;border-radius:6px;margin:12px 0;font-size:14px}
.breakdown{display:flex;gap:12px;margin-top:12px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
.breakdown span{background:var(--surface2);padding:4px 10px;border-radius:4px}
.gap-card{background:var(--surface2);border:1px solid var(--accent2);border-radius:10px;padding:20px;margin-top:16px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{background:var(--surface2);border:1px solid var(--border);padding:6px 12px;border-radius:99px;font-size:13px;font-family:'Monaco','Consolas',monospace}
.cta-section{margin:48px 0}
.bonus-section .bonus-card{position:relative;border-color:var(--accent2);background:linear-gradient(135deg,var(--surface),#3a2820,#4a3528)}
.cta-badge{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--accent2);color:var(--ink);padding:4px 16px;border-radius:99px;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;font-family:'Inter',sans-serif}
.cmd-preview a{color:var(--terracota-light);text-decoration:underline}
.steps{text-align:left;max-width:640px;margin:16px auto;padding-left:20px}
.steps li{margin:10px 0;font-size:14px;color:var(--text)}
.steps li strong{color:var(--terracota-light)}
.steps a{color:var(--terracota-light);text-decoration:underline}
.next-step-divider{border:none;height:1px;background:linear-gradient(90deg,transparent,var(--terracota),transparent);margin:64px 0 32px;opacity:0.5}
.next-step .next-card{background:linear-gradient(135deg,#2d2724 0%,#3a2820 50%,#4a3528 100%);border:2px solid var(--terracota);padding:40px 32px}
.next-step .next-card h3{font-size:32px;color:var(--cream);margin:12px 0 8px}
.next-badge{background:var(--terracota)!important;color:var(--cream)!important;font-size:12px!important;letter-spacing:2px!important;padding:6px 18px!important}
.intro-step{font-family:'Cormorant Garamond',serif;font-size:19px;font-style:italic;color:var(--terracota-light);max-width:640px;margin:0 auto 16px}
.how-it-works{max-width:600px;margin:24px auto;text-align:left;background:rgba(0,0,0,0.2);border-radius:10px;padding:20px 24px}
.how-it-works .step{display:flex;align-items:center;gap:14px;padding:10px 0;font-size:15px;color:var(--text);border-bottom:1px solid rgba(204,120,92,0.15)}
.how-it-works .step:last-child{border-bottom:none}
.how-it-works .step-num{flex-shrink:0;width:28px;height:28px;background:var(--terracota);color:var(--cream);border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-family:'Inter',sans-serif;font-size:14px}
.how-it-works a{color:var(--terracota-light);text-decoration:underline}
.cta-btn-big{font-size:18px;padding:20px 40px;margin-top:24px}
.cta-card{background:linear-gradient(135deg,var(--surface),#3a2820);border:2px solid var(--terracota);border-radius:14px;padding:32px;text-align:center}
.cta-icon{font-size:48px;margin-bottom:8px}
.cta-card h3{font-size:28px;color:var(--cream);margin-bottom:12px}
.cta-card p{max-width:640px;margin:8px auto;font-size:15px;color:var(--text)}
.cta-btn{display:inline-block;margin:20px auto 12px;padding:16px 32px;background:var(--terracota);color:var(--cream);border:none;border-radius:99px;font-size:16px;font-weight:600;letter-spacing:0.5px;cursor:pointer;font-family:'Inter',sans-serif;transition:all 0.2s;box-shadow:0 4px 12px rgba(204,120,92,0.3)}
.cta-btn:hover{background:var(--terracota-dark);transform:translateY(-2px);box-shadow:0 6px 16px rgba(204,120,92,0.4)}
.cta-btn.copied{background:var(--success);box-shadow:0 4px 12px rgba(122,156,94,0.3)}
.cmd-preview{margin-top:12px;font-size:13px;color:var(--muted)}
.cmd-preview code{background:var(--surface2);padding:6px 12px;border-radius:6px;font-family:'Monaco','Consolas',monospace;color:var(--terracota-light)}
.footer{margin-top:48px;padding:32px;background:var(--surface);border-top:1px solid var(--border);border-radius:10px;font-size:14px}
.footer p{margin:8px 0}
code{background:var(--surface2);padding:2px 8px;border-radius:4px;font-size:13px}
@media print{body{background:#fff;color:#000}.hero{background:#fff;color:#000}h1,h2,h3{color:#000}.persona-card,.math-card,.escal-card,.oferta-card,.data-table{background:#fff;border:1px solid #ddd;break-inside:avoid}}
"""
