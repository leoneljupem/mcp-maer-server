#!/usr/bin/env node
// 🦁 MCP MAER SERVER v2.0 — Motor Multimodal de Análisis Documental
// Leonel Mojica — Ecatepec MX — macOS Tahoe — 2026

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";
import { dirname } from "path";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PY_BACKEND = path.join(__dirname, "maer_backend", "maer_files.py");

// Detección dinámica del ejecutable de Python
const possiblePyPaths = [
  path.join(__dirname, ".venv", "bin", "python"),
  path.join(__dirname, "venv", "bin", "python"),
  path.join(process.env.HOME || "/Users/houssenm", "miniforge3_x86", "envs", "maer_env", "bin", "python"),
  "/opt/homebrew/bin/python3",
  "/usr/local/bin/python3",
  "/usr/bin/python3",
  "python3"
];

let PY_EXEC = "python3";
for (const p of possiblePyPaths) {
  if (p === "python3" || fs.existsSync(p)) {
    PY_EXEC = p;
    if (fs.existsSync(p)) break; // Si encontramos uno real absoluto, detenemos
  }
}

function runPythonAction(action, payload) {
  return new Promise((resolve, reject) => {
    const py = spawn(PY_EXEC, [PY_BACKEND, action, JSON.stringify(payload)], {
      stdio: ["ignore", "pipe", "pipe"],
    });

    let out = "";
    let err = "";

    py.stdout.on("data", (data) => {
      out += data.toString();
    });

    py.stderr.on("data", (data) => {
      err += data.toString();
    });

    py.on("close", (code) => {
      if (code !== 0) {
        return reject(new Error(`Python falló con código ${code}. Salida de error: ${err}`));
      }
      try {
        const parsed = JSON.parse(out || "{}");
        resolve(parsed);
      } catch (e) {
        reject(
          new Error(
            `No se pudo parsear salida Python (code=${code}): ${e} | stdout=${out} | stderr=${err}`
          )
        );
      }
    });
  });
}

// ═══════════════════════════════════════════════════════════
// Definición de herramientas
// ═══════════════════════════════════════════════════════════

