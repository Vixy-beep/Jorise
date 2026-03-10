"""
Jorise Knowledge Base — API Views

GET  /api/knowledge/stats/           → estado del índice
POST /api/knowledge/search/          → buscar en los PDFs
POST /api/knowledge/build/           → (admin) reconstruir índice
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .indexer import search, get_index_stats, build_index

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def knowledge_stats(request):
    """Retorna estadísticas del índice actual."""
    stats = get_index_stats()
    return JsonResponse(stats)


@csrf_exempt
@require_http_methods(["POST"])
def knowledge_search(request):
    """
    Busca en la base de conocimiento de PDFs de seguridad.

    Body JSON:
        query   (str)  — texto a buscar, e.g. "buffer overflow bypass techniques"
        top_k   (int)  — resultados a retornar (default 5, max 10)

    Response:
        {
            "query": "...",
            "results": [
                {"source": "AV_EDR_Bypass.pdf", "text": "...", "score": 9.12},
                ...
            ]
        }
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "JSON inválido"}, status=400)

    query = str(body.get("query", "")).strip()
    if not query:
        return JsonResponse({"error": "Campo 'query' requerido"}, status=400)

    if len(query) > 500:
        return JsonResponse({"error": "query demasiado larga (máx 500 chars)"}, status=400)

    top_k = min(int(body.get("top_k", 5)), 10)

    try:
        results = search(query, top_k=top_k)
    except RuntimeError as e:
        return JsonResponse({"error": str(e), "hint": "POST /api/knowledge/build/ para construir el índice"}, status=503)
    except Exception as e:
        logger.exception("Error en knowledge_search")
        return JsonResponse({"error": "Error interno"}, status=500)

    return JsonResponse({"query": query, "results": results})


@csrf_exempt
@require_http_methods(["POST"])
def knowledge_build(request):
    """
    Construye (o reconstruye) el índice BM25 desde los PDFs.
    Solo accesible por staff/admin.

    Body JSON (opcional):
        force (bool) — reconstruir aunque ya exista (default false)
    """
    if not request.user.is_staff:
        return JsonResponse({"error": "Acceso denegado"}, status=403)

    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    force = bool(body.get("force", False))

    try:
        result = build_index(force=force)
    except Exception as e:
        logger.exception("Error construyendo índice")
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse(result)
