"""
Jorise Knowledge Base — PDF Indexer
Extrae texto de los PDFs de seguridad y construye un índice BM25
para consultas tipo RAG sin necesidad de embeddings ni GPU.

Uso:
    python -m knowledge.indexer build          # indexar todos los PDFs
    python -m knowledge.indexer search "buffer overflow bypass"
"""
import os
import re
import json
import pickle
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR   = _BASE_DIR / "media" / "knowledge" / "pdfs"
INDEX_DIR = _BASE_DIR / "media" / "knowledge" / "index"
INDEX_FILE  = INDEX_DIR / "bm25_index.pkl"   # guarda {bm25, chunks} juntos
CHUNKS_FILE = INDEX_DIR / "chunks.json"      # legacy, no usado

CHUNK_SIZE  = 400   # palabras por chunk
CHUNK_OVERLAP = 50  # palabras de solapamiento


def _extract_text_pypdf(pdf_path: Path) -> str:
    """Extrae texto de un PDF con PyPDF2."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(pdf_path))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
        return "\n".join(pages)
    except Exception as e:
        logger.warning(f"Error leyendo {pdf_path.name}: {e}")
        return ""


def _clean_text(text: str) -> str:
    """Limpia texto extraído de PDF."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x20-\x7E\xC0-\xFF\n]', ' ', text)
    return text.strip()


def _chunk_text(text: str, source: str) -> list[dict]:
    """Divide texto en chunks con solapamiento."""
    words = text.split()
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for i in range(0, len(words), step):
        chunk_words = words[i:i + CHUNK_SIZE]
        if len(chunk_words) < 20:  # ignorar chunks muy pequeños
            continue
        chunks.append({
            "source": source,
            "chunk_id": len(chunks),
            "text": " ".join(chunk_words),
            "start_word": i,
        })
    return chunks


def build_index(pdf_dir: Path = PDF_DIR, force: bool = False) -> dict:
    """
    Construye el índice BM25 desde cero sobre todos los PDFs en pdf_dir.
    Retorna estadísticas del proceso.
    """
    from rank_bm25 import BM25Okapi

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    if INDEX_FILE.exists() and not force:
        print("Índice ya existe. Usa force=True para reconstruir.")
        with open(CHUNKS_FILE, encoding="utf-8") as f:
            chunks = json.load(f)
        return {"status": "already_built", "chunks": len(chunks)}

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    print(f"Procesando {len(pdf_files)} PDFs...")

    all_chunks = []
    stats = {"ok": 0, "empty": 0, "error": 0}

    for pdf_path in pdf_files:
        raw = _extract_text_pypdf(pdf_path)
        text = _clean_text(raw)
        if not text or len(text) < 100:
            stats["empty"] += 1
            continue
        chunks = _chunk_text(text, pdf_path.name)
        all_chunks.extend(chunks)
        stats["ok"] += 1
        if stats["ok"] % 20 == 0:
            print(f"  {stats['ok']}/{len(pdf_files)} procesados, {len(all_chunks)} chunks...")

    print(f"\nResultado: {stats['ok']} PDFs OK, {stats['empty']} vacíos, {stats['error']} errores")
    print(f"Total chunks: {len(all_chunks)}")

    # Tokenizar y construir BM25
    print("Construyendo índice BM25...")
    tokenized = [c["text"].lower().split() for c in all_chunks]
    bm25 = BM25Okapi(tokenized)

    # Guardar índice + chunks en un solo pickle (evita race condition con JSON)
    payload = {"bm25": bm25, "chunks": all_chunks}
    with open(INDEX_FILE, "wb") as f:
        pickle.dump(payload, f, protocol=4)

    print(f"Índice guardado en {INDEX_DIR}")
    return {"status": "built", "pdfs": stats["ok"], "chunks": len(all_chunks)}


def search(query: str, top_k: int = 5) -> list[dict]:
    """
    Busca los chunks más relevantes para una query.
    Retorna lista de {source, text, score}.
    """
    from rank_bm25 import BM25Okapi

    if not INDEX_FILE.exists():
        raise RuntimeError("Índice no construido. Ejecuta: python -m knowledge.indexer build")

    with open(INDEX_FILE, "rb") as f:
        payload = pickle.load(f)

    bm25: BM25Okapi = payload["bm25"]
    chunks: list[dict] = payload["chunks"]

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] < 0.01:
            break
        results.append({
            "source": chunks[idx]["source"],
            "text": chunks[idx]["text"][:600],
            "score": round(float(scores[idx]), 4),
        })
    return results


def get_index_stats() -> dict:
    """Retorna estadísticas del índice actual."""
    if not INDEX_FILE.exists():
        return {"status": "not_built"}
    with open(INDEX_FILE, "rb") as f:
        payload = pickle.load(f)
    chunks = payload.get("chunks", [])
    sources = list({c["source"] for c in chunks})
    return {
        "status": "ready",
        "chunks": len(chunks),
        "sources": len(sources),
        "index_size_mb": round(INDEX_FILE.stat().st_size / 1024 / 1024, 2),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2 or sys.argv[1] == "build":
        force = "--force" in sys.argv
        result = build_index(force=force)
        print(json.dumps(result, indent=2))
    elif sys.argv[1] == "search":
        query = " ".join(sys.argv[2:])
        if not query:
            print("Uso: python -m knowledge.indexer search <query>")
            sys.exit(1)
        results = search(query, top_k=5)
        for r in results:
            print(f"\n[{r['score']}] {r['source']}")
            print(r['text'][:300])
    elif sys.argv[1] == "stats":
        print(json.dumps(get_index_stats(), indent=2))
