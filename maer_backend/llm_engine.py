#!/usr/bin/env python3
# 🦁 MAER LLM Engine — Inferencia Local con llama.cpp
# Leonel Mojica — Ecatepec MX — 2026

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger("maer_llm")

# ── Configuración del modelo ──
# Podemos usar un modelo muy compacto para extracción de JSON, por ejemplo
# "bartowski/Llama-3.2-1B-Instruct-GGUF" para que sea ultra-rápido y liviano en Mac,
# o Qwen2.5-1.5B-Instruct-GGUF.
REPO_ID = os.environ.get("MAER_LLM_REPO_ID", "bartowski/Llama-3.2-1B-Instruct-GGUF")
FILENAME = os.environ.get("MAER_LLM_FILENAME", "Llama-3.2-1B-Instruct-Q4_K_M.gguf")

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

class LLMEngine:
    _instance = None
    _llm = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMEngine, cls).__new__(cls)
        return cls._instance

    def _ensure_model_downloaded(self) -> str:
        """Descarga el modelo GGUF usando huggingface_hub si no existe localmente."""
        from huggingface_hub import hf_hub_download
        
        logger.info(f"Verificando modelo {REPO_ID}/{FILENAME}...")
        try:
            model_path = hf_hub_download(
                repo_id=REPO_ID,
                filename=FILENAME,
                cache_dir=str(MODELS_DIR),
                local_dir=str(MODELS_DIR),
                local_dir_use_symlinks=False
            )
            return model_path
        except Exception as e:
            logger.error(f"Error descargando el modelo desde HF: {e}")
            raise Exception(f"No se pudo descargar el modelo LLM: {e}")

    def load_model(self):
        """Carga el modelo en memoria (llama-cpp-python)."""
        if self._llm is not None:
            return self._llm

        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError("Librería llama-cpp-python no instalada. Revisa requirements-llm.txt")

        model_path = self._ensure_model_downloaded()
        
        logger.info("Cargando modelo en memoria. Esto puede tardar unos segundos...")
        
        # Cargar con aceleración Metal si está disponible
        self._llm = Llama(
            model_path=model_path,
            n_ctx=4096,          # Context window (suficiente para la mayoría de documentos procesados)
            n_threads=4,         # Threads lógicos
            n_gpu_layers=0,      # 0 para forzar CPU en Intel Mac (Evita basura/alucinación por GPU AMD)
            verbose=False,
            chat_format="llama-3" # Formato específico para LLaMa 3
        )
        logger.info("¡LLM Local cargado exitosamente en memoria RAM/VRAM!")
        return self._llm

    def generate_response(self, prompt: str, system_prompt: str = "Eres MAER AI, un asistente experto en análisis documental.", max_tokens: int = 512, temperature: float = 0.2):
        """Generador genérico usando Create Chat Completion."""
        llm = self.load_model()
        try:
            response = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["<|eot_id|>"] # Stop token de Llama 3
            )
            return {
                "ok": True, 
                "text": response["choices"][0]["message"]["content"].strip(),
                "usage": response.get("usage", {})
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def summarize_text(self, text: str) -> dict:
        """Resume un texto largo usando el LLM."""
        if not text.strip():
            return {"ok": False, "error": "Texto vacío"}

        system = "Eres un asistente experto. Resume el siguiente documento al español destacando los puntos clave de manera muy precisa y omitiendo información de relleno."
        prompt = f"Resume el siguiente texto:\n\n{text[:4000]}" # Trunco text para no saturar ctx
        
        return self.generate_response(prompt=prompt, system_prompt=system, max_tokens=1024, temperature=0.3)

    def extract_structured_data(self, text: str, schema_description: str) -> dict:
        """Obliga al modelo a responder con un formato JSON."""
        if not text.strip():
            return {"ok": False, "error": "Texto vacío"}

        system = (
            "Eres un extractor experto de datos. Tu tarea es analizar el texto provisto y devolver "
            "EXCLUSIVAMENTE un bloque de código JSON válido con la información y nada más. No expliques, "
            "no uses markdown fuera del bloque JSON."
        )
        prompt = f"Texto del documento:\n{text[:4000]}\n\nInstrucciones:\nExtrae los datos en formato JSON según el siguiente esquema/campos solicitados:\n{schema_description}\n\nResponde SOLO con JSON."

        res = self.generate_response(prompt=prompt, system_prompt=system, max_tokens=2048, temperature=0.1)
        
        if res["ok"]:
            raw_text = res["text"]
            # Intentar limpiar si el modelo añadió markdown (```json ... ```)
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[-1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[-1].split("```")[0].strip()
                
            try:
                parsed_json = json.loads(raw_text)
                res["json"] = parsed_json
            except json.JSONDecodeError:
                res["json_error"] = "El modelo no generó un JSON válido."
                res["raw_text"] = raw_text
                
        return res

# Instancia global (Singleton)
llm_engine = LLMEngine()

def get_llm_engine():
    return llm_engine
