"""Agent swarm do Radar de Demanda — 8 agentes especializados em sequência.

Router → Scout → Analyst → Hunter → InfoHunter → Spy → Strategist → Validator
"""
from .router import router
from .scout import scout
from .analyst import analyst
from .hunter import hunter
from .info_hunter import info_hunter
from .spy import spy
from .strategist import strategist
from .validator import validator

__all__ = ["router", "scout", "analyst", "hunter", "info_hunter", "spy", "strategist", "validator"]
