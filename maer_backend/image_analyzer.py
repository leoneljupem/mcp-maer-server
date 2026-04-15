#!/usr/bin/env python3
# 🦁 MAER IMAGE ANALYZER — Análisis y clustering de imágenes
# Leonel Mojica — Ecatepec MX — 2026

"""
Análisis avanzado de imágenes:
  - Hash perceptual (pHash, aHash, dHash) para duplicados
  - Clustering con DBSCAN para agrupar similares
  - Reconocimiento facial con DeepFace
  - OCR en imágenes + regex para patrones
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger("maer.image")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"}


# ═══════════════════════════════════════════════
# Hash perceptual para detección de duplicados
# ═══════════════════════════════════════════════

def compute_image_hashes(path: Path) -> dict:
    """
    Calcula hashes perceptuales de una imagen.
    Retorna: {phash, ahash, dhash}
    """
    try:
        import imagehash
        img = Image.open(str(path))
        return {
            "phash": str(imagehash.phash(img)),
            "ahash": str(imagehash.average_hash(img)),
            "dhash": str(imagehash.dhash(img)),
        }
    except Exception as e:
        logger.error(f"Error calculando hashes: {e}")
        return {"phash": "", "ahash": "", "dhash": ""}


def find_duplicates(base_dir: Path, threshold: int = 10,
                    max_files: int = 1000) -> dict:
    """
    Busca imágenes duplicadas en una carpeta usando pHash.
    threshold: distancia máxima de Hamming para considerar duplicados.

    Retorna: {
        ok: bool,
        duplicates: [{group: [paths], distance: int}],
        total_images: int,
        total_groups: int
    }
    """
    try:
        import imagehash
    except ImportError:
        return {"ok": False, "error": "imagehash no instalado"}

    images = []
    hashes = []
    count = 0

    for root, dirs, files in os.walk(base_dir):
        # Exclusiones de seguridad
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {
            "node_modules", "__pycache__", ".venv", "venv"
        }]
        for name in files:
            if count >= max_files:
                break
            p = Path(root) / name
            if p.suffix.lower() not in IMAGE_EXTS:
                continue
            try:
                img = Image.open(str(p))
                h = imagehash.phash(img)
                images.append(str(p))
                hashes.append(h)
                count += 1
            except Exception:
                continue

    # Encontrar grupos de duplicados
    used = set()
    groups = []

    for i in range(len(hashes)):
        if i in used:
            continue
        group = [images[i]]
        distances = []
        for j in range(i + 1, len(hashes)):
            if j in used:
                continue
            dist = hashes[i] - hashes[j]
            if dist <= threshold:
                group.append(images[j])
                distances.append(dist)
                used.add(j)
        if len(group) > 1:
            used.add(i)
            groups.append({
                "group": group,
                "count": len(group),
                "max_distance": int(max(distances)) if distances else 0,
            })

    return {
        "ok": True,
        "total_images": len(images),
        "total_groups": len(groups),
        "duplicates": groups,
    }


# ═══════════════════════════════════════════════
# Clustering de imágenes con DBSCAN
# ═══════════════════════════════════════════════

def cluster_images(base_dir: Path, eps: float = 15.0,
                   min_samples: int = 2, max_files: int = 500) -> dict:
    """
    Agrupa imágenes similares usando DBSCAN sobre hashes perceptuales.
    """
    try:
        import imagehash
        from sklearn.cluster import DBSCAN
    except ImportError as e:
        return {"ok": False, "error": f"Dependencia faltante: {e}"}

    images = []
    hash_arrays = []
    count = 0

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {
            "node_modules", "__pycache__", ".venv"
        }]
        for name in files:
            if count >= max_files:
                break
            p = Path(root) / name
            if p.suffix.lower() not in IMAGE_EXTS:
                continue
            try:
                img = Image.open(str(p))
                h = imagehash.phash(img)
                # Convertir hash a array numérico
                hash_array = np.array([int(b) for b in bin(int(str(h), 16))[2:].zfill(64)])
                images.append(str(p))
                hash_arrays.append(hash_array)
                count += 1
            except Exception:
                continue

    if len(hash_arrays) < 2:
        return {"ok": True, "clusters": [], "total_images": len(images),
                "message": "Insuficientes imágenes para clustering"}

    X = np.array(hash_arrays)

    # DBSCAN clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="hamming")
    labels = clustering.fit_predict(X)

    # Organizar clusters
    clusters = {}
    for idx, label in enumerate(labels):
        if label == -1:
            continue  # Ruido
        label_str = str(label)
        if label_str not in clusters:
            clusters[label_str] = []
        clusters[label_str].append(images[idx])

    cluster_list = [
        {"cluster_id": int(k), "images": v, "count": len(v)}
        for k, v in clusters.items()
    ]

    noise_count = sum(1 for l in labels if l == -1)

    return {
        "ok": True,
        "total_images": len(images),
        "total_clusters": len(cluster_list),
        "noise_images": noise_count,
        "clusters": cluster_list,
    }


# ═══════════════════════════════════════════════
# Reconocimiento facial con DeepFace
# ═══════════════════════════════════════════════

def detect_faces(path: Path) -> dict:
    """
    Detecta rostros en una imagen usando DeepFace.
    Retorna: {ok, faces: [{region, confidence}], total_faces}
    """
    try:
        from deepface import DeepFace
    except ImportError:
        return {"ok": False, "error": "DeepFace no instalado", "faces": []}

    if not path.exists():
        return {"ok": False, "error": f"Archivo no existe: {path}", "faces": []}

    try:
        faces = DeepFace.extract_faces(
            img_path=str(path),
            detector_backend="opencv",
            enforce_detection=False,
        )

        face_list = []
        for face in faces:
            if face.get("confidence", 0) > 0.5:
                region = face.get("facial_area", {})
                face_list.append({
                    "x": region.get("x", 0),
                    "y": region.get("y", 0),
                    "w": region.get("w", 0),
                    "h": region.get("h", 0),
                    "confidence": round(face.get("confidence", 0), 4),
                })

        return {
            "ok": True,
            "path": str(path),
            "total_faces": len(face_list),
            "faces": face_list,
        }
    except Exception as e:
        logger.error(f"Error detectando rostros: {e}")
        return {"ok": False, "error": str(e), "faces": []}


def find_and_group_faces(base_dir: Path, max_files: int = 200,
                         distance_threshold: float = 0.6) -> dict:
    """
    Busca rostros en todas las imágenes de una carpeta y los agrupa
    por similitud usando embeddings faciales.
    """
    try:
        from deepface import DeepFace
    except ImportError:
        return {"ok": False, "error": "DeepFace no instalado"}

    embeddings = []
    face_meta = []
    count = 0

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {
            "node_modules", "__pycache__", ".venv"
        }]
        for name in files:
            if count >= max_files:
                break
            p = Path(root) / name
            if p.suffix.lower() not in IMAGE_EXTS:
                continue

            try:
                result = DeepFace.represent(
                    img_path=str(p),
                    model_name="Facenet",
                    detector_backend="opencv",
                    enforce_detection=False,
                )
                for face in result:
                    emb = face.get("embedding")
                    if emb:
                        embeddings.append(emb)
                        region = face.get("facial_area", {})
                        face_meta.append({
                            "path": str(p),
                            "region": region,
                        })
                count += 1
            except Exception:
                count += 1
                continue

    if len(embeddings) < 2:
        return {
            "ok": True, "groups": [], "total_faces": len(embeddings),
            "message": "Insuficientes rostros para agrupar"
        }

    # Clustering de embeddings faciales
    try:
        from sklearn.cluster import DBSCAN
        X = np.array(embeddings)
        clustering = DBSCAN(eps=distance_threshold, min_samples=2, metric="cosine")
        labels = clustering.fit_predict(X)

        groups = {}
        for idx, label in enumerate(labels):
            if label == -1:
                continue
            label_str = str(label)
            if label_str not in groups:
                groups[label_str] = []
            groups[label_str].append(face_meta[idx])

        group_list = [
            {"group_id": int(k), "faces": v, "count": len(v)}
            for k, v in groups.items()
        ]

        return {
            "ok": True,
            "total_faces": len(embeddings),
            "total_groups": len(group_list),
            "groups": group_list,
        }
    except Exception as e:
        return {"ok": False, "error": f"Error en clustering: {e}"}


# ═══════════════════════════════════════════════
# Indexación de imágenes
# ═══════════════════════════════════════════════

def index_images(base_dir: Path, max_files: int = 500,
                 compute_faces: bool = False) -> dict:
    """
    Crea un índice completo de imágenes con metadatos.
    """
    index = []
    count = 0

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {
            "node_modules", "__pycache__", ".venv"
        }]
        for name in files:
            if count >= max_files:
                break
            p = Path(root) / name
            if p.suffix.lower() not in IMAGE_EXTS:
                continue

            entry = {
                "path": str(p),
                "name": p.name,
                "ext": p.suffix.lower(),
                "size_bytes": p.stat().st_size,
            }

            # Dimensiones
            try:
                img = Image.open(str(p))
                entry["width"] = img.width
                entry["height"] = img.height
                entry["mode"] = img.mode
            except Exception:
                entry["width"] = 0
                entry["height"] = 0

            # Hashes
            hashes = compute_image_hashes(p)
            entry["hashes"] = hashes

            # Rostros (opcional, lento)
            if compute_faces:
                faces_result = detect_faces(p)
                entry["faces"] = faces_result.get("total_faces", 0)

            index.append(entry)
            count += 1

    return {
        "ok": True,
        "total_images": len(index),
        "base_dir": str(base_dir),
        "index": index,
    }