const toolDefinitions = [
  {
    name: "ping_maer",
    description: "Comprueba que el servidor MCP MAER está vivo",
    inputSchema: {
      type: "object",
      properties: {
        message: { type: "string", description: "Mensaje opcional para eco" },
      },
      required: [],
    },
  },
  {
    name: "suma_simple",
    description: "Suma dos números (a + b)",
    inputSchema: {
      type: "object",
      properties: {
        a: { type: "number", description: "Primer número" },
        b: { type: "number", description: "Segundo número" },
      },
      required: ["a", "b"],
    },
  },
  {
    name: "maer_search_files",
    description:
      "Busca archivos por nombre y/o contenido de texto dentro de una carpeta base",
    inputSchema: {
      type: "object",
      properties: {
        base_dir: {
          type: "string",
          description: "Ruta base donde buscar (por defecto, carpeta HOME)",
        },
        query: {
          type: "string",
          description: "Texto a buscar (ej. 'jose luis mora')",
        },
        mode: {
          type: "string",
          enum: ["name", "content", "both"],
          description: "Tipo de búsqueda: por nombre, contenido o ambos",
        },
        max_results: {
          type: "number",
          description: "Máximo resultados (default 100)",
        },
      },
      required: ["query"],
    },
  },
  {
    name: "maer_analyze_file",
    description:
      "Analiza un archivo (tamaño, extensión, hash SHA-256, preview de contenido)",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "Ruta absoluta del archivo a analizar",
        },
      },
      required: ["path"],
    },
  },
  {
    name: "maer_fix_code_file",
    description:
      "Corrige un archivo de código quitando espacios finales de líneas (backup .maer.bak)",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "Ruta absoluta del archivo de código a corregir",
        },
        mode: {
          type: "string",
          description: "Modo de corrección (por ahora solo 'strip_trailing')",
        },
      },
      required: ["path"],
    },
  },
  {
    name: "maer_extract_text",
    description:
      "Extrae texto de un archivo (PDF con OCR si es escaneado, DOCX, imágenes, texto/código).",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "Ruta absoluta del archivo",
        },
        ocr_for_pdf: {
          type: "boolean",
          description: "Si es PDF, usar OCR cuando no haya texto suficiente (default true)",
        },
        max_chars: {
          type: "number",
          description: "Máximo de caracteres a devolver (0 = sin límite, default 0)",
        },
      },
      required: ["path"],
    },
  },
  {
    name: "maer_index_full",
    description:
      "Indexa una carpeta completa (texto, PDF+OCR, DOCX, imágenes) y guarda un JSON con metadatos y snippets.",
    inputSchema: {
      type: "object",
      properties: {
        base_dir: {
          type: "string",
          description: "Carpeta base a indexar",
        },
        out_file: {
          type: "string",
          description: "Ruta del archivo JSON de salida (default: <base_dir>/maer_index.json)",
        },
        max_files: {
          type: "number",
          description: "Máximo de archivos a procesar (default 500)",
        },
        ocr_for_pdf: {
          type: "boolean",
          description: "Usar OCR en PDFs cuando sea necesario (default true)",
        },
        snippet_chars: {
          type: "number",
          description: "Longitud del snippet de texto guardado por archivo (default 1000)",
        },
      },
      required: ["base_dir"],
    },
  },
  {
    name: "maer_search_index",
    description:
      "Busca en un índice JSON generado por maer_index_full (por path y snippet).",
    inputSchema: {
      type: "object",
      properties: {
        index_file: {
          type: "string",
          description: "Ruta al índice JSON",
        },
        base_dir: {
          type: "string",
          description: "Carpeta base para deducir index_file si no se pasa",
        },
        query: {
          type: "string",
          description: "Texto a buscar dentro de los snippets y paths del índice",
        },
        max_results: {
          type: "number",
          description: "Máximo de resultados a devolver (default 50)",
        },
      },
      required: ["query"],
    },
  },
  {
    name: "maer_detect_ids",
    description:
      "Detecta CURP (válidas/invalidas/homonimias), RFC e INE en un archivo o índice y extrae correos/teléfonos/NSS.",
    inputSchema: {
      type: "object",
      properties: {
        mode: {
          type: "string",
          enum: ["file", "index"],
          description: "Modo: 'file' para un solo archivo, 'index' para revisar un índice completo",
        },
        path: {
          type: "string",
          description: "Ruta del archivo a analizar (modo file)",
        },
        ocr_for_pdf: {
          type: "boolean",
          description: "Usar OCR en PDFs (modo file, default true)",
        },
        index_file: {
          type: "string",
          description: "Ruta al índice JSON (modo index)",
        },
        base_dir: {
          type: "string",
          description: "Carpeta base para deducir index_file (modo index)",
        },
        max_entries: {
          type: "number",
          description: "Máximo entradas del índice a revisar (modo index, default 500)",
        },
      },
      required: ["mode"],
    },
  },
  {
    name: "maer_detect_related",
    description:
      "Dado un CURP/RFC/INE, busca en un índice archivos donde aparezca y extrae datos asociados.",
    inputSchema: {
      type: "object",
      properties: {
        id_value: {
          type: "string",
          description: "Identificador a buscar (CURP, RFC o clave INE)",
        },
        index_file: {
          type: "string",
          description: "Ruta al índice JSON",
        },
        base_dir: {
          type: "string",
          description: "Carpeta base para deducir index_file si no se pasa",
        },
        max_entries: {
          type: "number",
          description: "Máximo entradas del índice a revisar (default 500)",
        },
      },
      required: ["id_value"],
    },
  },
  {
    name: "maer_curp_renapo_check",
    description:
      "Consulta una CURP contra un servicio REST que valida en RENAPO.",
    inputSchema: {
      type: "object",
      properties: {
        curp: {
          type: "string",
          description: "CURP a validar contra RENAPO",
        },
      },
      required: ["curp"],
    },
  },
  // ═══════════════════════════════════════════════════════════
  // Nuevas herramientas multimodales v2.0
  // ═══════════════════════════════════════════════════════════
  {
    name: "maer_ocr_multimodal",
    description:
      "OCR avanzado con selección de motor (Tesseract, EasyOCR, PaddleOCR) y preprocesamiento OpenCV. Incluye cacheo inteligente.",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "Ruta del archivo (PDF o imagen)",
        },
        engine: {
          type: "string",
          enum: ["auto", "tesseract", "easyocr", "paddleocr"],
          description: "Motor OCR a usar (default: auto = selecciona el mejor)",
        },
        use_cache: {
          type: "boolean",
          description: "Usar cache de OCR si disponible (default true)",
        },
      },
      required: ["path"],
    },
  },
  {
    name: "maer_extract_tables",
    description:
      "Extrae tablas y formularios de un PDF usando pdfplumber. Retorna tablas como listas de diccionarios.",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "Ruta del archivo PDF",
        },
        max_pages: {
          type: "number",
          description: "Máximo de páginas a procesar (default 50)",
        },
      },
      required: ["path"],
    },
  },
  {
    name: "maer_nlp_entities",
    description:
      "Detecta entidades con NLP (personas, organizaciones, fechas, ubicaciones) usando spaCy. Clasifica tipo de documento.",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "Ruta del archivo (extrae texto automáticamente)",
        },
        text: {
          type: "string",
          description: "Texto directo a analizar (alternativa a path)",
        },
      },
      required: [],
    },
  },
  {
    name: "maer_image_duplicates",
    description:
      "Encuentra imágenes duplicadas o similares en una carpeta usando hash perceptual (pHash/dHash).",
    inputSchema: {
      type: "object",
      properties: {
        base_dir: {
          type: "string",
          description: "Carpeta con imágenes a analizar",
        },
        threshold: {
          type: "number",
          description: "Umbral de similitud: 0 = idénticas, 10 = similares (default 10)",
        },
        max_files: {
          type: "number",
          description: "Máximo de imágenes a procesar (default 1000)",
        },
      },
      required: ["base_dir"],
    },
  },
  {
    name: "maer_face_detect",
    description:
      "Detecta rostros en imágenes. En modo carpeta, agrupa rostros similares usando embeddings faciales.",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "Ruta de una imagen para detección individual",
        },
        base_dir: {
          type: "string",
          description: "Carpeta para búsqueda y agrupación de rostros",
        },
        max_files: {
          type: "number",
          description: "Máximo de archivos a procesar (default 200)",
        },
      },
      required: [],
    },
  },
  {
    name: "maer_cluster_files",
    description:
      "Clustering automático de archivos por similitud visual (imágenes) usando DBSCAN.",
    inputSchema: {
      type: "object",
      properties: {
        base_dir: {
          type: "string",
          description: "Carpeta a analizar",
        },
        type: {
          type: "string",
          enum: ["images"],
          description: "Tipo de clustering (default: images)",
        },
        max_files: {
          type: "number",
          description: "Máximo de archivos a procesar (default 500)",
        },
      },
      required: ["base_dir"],
    },
  },
  // ═══════════════════════════════════════════════════════════
  // LLM Local y Renapo Avanzado
  // ═══════════════════════════════════════════════════════════
  {
    name: "maer_llm_summarize",
    description: "Resume documentos usando un LLM local offline (Llama.cpp)",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string", description: "Ruta del archivo a resumir" },
        text: { type: "string", description: "Texto directo a resumir (opcional si se da path)" },
      },
      required: [],
    },
  },
  {
    name: "maer_llm_extract_json",
    description: "Extrae estructuradamente (en JSON) los datos pedidos desde un texto o archivo usando un LLM local",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string", description: "Ruta de archivo" },
        text: { type: "string", description: "Texto directo" },
        schema_description: { type: "string", description: "Instrucciones de los datos a extraer (Ej: 'Extrae Nombre y Fecha')" },
      },
      required: ["schema_description"],
    },
  },
  {
    name: "maer_verify_identity",
    description: "Realiza una validación Renapo avanzada: lee el documento, valida CURP, y usa el LLM para comprobar concordancia de nombre e identidad",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string", description: "Ruta del archivo a verificar" },
      },
      required: ["path"],
    },
  },
  {
    name: "maer_deep_search",
    description: "Búsqueda masiva y difusa (fuzzy search) de palabras o frases (mayúsculas/minúsculas) en documentos, imágenes y PDFs usando NLP y distancias.",
    inputSchema: {
      type: "object",
      properties: {
        base_dir: { type: "string", description: "Carpeta base a buscar" },
        query: { type: "string", description: "Palabra o frase a buscar" },
        fuzzy_match: { type: "boolean", description: "Permitir similitud o variaciones (default true)" },
      },
      required: ["base_dir", "query"],
    },
  },
  {
    name: "maer_workspace_analyzer",
    description: "Analizador de carpetas para encontrar proyectos duplicados, código similar o archivos basura innecesarios y sugerir limpieza o fusión.",
    inputSchema: {
      type: "object",
      properties: {
        base_dir: { type: "string", description: "Carpeta base a analizar (ej. /Users/houssenm/Proyectos)" },
      },
      required: ["base_dir"],
    },
  }
];

