"""YouTube Comments — captura comentários de vídeos relevantes pro nicho.

Usa yt-dlp (sem API key, sem custo) pra:
1. Buscar vídeos relevantes por query (ytsearch) — opcional
2. Extrair comentários de cada vídeo (busca ou lista explícita de URLs)

Comentários são uma fonte rica de reação/dúvida/dor real do público,
principalmente em vídeos educacionais e tutoriais do nicho.
"""
from __future__ import annotations
import time
from typing import Iterable

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


def _ydl_opts(**overrides) -> dict:
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    opts.update(overrides)
    return opts


def search_videos(query: str, limit: int = 5) -> list[dict]:
    """Busca vídeos no YouTube pra uma query. Retorna [{video_id, url, title}, ...]."""
    if yt_dlp is None:
        return []
    opts = _ydl_opts(extract_flat=True)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
    except Exception:
        return []

    out = []
    for entry in (info or {}).get("entries", []) or []:
        if not entry:
            continue
        vid = entry.get("id")
        out.append({
            "video_id": vid,
            "url": entry.get("url") or f"https://www.youtube.com/watch?v={vid}",
            "title": entry.get("title", ""),
        })
    return out


def fetch_comments(video_url: str, max_comments: int = 100) -> list[dict]:
    """Extrai comentários de 1 vídeo. Retorna sinais no formato padrão do Radar de Demanda.

    Cada sinal: {"texto": str, "fonte": str, "url": str, "metadata": dict}
    """
    if yt_dlp is None:
        return []
    opts = _ydl_opts(getcomments=True)
    opts["extractor_args"] = {"youtube": {"max_comments": [str(max_comments)]}}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
    except Exception:
        return []

    titulo = (info or {}).get("title", "") or ""
    comments = (info or {}).get("comments") or []
    out = []
    for c in comments[:max_comments]:
        texto = (c.get("text") or "").strip()
        if not texto:
            continue
        out.append({
            "texto": texto[:1500],
            "fonte": f"youtube-comment:{titulo[:60]}",
            "url": video_url,
            "metadata": {
                "author": c.get("author", ""),
                "like_count": c.get("like_count", 0),
                "video_title": titulo,
            },
        })
    return out


def scrape_youtube_comments(
    queries: Iterable[str] = (),
    *,
    videos: list[str] | None = None,
    max_videos_per_query: int = 3,
    max_comments_per_video: int = 50,
    delay: float = 0.5,
) -> list[dict]:
    """Roda busca (opcional) + coleta de comentários.

    Aceita queries (busca vídeos no YouTube) e/ou uma lista explícita de
    URLs de vídeo já conhecidos (ex: vídeos de referência do nicho).
    """
    out: list[dict] = []
    visto_videos: set[str] = set()
    video_urls: list[str] = list(videos or [])

    for q in queries:
        print(f"  🔍 youtube search: {q}")
        for v in search_videos(q, limit=max_videos_per_query):
            video_urls.append(v["url"])

    for url in video_urls:
        if url in visto_videos:
            continue
        visto_videos.add(url)
        print(f"  💬 coletando comentários: {url}")
        out.extend(fetch_comments(url, max_comments=max_comments_per_video))
        time.sleep(delay)

    return out
