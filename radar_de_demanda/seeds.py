"""Keywords semente por nicho.

Pra ampliar: adicionar especialidades novas. Cada seed gera ~10-30 perguntas
no PAA + ~10 autocompletes + ~5 related = ~25-45 sinais por seed.
"""

SEEDS = {
    # ⚠️ DOR DO PRÓPRIO ADVOGADO (sobre marketing/vendas/gestão)
    # Usar pra hook de prospecção B2B (subject, MSG1, audit)
    "advocacia_dor_negocio": [
        # Marketing
        "marketing para advogado",
        "como advogado pode fazer marketing",
        "marketing jurídico OAB",
        "site para advogado",
        "instagram para advogado",
        "anúncio no google para advogado",
        # Captação
        "como captar clientes advogado",
        "captação de clientes na advocacia",
        "advogado novo como conseguir cliente",
        "advocacia sem clientes",
        # Vendas / honorários
        "como cobrar honorários advogado",
        "como precificar advocacia",
        "advogado cliente não paga",
        # Gestão escritório
        "como abrir escritório de advocacia",
        "software para escritório de advocacia",
        "produtividade advogado",
        # OAB compliance
        "Provimento OAB 205",
        "advogado pode fazer publicidade",
        "publicidade advocacia o que pode",
        # Concorrência / dor de mercado
        "concorrência na advocacia",
        "escritório de advocacia faliu",
        "advogado autônomo dificuldade",
    ],

    # ⚠️ DOR DO CLIENTE DO ADVOGADO (sobre temas jurídicos)
    # Usar pra pauta de blog SEO do escritório (produto BLOG)
    "advocacia": [
        # Direito do trabalho
        "advogado trabalhista",
        "demissão por justa causa",
        "rescisão indireta",
        "horas extras não pagas",
        "assédio moral no trabalho",
        # Previdenciário
        "advogado INSS",
        "revisão aposentadoria",
        "auxílio doença negado",
        "BPC LOAS",
        # Civil / família
        "advogado divórcio",
        "pensão alimentícia",
        "guarda compartilhada",
        "inventário extrajudicial",
        # Consumidor
        "advogado plano de saúde",
        "cancelamento de plano de saúde",
        "negativação indevida",
        "atraso de voo indenização",
        # Criminal
        "advogado criminalista",
        "habeas corpus",
        # Tributário (pequeno)
        "advogado tributário",
    ],
    "contabilidade": [
        # MEI / abertura
        "abrir MEI",
        "como abrir empresa",
        "Simples Nacional ou Lucro Presumido",
        # Operacional
        "declaração de imposto de renda",
        "como pagar menos imposto legalmente",
        "DAS atrasado",
        "contador para empresa",
        # Específico
        "abertura de CNPJ médico",
        "MEI ou ME",
        "fechar empresa CNPJ",
    ],
    "nutricionista": [
        # Regulação CFN 856/2026
        "nutricionista clínico",
        "consulta nutricional online",
        "emagrecer com nutricionista",
        # Específico
        "nutricionista esportivo",
        "nutricionista materno infantil",
        "reeducação alimentar",
        "dieta cetogênica",
        "dieta para diabéticos",
    ],
    # ⚠️ DOR DO DONO DE AGÊNCIA DE MARKETING (sobre escalar produção com IA/multiagentes)
    # Usar pra prospecção da Consultoria Agentes para Marketing
    "agencia_marketing_multiagentes_dor_negocio": [
        # Produção de conteúdo / equipe
        "contratar redator agência",
        "redator de IA qualidade ruim",
        "conteúdo com cara de IA",
        "como escalar produção de conteúdo agência",
        "agência de marketing não dá conta dos clientes",
        "processo de aprovação de conteúdo cliente",
        "briefing perdido agência de marketing",
        # IA / automação aplicada ao dia a dia
        "agente de IA para marketing",
        "multiagentes de IA para conteúdo",
        "automação para agência de marketing",
        "ferramenta de IA para social media",
        "como treinar IA no tom de voz do cliente",
        "chatgpt genérico demais para cliente",
        "sistema operacional para agência de marketing",
        # Gestão / operação da agência
        "agência de marketing pequena dificuldade",
        "escalar agência sem contratar mais gente",
        "agência perde cliente por atraso de entrega",
        "quanto cobrar por gestão de redes sociais",
        "como estruturar processo de agência de marketing",
        # Dor emocional / urgência
        "sobrecarga dona de agência de marketing",
        "dependo demais de mim na agência",
        "medo de perder cliente por qualidade",
    ],

    # ⚠️ DOR DE EMPRESA COM TIME DE MARKETING INTERNO (quer mais performance do time que já tem)
    # Usar pra prospecção da Consultoria Agentes para Marketing — segmento 2 (não é agência)
    "empresa_time_marketing_performance_dor_negocio": [
        # Performance / resultado do time
        "time de marketing não bate meta",
        "como aumentar performance do time de marketing",
        "produtividade do time de marketing",
        "time de marketing sobrecarregado",
        "gestor de marketing sobrecarregado",
        "marketing não gera resultado",
        "como medir performance de marketing",
        # IA / automação aplicada ao marketing interno
        "IA para equipe de marketing",
        "automatizar marketing da empresa",
        "ferramentas de IA para time de marketing",
        "agente de IA para marketing interno",
        "como usar IA no departamento de marketing",
        "IA para relatório de marketing",
        # Gestão / operação do departamento
        "departamento de marketing pequeno",
        "falta de gente no time de marketing",
        "contratar analista de marketing",
        "terceirizar marketing ou contratar time",
        "CMO reclama de falta de resultado",
        # Dor emocional / urgência
        "cobrança de resultado de marketing",
        "marketing não escala junto com a empresa",
        "diretoria pressiona time de marketing",
    ],

    # ⚠️ DOR DO EMPRESÁRIO/RH (sobre treinamento de colaboradores)
    # Usar pra prospecção LinkedIn — vender treinamento in-company/online
    "treinamento_corporativo": [
        # Genérico — busca de soluções
        "treinamento para colaboradores",
        "treinamento in company",
        "curso para empresa",
        "capacitação de funcionários",
        "treinamento corporativo",
        "workshop para empresa",
        "consultoria de treinamento empresarial",
        # Tipos de treinamento mais buscados
        "treinamento de vendas equipe",
        "treinamento de liderança gerentes",
        "treinamento de atendimento ao cliente",
        "treinamento soft skills equipe",
        "treinamento de IA para empresa",
        "treinamento de ChatGPT para funcionários",
        "treinamento marketing digital equipe",
        # Dor / motivação real
        "como engajar equipe em treinamento",
        "ROI de treinamento corporativo",
        "como treinar funcionários novos",
        "minha equipe não bate meta o que fazer",
        "funcionário desmotivado o que fazer",
        "treinamento online ou presencial qual melhor",
        "como medir eficácia de treinamento",
        # Gestão / RH
        "PDI plano de desenvolvimento individual",
        "T&D treinamento e desenvolvimento",
        "universidade corporativa pequena empresa",
        "LNT levantamento de necessidade de treinamento",
    ],
}