// ═══════════════════════════════════════════════════════════
// Tool handler
// ═══════════════════════════════════════════════════════════

async function handleTool(name, args = {}) {
  if (name === "ping_maer") {
    const msg = args.message || "MAER MCP OK en macOS Tahoe";
    return `🦁 MCP MAER v2.0 responde: ${msg}`;
  }

  if (name === "suma_simple") {
    const a = Number(args.a);
    const b = Number(args.b);
    if (Number.isNaN(a) || Number.isNaN(b)) {
      throw new Error("Parámetros 'a' y 'b' deben ser numéricos");
    }
    const result = a + b;
    return `Resultado de ${a} + ${b} = ${result}`;
  }

  // Mapeo de nombre de herramienta MCP → acción Python
  const toolActionMap = {
    maer_search_files: "search_files",
    maer_analyze_file: "analyze_file",
    maer_fix_code_file: "fix_code_file",
    maer_extract_text: "extract_text",
    maer_index_full: "index_full",
    maer_search_index: "search_index",
    maer_detect_ids: "detect_ids",
    maer_detect_related: "detect_related",
    maer_curp_renapo_check: "curp_renapo_check",
    // Nuevas
    maer_ocr_multimodal: "ocr_multimodal",
    maer_extract_tables: "extract_tables",
    maer_nlp_entities: "nlp_entities",
    maer_image_duplicates: "image_duplicates",
    maer_face_detect: "face_detect",
    maer_cluster_files: "cluster_files",
    // LLM y Renapo Avanzado
    maer_llm_summarize: "llm_summarize",
    maer_llm_extract_json: "llm_extract_json",
    maer_verify_identity: "renapo_verify_identity",
    maer_deep_search: "deep_search",
    maer_workspace_analyzer: "workspace_analyzer",
  };

  const pyAction = toolActionMap[name];
  if (pyAction) {
    const pyResult = await runPythonAction(pyAction, args);
    return JSON.stringify(pyResult, null, 2);
  }

  throw new Error(`Herramienta desconocida: ${name}`);
}

// ═══════════════════════════════════════════════════════════
// Resources
// ═══════════════════════════════════════════════════════════

const resourceDefinitions = [
  {
    uri: "maer://info/servidor",
    name: "Información del servidor MAER en Mac",
    description: "Descripción del servidor MCP MAER v2.0 en macOS Tahoe",
    mimeType: "text/plain",
  },
];

async function listDynamicResources() {
  return [];
}

async function getResourceContent(uri) {
  if (uri === "maer://info/servidor") {
    return [
      "🦁 Servidor MCP MAER 2.0.0 — Motor Multimodal en macOS Tahoe",
      "Autor: Leonel Mojica — Ecatepec de Morelos, MX",
      "Descripción: Servidor MCP para análisis documental, OCR multimodal, validación de IDs mexicanos, reconocimiento facial y clustering.",
      "",
      "Tools originales: ping_maer, suma_simple, maer_search_files, maer_analyze_file, maer_fix_code_file, maer_extract_text, maer_index_full, maer_search_index, maer_detect_ids, maer_detect_related, maer_curp_renapo_check",
      "",
      "Tools v2.0: maer_ocr_multimodal, maer_extract_tables, maer_nlp_entities, maer_image_duplicates, maer_face_detect, maer_cluster_files",
    ].join("\n");
  }
  throw new Error(`Recurso desconocido: ${uri}`);
}

// ═══════════════════════════════════════════════════════════
// Prompts
// ═══════════════════════════════════════════════════════════

const promptDefinitions = [
  {
    name: "maer_sistema",
    description:
      "Prompt de sistema base para hablar con MAER usando este MCP",
    arguments: [],
  },
];

function generatePrompt(name, _args = {}) {
  if (name === "maer_sistema") {
    return [
      {
        role: "system",
        content:
          "Eres MAER v2.0, una IA local avanzada en macOS Tahoe que usa este servidor MCP para análisis documental multimodal: búsqueda de archivos, OCR avanzado (Tesseract/EasyOCR/PaddleOCR), extracción de tablas, detección/validación de CURP/RFC/INE, consulta RENAPO, clasificación NLP de entidades, detección de imágenes duplicadas, reconocimiento facial y clustering automático.",
      },
    ];
  }
  throw new Error(`Prompt desconocido: ${name}`);
}

// ═══════════════════════════════════════════════════════════
// Server setup
// ═══════════════════════════════════════════════════════════

const server = new Server(
  {
    name: "maer-mcp-server",
    version: "2.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: toolDefinitions,
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    const result = await handleTool(name, args || {});
    return {
      content: [{ type: "text", text: result }],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text:
            "Error en herramienta: " +
            (error instanceof Error ? error.message : String(error)),
        },
      ],
      isError: true,
    };
  }
});

server.setRequestHandler(ListResourcesRequestSchema, async () => {
  const dynamic = await listDynamicResources();
  return {
    resources: [...resourceDefinitions, ...dynamic],
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;
  try {
    const content = await getResourceContent(uri);
    const resource = resourceDefinitions.find((r) => r.uri === uri);
    return {
      contents: [
        {
          uri,
          mimeType: resource?.mimeType || "text/plain",
          text: content,
        },
      ],
    };
  } catch (error) {
    throw new McpError(
      ErrorCode.InvalidRequest,
      "No se pudo leer el recurso: " +
        (error instanceof Error ? error.message : String(error))
    );
  }
});

server.setRequestHandler(ListPromptsRequestSchema, async () => ({
  prompts: promptDefinitions,
}));

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    const messages = generatePrompt(name, args || {});
    return {
      description: promptDefinitions.find((p) => p.name === name)?.description,
      messages,
    };
  } catch (error) {
    throw new McpError(
      ErrorCode.InvalidRequest,
      "No se pudo generar el prompt: " +
        (error instanceof Error ? error.message : String(error))
    );
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("🦁 MCP MAER Server v2.0 ejecutándose en macOS Tahoe por stdio");
}

main().catch((error) => {
  console.error("Error fatal MCP en Mac:", error);
  process.exit(1);
});
