#!/usr/bin/env python3
import json
import subprocess
import os
import sys
import psutil
import re
import requests
import glob
import shutil
import base64
import mimetypes
from datetime import datetime
from ollama import Client
from duckduckgo_search import DDGS

# --- RAINBOW TECHNOLOGY SIGNATURES ---
# #xyz-rainbow #xyz-rainbowtechnology #rainbowtechnology.xyz

if os.name == 'nt':
    import msvcrt
else:
    import termios
    import tty

# Readline: Tab autocompletes commands starting with /
COMMANDS = ['/exit', '/settings', '/tools', '/skills', '/search', '/history',
            '/pull ', '/img ']

def _cmd_completer(text, state):
    if text.startswith('/'):
        matches = [c for c in COMMANDS if c.startswith(text)]
        return matches[state] if state < len(matches) else None
    return None

try:
    import readline
    readline.set_completer(_cmd_completer)
    readline.set_completer_delims('')   # treat the whole line as one token
    readline.parse_and_bind('tab: complete')
except ImportError:
    pass

CORE_ID        = "rainbow-tech-v4.8-full"
SESSIONS_DIR   = os.path.expanduser("~/.ollama-run/sessions")
CONFIG_FILE    = os.path.expanduser("~/.ollama-run/config.json")
SKILLS_CATALOG = os.path.expanduser("~/.ollama-run/skills_catalog.json")
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

LOGSEQ_PATH = os.path.expanduser("~/Documents/Logseq/pages")
if os.path.exists("/media/cloud-xyz/X/[Graph]/pages"):
    LOGSEQ_PATH = "/media/cloud-xyz/X/[Graph]/pages"

client = Client()

# ── COLORES POR TEMA ───────────────────────────────────────────────────────────
THEMES = {
    "default": dict(
        THINK_L="\033[1;96m", THINK="\033[0;96m", RESP="\033[0;92m",
        TOOL="\033[1;33m",    TOOL_R="\033[0;33m", INFO="\033[0;90m",
        ACCENT="\033[1;96m",  SEL="\033[1;32m",    WARN="\033[1;33m",
        OK="\033[1;32m",      ERR="\033[1;31m",    DIM="\033[2m",
    ),
    "matrix": dict(
        THINK_L="\033[1;32m", THINK="\033[0;32m", RESP="\033[1;32m",
        TOOL="\033[0;32m",    TOOL_R="\033[2;32m", INFO="\033[2;32m",
        ACCENT="\033[1;32m",  SEL="\033[1;92m",   WARN="\033[1;32m",
        OK="\033[1;32m",      ERR="\033[0;31m",   DIM="\033[2m",
    ),
    "dracula": dict(
        THINK_L="\033[1;35m", THINK="\033[0;35m", RESP="\033[0;95m",
        TOOL="\033[1;33m",    TOOL_R="\033[0;33m", INFO="\033[0;90m",
        ACCENT="\033[1;35m",  SEL="\033[1;95m",   WARN="\033[1;33m",
        OK="\033[1;32m",      ERR="\033[1;31m",   DIM="\033[2m",
    ),
    "amber": dict(
        THINK_L="\033[1;33m", THINK="\033[0;33m", RESP="\033[1;33m",
        TOOL="\033[0;33m",    TOOL_R="\033[2;33m", INFO="\033[2;33m",
        ACCENT="\033[1;33m",  SEL="\033[1;93m",   WARN="\033[1;31m",
        OK="\033[1;33m",      ERR="\033[1;31m",   DIM="\033[2m",
    ),
    "mono": dict(
        THINK_L="\033[1m",  THINK="\033[2m",  RESP="\033[0m",
        TOOL="\033[1m",     TOOL_R="\033[2m", INFO="\033[2m",
        ACCENT="\033[1m",   SEL="\033[1m",    WARN="\033[1m",
        OK="\033[1m",       ERR="\033[1m",    DIM="\033[2m",
    ),
}
C_RESET = "\033[0m"

# ── SESIÓN ─────────────────────────────────────────────────────────────────────
class Session:
    def __init__(self):
        self.model         = ""
        self.thinking_mode = "ON"
        self.thinking_level= "Medium"
        self.theme         = "default"
        self.tools_enabled = {
            'web_search':        True,
            'execute_shell':     True,
            'logseq_io':         True,
            'get_system_status': True,
            'describe_image':    True,
            'ocr_image':         True,
        }
        self.skills_enabled = {}   # name → bool (default OFF)
        self._load_config()

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                d = json.loads(open(CONFIG_FILE).read())
                self.model          = d.get('model', '')
                self.thinking_mode  = d.get('thinking_mode', 'ON')
                self.thinking_level = d.get('thinking_level', 'Medium')
                self.theme          = d.get('theme', 'default')
                te = d.get('tools_enabled')
                if isinstance(te, dict): self.tools_enabled.update(te)
                se = d.get('skills_enabled')
                if isinstance(se, dict): self.skills_enabled.update(se)
            except Exception: pass

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({
                'model': self.model,
                'thinking_mode': self.thinking_mode,
                'thinking_level': self.thinking_level,
                'theme': self.theme,
                'tools_enabled': self.tools_enabled,
                'skills_enabled': self.skills_enabled,
            }, f, indent=2)

    @property
    def c(self):
        return THEMES.get(self.theme, THEMES['default'])

session = Session()

def C(key): return session.c.get(key, "")

# ── TOOLS DEFINITIONS ──────────────────────────────────────────────────────────
ALL_TOOLS = [
    {'type':'function','function':{'name':'web_search','description':'Búsqueda web.','parameters':{'type':'object','properties':{'query':{'type':'string'}},'required':['query']}}},
    {'type':'function','function':{'name':'execute_shell','description':'Comandos Bash.','parameters':{'type':'object','properties':{'command':{'type':'string'}},'required':['command']}}},
    {'type':'function','function':{'name':'logseq_io','description':'Logseq.','parameters':{'type':'object','properties':{'action':{'type':'string','enum':['read','write','append']},'page_name':{'type':'string'},'content':{'type':'string'}},'required':['action','page_name']}}},
    {'type':'function','function':{'name':'get_system_status','description':'Estado del sistema.','parameters':{'type':'object','properties':{}}}},
    {'type':'function','function':{'name':'describe_image','description':'Analiza y describe el contenido visual de una imagen usando un modelo vision. Úsala cuando el usuario mande una imagen o pregunte qué hay en ella.','parameters':{'type':'object','properties':{'image_path':{'type':'string','description':'Ruta local o URL de la imagen'},'question':{'type':'string','description':'Pregunta específica sobre la imagen'}},'required':['image_path']}}},
    {'type':'function','function':{'name':'ocr_image','description':'Extrae texto de una imagen mediante OCR (reconocimiento óptico de caracteres). Ideal para capturas de pantalla, documentos escaneados, fotos de texto.','parameters':{'type':'object','properties':{'image_path':{'type':'string','description':'Ruta local o URL de la imagen'},'lang':{'type':'string','description':'Idioma para OCR, ej: spa, eng, fra (default: spa+eng)'}},'required':['image_path']}}},
]

def get_active_tools():
    return [t for t in ALL_TOOLS if session.tools_enabled.get(t['function']['name'], True)]

# ── SKILLS CATALOG ─────────────────────────────────────────────────────────────
BUILTIN_SKILLS = [
    {"name": "code_review",   "description": "Revisa código en busca de bugs, mejoras y estilo", "prompt": "Eres un experto en code review. Analiza el código presentado detallando bugs, mejoras de rendimiento, legibilidad y mejores prácticas. Sé preciso y constructivo."},
    {"name": "translate",     "description": "Traducción precisa entre idiomas",                 "prompt": "Eres un traductor profesional experto. Detecta el idioma origen automáticamente y traduce al idioma destino solicitado con precisión, preservando el tono y contexto."},
    {"name": "summarize",     "description": "Resume textos largos de forma concisa",            "prompt": "Eres un experto en síntesis. Resume el texto dado de forma clara y estructurada, extrayendo los puntos clave, manteniendo la esencia sin perder información crítica."},
    {"name": "math_solver",   "description": "Resuelve problemas matemáticos paso a paso",      "prompt": "Eres un matemático experto. Resuelve cada problema paso a paso de forma clara, mostrando el razonamiento completo y verificando el resultado."},
    {"name": "sql_expert",    "description": "Genera y optimiza queries SQL",                   "prompt": "Eres un DBA experto en SQL. Genera queries optimizadas, explica el plan de ejecución y sugiere índices cuando sea relevante. Soporta PostgreSQL, MySQL y SQLite."},
    {"name": "regex_builder", "description": "Construye y explica expresiones regulares",       "prompt": "Eres un experto en expresiones regulares. Construye el regex solicitado, explica cada parte y proporciona ejemplos de matches y non-matches."},
    {"name": "git_helper",    "description": "Ayuda con comandos y flujos de Git",              "prompt": "Eres un experto en Git y control de versiones. Proporciona comandos exactos, explica los efectos y advierte sobre operaciones destructivas."},
    {"name": "api_designer",  "description": "Diseña y documenta APIs REST/GraphQL",            "prompt": "Eres un arquitecto de APIs. Diseña endpoints RESTful o schemas GraphQL siguiendo mejores prácticas, con ejemplos de request/response y consideraciones de autenticación."},
    {"name": "security_audit","description": "Analiza código en busca de vulnerabilidades",     "prompt": "Eres un experto en seguridad (OWASP). Analiza el código buscando vulnerabilidades como injection, XSS, CSRF, auth issues. Clasifica por severidad y sugiere mitigaciones."},
    {"name": "doc_writer",    "description": "Genera documentación técnica profesional",        "prompt": "Eres un technical writer experto. Genera documentación clara, completa y bien estructurada con ejemplos prácticos, siguiendo el formato solicitado (README, docstring, wiki)."},
]

def load_skills_catalog():
    catalog = list(BUILTIN_SKILLS)
    if os.path.exists(SKILLS_CATALOG):
        try:
            extra = json.loads(open(SKILLS_CATALOG).read())
            catalog += [s for s in extra if s.get('name') not in [x['name'] for x in catalog]]
        except Exception: pass
    return catalog

def search_skills_online(query):
    """Busca skills en un registro online (simulado con búsqueda web)."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"ollama AI assistant skill prompt {query}", max_results=5))
        skills = []
        for r in results:
            skills.append({
                "name": re.sub(r'[^a-z0-9_]', '_', r['title'][:30].lower()).strip('_'),
                "description": r['body'][:100],
                "prompt": f"Actúa como experto en {r['title']}. {r['body'][:200]}",
                "_source": r['href'],
            })
        return skills
    except Exception:
        return []

def get_active_skill_prompt():
    catalog = load_skills_catalog()
    active = [s for s in catalog if session.skills_enabled.get(s['name'], False)]
    if not active: return ""
    parts = [f"[SKILL: {s['name']}] {s['prompt']}" for s in active]
    return "\n\n" + "\n\n".join(parts)

# ── UTILIDADES ─────────────────────────────────────────────────────────────────
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_banner(version="v4.8"):
    return f"\n  {C('ACCENT')}[XYZ]{C_RESET} \033[1;37mOLLAMA-RUN{C_RESET} {C('INFO')}{version}{C_RESET}\n  {C('DIM')}────────────────────────────────────────{C_RESET}"

def print_tool_msg(msg):
    print(f"\n  {C('TOOL')}⚙  {msg}{C_RESET}")

def print_tool_result(name, preview):
    short = str(preview).strip().splitlines()[0][:120]
    print(f"  {C('TOOL_R')}↳ [{name}] {short}{C_RESET}\n")

# ── FUNCIONES DE HERRAMIENTAS ──────────────────────────────────────────────────
def get_system_status():
    print_tool_msg("Retrieving system status…")
    data = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "cpu": psutil.cpu_percent(), "ram_mb": psutil.virtual_memory().available // 10**6}
    print_tool_result("system_status", data)
    return json.dumps(data)

def web_search(query):
    print_tool_msg(f"Searching: {query}…")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        print_tool_result("web_search", f"{len(results)} results")
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        print_tool_result("web_search", f"ERROR: {e}")
        return str(e)

SHELL_DANGEROUS = [r'rm\s+-rf', r'\bdd\b', r'mkfs', r'chmod\s+777', r'>\s*/dev/',
                   r'curl.+\|\s*sh', r'wget.+\|\s*sh', r':\(\)\{', r'fork\s*bomb']

def execute_shell(command):
    print_tool_msg(f"Executing: {command}…")
    # Confirmación para comandos potencialmente destructivos
    if any(re.search(p, command, re.IGNORECASE) for p in SHELL_DANGEROUS):
        print(f"\n  {C('ERR')}⚠ DANGEROUS COMMAND DETECTED:{C_RESET} {command}")
        try:
            confirm = input(f"  {C('WARN')}Execute anyway? [y/N]{C_RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = 'n'
        if confirm not in ('y','yes'):
            return "Execution cancelled by user."
    try:
        res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=20)
        out = (res.stdout + res.stderr).strip()
        print_tool_result("shell", out[:200] or "(no output)")
        return f"OUT: {res.stdout}\nERR: {res.stderr}"
    except subprocess.TimeoutExpired:
        print_tool_result("shell", "ERROR: timeout (20s)")
        return "Error: command exceeded the 20 second time limit."
    except Exception as e:
        print_tool_result("shell", f"ERROR: {e}")
        return f"Error executing command: {e}"

def logseq_io(action, page_name, content=None):
    if not page_name.endswith(".md"): page_name += ".md"
    path = os.path.join(LOGSEQ_PATH, page_name)
    print_tool_msg(f"Logseq {action}: {page_name}…")
    try:
        if action == 'read':
            with open(path, 'r', encoding='utf-8') as f: data = f.read()
            print_tool_result("logseq", f"{len(data)} chars")
            return data
        elif action == 'write':
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f: f.write(content or "")
            print_tool_result("logseq", "written OK"); return "OK"
        elif action == 'append':
            with open(path, 'a', encoding='utf-8') as f: f.write(f"\n- {content}" if content else "")
            print_tool_result("logseq", "appended OK"); return "OK"
    except Exception as e:
        print_tool_result("logseq", f"ERROR: {e}"); return str(e)

def describe_image(image_path, question=None):
    """Usa el primer modelo vision disponible para describir una imagen."""
    print_tool_msg(f"Analyzing image: {image_path}…")
    # Find available local vision model
    vision_model = None
    try:
        local_models = [m.model for m in client.list().models]
        for m in local_models:
            if is_vision_model(m):
                vision_model = m
                break
    except Exception:
        pass

    if not vision_model:
        result = "No vision model installed. Install llava, moondream or similar with /pull llava"
        print_tool_result("describe_image", result)
        return result

    try:
        img_b64 = load_image_b64(image_path)
        prompt = question or "Describe this image in detail."
        resp = client.chat(
            model=vision_model,
            messages=[{'role': 'user', 'content': prompt, 'images': [img_b64]}],
            stream=False,
        )
        description = resp.message.content if hasattr(resp, 'message') else resp['message']['content']
        print_tool_result("describe_image", f"[{vision_model}] {description[:120]}")
        return description
    except Exception as e:
        result = f"Error analyzing image: {e}"
        print_tool_result("describe_image", result)
        return result

def ocr_image(image_path, lang=None):
    """Extrae texto de una imagen con OCR (tesseract)."""
    print_tool_msg(f"OCR: {image_path}…")
    lang = lang or "spa+eng"
    # Descargar si es URL
    local_path = image_path.strip().strip("'\"")
    tmp_file = None
    try:
        if local_path.startswith('http://') or local_path.startswith('https://'):
            import tempfile
            resp = requests.get(local_path, timeout=15)
            resp.raise_for_status()
            suffix = os.path.splitext(local_path)[1] or '.png'
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(resp.content); tmp.close()
            tmp_file = local_path = tmp.name
        else:
            local_path = os.path.expandvars(os.path.expanduser(local_path))

        # Intentar pytesseract primero
        try:
            import pytesseract
            from PIL import Image as PILImage
            img = PILImage.open(local_path)
            text = pytesseract.image_to_string(img, lang=lang)
            print_tool_result("ocr_image", text[:120] or "(no text found)")
            return text.strip() or "(No text detected)"
        except ImportError:
            pass

        # Fallback: tesseract CLI
        if shutil.which('tesseract'):
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                out_base = os.path.join(tmpdir, 'ocr_out')
                subprocess.run(
                    ['tesseract', local_path, out_base, '-l', lang],
                    capture_output=True, timeout=30
                )
                out_file = out_base + '.txt'
                if os.path.exists(out_file):
                    with open(out_file) as f: text = f.read()
                    print_tool_result("ocr_image", text[:120] or "(no text found)")
                    return text.strip() or "(No text detected)"

        result = ("OCR not available. Install tesseract:\n"
                  "  Linux: sudo apt install tesseract-ocr tesseract-ocr-spa\n"
                  "  macOS: brew install tesseract\n"
                  "  Python: pip install pytesseract pillow")
        print_tool_result("ocr_image", result)
        return result
    except Exception as e:
        result = f"OCR error: {e}"
        print_tool_result("ocr_image", result)
        return result
    finally:
        if tmp_file and os.path.exists(tmp_file):
            os.remove(tmp_file)

funcs = {
    'web_search': web_search,
    'execute_shell': execute_shell,
    'logseq_io': logseq_io,
    'get_system_status': get_system_status,
    'describe_image': describe_image,
    'ocr_image': ocr_image,
}

# ── HISTORY DE SESIONES ──────────────────────────────────────────────────────
def _serialize_msg(m):
    """Convert a message dict to a JSON-serializable form (ToolCall objects → dicts)."""
    out = {k: v for k, v in m.items() if k != 'tool_calls'}
    if 'tool_calls' in m and m['tool_calls']:
        out['tool_calls'] = [
            {'name': t.function.name, 'arguments': t.function.arguments}
            if hasattr(t, 'function') else t
            for t in m['tool_calls']
        ]
    return out

def save_session(msgs, session_id=None):
    """Save conversation to disk."""
    if not msgs or all(m['role'] == 'system' for m in msgs): return None
    if not session_id:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'id': session_id,
                'model': session.model,
                'date': datetime.now().isoformat(),
                'messages': [_serialize_msg(m) for m in msgs],
            }, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # never crash the chat due to save errors
    return session_id

def list_sessions():
    files = sorted(glob.glob(os.path.join(SESSIONS_DIR, "*.json")), reverse=True)
    sessions = []
    for f in files:
        try:
            d = json.loads(open(f).read())
            # Primer mensaje de usuario para el título
            first_user = next((m['content'][:60] for m in d.get('messages', []) if m['role'] == 'user'), "(vacío)")
            sessions.append({
                'id': d.get('id', os.path.basename(f)),
                'date': d.get('date', '')[:16].replace('T', ' '),
                'model': d.get('model', '?'),
                'preview': first_user,
                'path': f,
                'messages': d.get('messages', []),
            })
        except Exception: pass
    return sessions

def open_history():
    while True:
        sessions = list_sessions()
        if not sessions:
            clear_screen()
            print(get_banner())
            print(f"\n  {C('INFO')}No saved conversations.{C_RESET}\n")
            input(f"  {C('DIM')}[Enter]{C_RESET}")
            return None

        idx = 0
        while True:
            clear_screen()
            print(get_banner())
            print(f"  {C('ACCENT')}HISTORY{C_RESET}  {C('INFO')}[Enter] load  [d] delete  [ESC] exit{C_RESET}\n")
            for i, s in enumerate(sessions):
                marker = f"  {C('SEL')}>{C_RESET}" if i == idx else "   "
                print(f"{marker} {C('RESP')}{s['date']}{C_RESET}  {C('INFO')}{s['model']}{C_RESET}")
                print(f"     {C('DIM')}{s['preview']}{C_RESET}")
            # Opciones finales
            extras = ["── Delete all ──", "Back"]
            for j, ex in enumerate(extras):
                i = len(sessions) + j
                marker = f"  {C('SEL')}>{C_RESET}" if i == idx else "   "
                col = C('ERR') if 'Delete' in ex else C('DIM')
                print(f"{marker} {col}{ex}{C_RESET}")

            total = len(sessions) + len(extras)
            key = get_key()
            if key == '\x1b': return None
            elif key == '\x1b[A': idx = (idx - 1) % total
            elif key == '\x1b[B': idx = (idx + 1) % total
            elif key in ['\r', '\n', '\r\n']:
                if idx < len(sessions):
                    return sessions[idx]['messages']
                elif idx == len(sessions):  # Delete all
                    shutil.rmtree(SESSIONS_DIR)
                    os.makedirs(SESSIONS_DIR, exist_ok=True)
                    break
                else:
                    return None
            elif key in ['d', '\x7f'] and idx < len(sessions):
                os.remove(sessions[idx]['path'])
                break  # Recargar lista

# ── UI / INPUT ─────────────────────────────────────────────────────────────────
def get_key():
    if os.name == 'nt':
        ch = msvcrt.getch()
        if ch == b'\xe0':
            ch = msvcrt.getch()
            mapping = {b'H': 'A', b'P': 'B', b'M': 'C', b'K': 'D'}
            return f"\x1b[{mapping.get(ch, ' ')}"
        try: return ch.decode('utf-8')
        except: return ""
    else:
        import select
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = os.read(fd, 1).decode('utf-8', errors='replace')
            if ch == '\x1b':
                while True:
                    ready, _, _ = select.select([fd], [], [], 0.1)
                    if not ready:
                        break
                    c = os.read(fd, 1).decode('utf-8', errors='replace')
                    ch += c
                    if c.isalpha() or c == '~':
                        break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch

def interactive_menu(options, title, right_action=None, right_hint=None):
    idx = 0
    while True:
        clear_screen()
        print(get_banner())
        print(f"\n  {C('ACCENT')}{title}{C_RESET}\n")
        for i, opt in enumerate(options):
            if i == idx: print(f"  {C('SEL')}> {opt}{C_RESET}")
            else:        print(f"    {opt}")
        if right_hint:
            print(f"\n  {C('INFO')}[→] {right_hint}{C_RESET}")
        key = get_key()
        if   key == '\x1b[A':  idx = (idx - 1) % len(options)
        elif key == '\x1b[B':  idx = (idx + 1) % len(options)
        elif key in ['\r','\n','\r\n']: return options[idx]
        elif key == '\x1b[C' and right_action: right_action(idx)
        elif key == '\x1b': return None

# ── TOGGLE LIST (para /tools y /skills) ───────────────────────────────────────
def toggle_list_menu(title, items, state_dict, default_state=False, extra_top=None):
    """
    Menú de lista con toggle por ESPACIO.
    items: list of {"name": str, "description": str}
    state_dict: dict mutable name→bool
    extra_top: lista de opciones especiales al inicio (ej: "[Search skills]")
    """
    idx = 0
    all_options = (extra_top or []) + items
    n_extra = len(extra_top) if extra_top else 0

    while True:
        clear_screen()
        print(get_banner())
        print(f"\n  {C('ACCENT')}{title}{C_RESET}  {C('INFO')}[SPACE] toggle  [Enter] seleccionar  [ESC] exit{C_RESET}\n")

        for i, item in enumerate(all_options):
            is_extra = i < n_extra
            selected = (i == idx)
            marker = f"  {C('SEL')}>{C_RESET}" if selected else "   "

            if is_extra:
                name = item if isinstance(item, str) else item.get('name', str(item))
                print(f"{marker} {C('ACCENT')}{name}{C_RESET}")
            else:
                name = item['name']
                desc = item.get('description', '')
                enabled = state_dict.get(name, default_state)
                status_color = C('OK') if enabled else C('ERR')
                status_text  = " ON " if enabled else "OFF"
                print(f"{marker} [{status_color}{status_text}{C_RESET}]  {C('RESP')}{name}{C_RESET}  {C('DIM')}{desc}{C_RESET}")

        key = get_key()
        if key == '\x1b': break
        elif key == '\x1b[A': idx = (idx - 1) % len(all_options)
        elif key == '\x1b[B': idx = (idx + 1) % len(all_options)
        elif key == ' ':
            if idx >= n_extra:
                name = all_options[idx]['name']
                state_dict[name] = not state_dict.get(name, default_state)
                session.save_config()
        elif key in ['\r','\n','\r\n']:
            if idx < n_extra:
                return all_options[idx]  # retorna la opción especial seleccionada
            else:
                name = all_options[idx]['name']
                state_dict[name] = not state_dict.get(name, default_state)
                session.save_config()

# ── /TOOLS ────────────────────────────────────────────────────────────────────
def open_tools():
    items = [{'name': t['function']['name'], 'description': t['function']['description']} for t in ALL_TOOLS]
    toggle_list_menu("TOOLS", items, session.tools_enabled, default_state=True)

# ── /SKILLS ───────────────────────────────────────────────────────────────────
def open_skills():
    while True:
        catalog = load_skills_catalog()
        result = toggle_list_menu(
            "SKILLS",
            catalog,
            session.skills_enabled,
            default_state=False,
            extra_top=["[Search skills]"],
        )
        if result == "[Search skills]":
            clear_screen()
            print(get_banner())
            print(f"\n  {C('ACCENT')}SEARCH SKILLS{C_RESET}\n")
            q = input(f"  {C('INFO')}Search:{C_RESET} ").strip()
            if q:
                clear_screen()
                print(get_banner())
                print(f"\n  {C('DIM')}Searching skills for '{q}'…{C_RESET}\n")
                found = search_skills_online(q)
                if found:
                    # Guardar en catálogo extendido
                    existing = []
                    if os.path.exists(SKILLS_CATALOG):
                        try: existing = json.loads(open(SKILLS_CATALOG).read())
                        except: pass
                    names = {s['name'] for s in existing}
                    added = [s for s in found if s['name'] not in names]
                    existing += added
                    with open(SKILLS_CATALOG, 'w') as f: json.dump(existing, f, indent=2)
                    print(f"  {C('OK')}✓ {len(added)} skills added to catalog.{C_RESET}\n")
                else:
                    print(f"  {C('WARN')}No skills found.{C_RESET}\n")
                input(f"  {C('DIM')}[Enter]{C_RESET}")
        else:
            break

# ── MODEL SELECT / PULL / SEARCH ───────────────────────────────────────────────
def select_model():
    try:
        models = [m.model for m in client.list().models]
        if not models:
            print(f"\n  {C('WARN')}No models found. Use /search or /pull.{C_RESET}")
            input(f"  {C('DIM')}[Enter]{C_RESET}"); return None
        return interactive_menu(models, "SELECT MODEL")
    except Exception as e:
        print(f"\n  {C('ERR')}Error: {e}{C_RESET}"); return None

def pull_model(model_name):
    clear_screen()
    print(get_banner())
    print(f"\n  {C('ACCENT')}DOWNLOADING{C_RESET}  {C('INFO')}{model_name}{C_RESET}\n")
    try:
        bar_width = 40
        cur_status = ""; cur_digest = ""
        for progress in client.pull(model_name, stream=True):
            status    = getattr(progress, 'status', '') or ''
            completed = getattr(progress, 'completed', None)
            total     = getattr(progress, 'total', None)
            digest    = getattr(progress, 'digest', '') or ''
            if digest and digest != cur_digest:
                cur_digest = digest
                print(f"\n  {C('DIM')}{digest[:28]}…{C_RESET}")
            if status != cur_status:
                cur_status = status
                if status and not (completed and total):
                    print(f"  {C('DIM')}{status}{C_RESET}")
            if completed and total and total > 0:
                pct  = completed / total
                fill = int(bar_width * pct)
                bar  = "█" * fill + "░" * (bar_width - fill)
                mb_d = completed / 1_000_000; mb_t = total / 1_000_000
                print(f"\r  {C('THINK')}[{bar}]{C_RESET} {C('INFO')}{pct*100:.1f}% {mb_d:.1f}/{mb_t:.1f} MB{C_RESET}   ", end="", flush=True)
        print(f"\n\n  {C('OK')}✓ '{model_name}' downloaded.{C_RESET}")
    except Exception as e:
        print(f"\n  {C('ERR')}✗ Error: {e}{C_RESET}")
    print(); input(f"  {C('DIM')}[Enter]{C_RESET}")

def fetch_ollama_models(query=""):
    """Obtiene modelos de ollama.com/search parseando el HTML."""
    try:
        url = "https://ollama.com/search"
        params = {"q": query, "sort": "newest"} if query else {"sort": "newest"}
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            html = resp.text
            models = []
            # Extraer bloques de modelo del HTML
            # Patrón: href="/library/nombre" y datos asociados
            entries = re.findall(
                r'href="/library/([^"]+)"[^>]*>.*?'
                r'(?:<p[^>]*>([^<]{0,120})</p>)?'
                r'(?:.*?(\d+\.?\d*[BbMmKk](?:/\d+\.?\d*[BbMmKk])*))?',
                html, re.DOTALL
            )
            seen = set()
            for e in entries:
                name = e[0].strip().split('?')[0]
                if not name or name in seen or '/' in name: continue
                seen.add(name)
                desc = re.sub(r'\s+', ' ', e[1]).strip() if e[1] else ''
                params_str = e[2].strip() if e[2] else ''
                models.append({
                    "name": f"{name}:latest",
                    "description": desc,
                    "parameters": params_str,
                    "updated": "",
                })
            if models:
                return models
    except Exception:
        pass

    # Fallback estático con los modelos más populares
    return [
        {"name":"gemma3:latest",        "description":"Google Gemma 3",              "parameters":"2B/9B/27B",   "updated":"2025-04"},
        {"name":"llama3.3:latest",      "description":"Meta Llama 3.3",              "parameters":"70B",         "updated":"2025-01"},
        {"name":"qwq:latest",           "description":"Qwen QwQ reasoning",          "parameters":"32B",         "updated":"2025-01"},
        {"name":"deepseek-r1:latest",   "description":"DeepSeek R1 reasoning",       "parameters":"1.5B/7B/8B/14B/32B/70B/671B", "updated":"2025-01"},
        {"name":"phi4:latest",          "description":"Microsoft Phi-4",             "parameters":"14B",         "updated":"2025-01"},
        {"name":"phi4-mini:latest",     "description":"Microsoft Phi-4 Mini",        "parameters":"3.8B",        "updated":"2025-02"},
        {"name":"mistral:latest",       "description":"Mistral 7B v0.3",            "parameters":"7B",          "updated":"2024-06"},
        {"name":"mixtral:latest",       "description":"Mistral MoE",                "parameters":"8x7B/8x22B",  "updated":"2024-04"},
        {"name":"llama3.2:latest",      "description":"Meta Llama 3.2",             "parameters":"1B/3B",       "updated":"2024-09"},
        {"name":"llama3.1:latest",      "description":"Meta Llama 3.1",             "parameters":"8B/70B/405B", "updated":"2024-07"},
        {"name":"qwen2.5:latest",       "description":"Alibaba Qwen 2.5",           "parameters":"0.5B/1.5B/3B/7B/14B/32B/72B", "updated":"2024-09"},
        {"name":"qwen2.5-coder:latest", "description":"Qwen 2.5 Coder",            "parameters":"1.5B/7B/14B/32B", "updated":"2024-11"},
        {"name":"codellama:latest",     "description":"Meta Code Llama",            "parameters":"7B/13B/34B",  "updated":"2024-01"},
        {"name":"llava:latest",         "description":"LLaVA vision+language",       "parameters":"7B/13B/34B",  "updated":"2024-02"},
        {"name":"nomic-embed-text",     "description":"Text embeddings",             "parameters":"137M",        "updated":"2024-02"},
        {"name":"mxbai-embed-large",    "description":"MixedBread embeddings",       "parameters":"334M",        "updated":"2024-03"},
        {"name":"neural-chat:latest",   "description":"Intel Neural Chat",           "parameters":"7B",          "updated":"2024-01"},
        {"name":"starling-lm:latest",   "description":"Starling LM",                "parameters":"7B",          "updated":"2024-01"},
        {"name":"vicuna:latest",        "description":"Vicuna UC Berkeley",          "parameters":"7B/13B",      "updated":"2023-12"},
        {"name":"orca-mini:latest",     "description":"Orca Mini",                  "parameters":"3B/7B/13B",   "updated":"2023-11"},
    ]

def fetch_model_tags(base_name):
    """Fetch available tags for a model from ollama.com/library/{name}/tags"""
    try:
        url = f"https://ollama.com/library/{base_name}/tags"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code == 200:
            found = re.findall(r'href="/library/' + re.escape(base_name) + r':([^"]+)"', resp.text)
            seen = set()
            tags = []
            for t in found:
                t = t.strip()
                if t and t not in seen:
                    seen.add(t)
                    tags.append(f"{base_name}:{t}")
            if tags:
                return tags
    except Exception:
        pass
    return [f"{base_name}:latest"]

def show_model_detail(model_info):
    name   = model_info.get('name', str(model_info))
    desc   = model_info.get('description', '')
    params = model_info.get('parameters', 'N/A')
    upd    = model_info.get('updated', 'N/A')
    base_name = name.split(':')[0]

    # Fetch real tags from ollama.com
    tags = None
    clear_screen(); print(get_banner())
    print(f"\n  {C('DIM')}Loading variants for {base_name}…{C_RESET}", flush=True)
    tags = fetch_model_tags(base_name)

    # Menú de variantes con info del modelo arriba
    idx = 0
    while True:
        clear_screen(); print(get_banner())
        print(f"\n  {C('ACCENT')}DETAILS{C_RESET}  {C('DIM')}{base_name}{C_RESET}\n")
        print(f"  {C('RESP')}Description:{C_RESET} {desc}")
        print(f"  {C('RESP')}Parameters:{C_RESET}  {params}")
        print(f"  {C('RESP')}Updated:{C_RESET} {upd}")
        print(f"\n  {C('INFO')}Available variants:{C_RESET}  {C('DIM')}[↑↓] navigate  [Enter] download  [ESC] back{C_RESET}\n")
        for i, tag in enumerate(tags):
            if i == idx:
                print(f"  {C('SEL')}> {tag}{C_RESET}")
            else:
                print(f"    {C('INFO')}{tag}{C_RESET}")

        key = get_key()
        if key == '\x1b': break
        elif key == '\x1b[A': idx = (idx - 1) % len(tags)
        elif key == '\x1b[B': idx = (idx + 1) % len(tags)
        elif key in ['\r','\n','\r\n']:
            pull_model(tags[idx])
            break

def search_models():
    query = ""; models = []; loading = True
    idx = 0
    while True:
        if loading:
            clear_screen(); print(get_banner())
            print(f"\n  {C('DIM')}Loading…{C_RESET}", flush=True)
            models = fetch_ollama_models(query)
            loading = False

        clear_screen(); print(get_banner())
        print(f"\n  {C('ACCENT')}SEARCH MODELS{C_RESET}  {C('DIM')}newest → oldest{C_RESET}")
        print(f"  {C('DIM')}search:{C_RESET} {C('RESP')}{query or '(all)'}{C_RESET}")
        print(f"  {C('INFO')}[↑↓] navigate  [→] details  [Enter] download  [n] new search  [ESC] exit{C_RESET}\n")

        if not models:
            print(f"  {C('WARN')}No models found.{C_RESET}")
        else:
            for i, m in enumerate(models):
                name = m.get('name', str(m)) if isinstance(m, dict) else str(m)
                desc = (m.get('description', '') if isinstance(m, dict) else '')[:60]
                upd  = m.get('updated', '') if isinstance(m, dict) else ''
                if i == idx:
                    print(f"  {C('SEL')}> {name}{C_RESET}  {C('DIM')}{desc}{C_RESET}  {C('INFO')}{upd}{C_RESET}")
                else:
                    print(f"    {C('INFO')}{name}{C_RESET}  {C('DIM')}{desc}{C_RESET}")

        key = get_key()
        if key == '\x1b': break
        elif key == '\x1b[A' and models: idx = (idx - 1) % len(models)
        elif key == '\x1b[B' and models: idx = (idx + 1) % len(models)
        elif key == '\x1b[C' and models:
            m = models[idx]
            show_model_detail(m if isinstance(m, dict) else {"name": str(m)})
        elif key in ['\r','\n','\r\n'] and models:
            m = models[idx]
            pull_model(m.get('name', str(m)) if isinstance(m, dict) else str(m))
        elif key == 'n':
            clear_screen(); print(get_banner())
            query = input(f"\n  {C('INFO')}Search:{C_RESET} ").strip()
            idx = 0; loading = True

# ── SETTINGS ───────────────────────────────────────────────────────────────────
def open_settings():
    while True:
        opts = [
            f"Model:    {session.model}",
            f"Thinking: {session.thinking_mode}",
            f"Level:    {session.thinking_level}",
            f"Theme:    {session.theme}",
            "Pull model…",
            "Search models…",
            "Chats…",
            "Back",
        ]
        opt = interactive_menu(opts, "SETTINGS")
        if not opt or "Back" in opt: break
        if "Model"    in opt:
            new = select_model()
            if new: session.model = new; session.save_config()
        elif "Thinking" in opt:
            mode = interactive_menu(["OFF","ON","FORCE"], "THINKING MODE")
            if mode: session.thinking_mode = mode; session.save_config()
        elif "Level"   in opt:
            lv = interactive_menu(["Low","Medium","High"], "THINKING LEVEL")
            if lv: session.thinking_level = lv; session.save_config()
        elif "Theme"   in opt:
            th = interactive_menu(list(THEMES.keys()), "THEME")
            if th: session.theme = th; session.save_config()
        elif "Pull"    in opt:
            clear_screen(); print(get_banner())
            name = input(f"\n  {C('INFO')}Model name:{C_RESET} ").strip()
            if name: pull_model(name)
        elif "Search" in opt:
            search_models()
        elif "Chats"   in opt:
            open_history_settings()

def open_history_settings():
    """Manage chats from Settings."""
    while True:
        sessions_list = list_sessions()
        if not sessions_list:
            clear_screen(); print(get_banner())
            print(f"\n  {C('INFO')}No saved conversations.{C_RESET}\n")
            input(f"  {C('DIM')}[Enter]{C_RESET}"); return

        opts = [f"{s['date']}  {s['model']}  {s['preview']}" for s in sessions_list]
        opts += ["── Delete all ──", "Back"]
        choice = interactive_menu(opts, "CHATS  [Enter=open/delete]")
        if not choice or "Back" in choice: break
        if "Delete all" in choice:
            shutil.rmtree(SESSIONS_DIR); os.makedirs(SESSIONS_DIR, exist_ok=True)
            break
        # Find session and offer to delete
        for s in sessions_list:
            label = f"{s['date']}  {s['model']}  {s['preview']}"
            if choice == label:
                action = interactive_menu(["View preview", "Delete this chat", "Back"], f"CHAT: {s['date']}")
                if action == "Delete this chat":
                    os.remove(s['path'])
                break

# ── SYSTEM PROMPT ──────────────────────────────────────────────────────────────
def get_system_prompt():
    active_tool_names = [t['function']['name'] for t in get_active_tools()]
    tools_str = ", ".join(active_tool_names) if active_tool_names else "none"
    base = f"You are a Rainbow Technology Assistant. Active tools: {tools_str}."
    thinking = {
        "OFF":   "Respond directly without tags.",
        "ON":    "Use <thought>...</thought> tags to reason BEFORE responding.",
        "FORCE": "MANDATORY: Use <thought>...</thought> for extensive reasoning BEFORE using tools.",
    }[session.thinking_mode]
    skill_prompt = get_active_skill_prompt()
    return f"{base}\n{thinking}\nAll reasoning goes inside <thought>.{skill_prompt}"

# ── STREAMING MEJORADO ─────────────────────────────────────────────────────────
def stream_response(response_iter, show_thinking=True):
    full_text = ""
    in_thought = False
    thought_shown = False
    response_shown = False
    buf = ""

    for chunk in response_iter:
        content = chunk['message'].content
        if not content: continue
        buf += content
        full_text += content

        # Procesar buffer buscando tags
        while True:
            if not in_thought:
                ts = buf.find("<thought>")
                if ts != -1:
                    before = buf[:ts]
                    if before:
                        if not response_shown:
                            print(f"\n  {C('RESP')}── Response ────────────────────────────{C_RESET}\n  ", end="", flush=True)
                            response_shown = True
                        print(f"{C('RESP')}{before}{C_RESET}", end="", flush=True)
                    if not thought_shown and show_thinking:
                        print(f"\n  {C('THINK_L')}── Thinking ────────────────────────────{C_RESET}\n  {C('THINK')}", end="", flush=True)
                        thought_shown = True
                    in_thought = True
                    buf = buf[ts + len("<thought>"):]
                else:
                    break
            else:
                te = buf.find("</thought>")
                if te != -1:
                    if buf[:te]:
                        print(f"{C('THINK')}{buf[:te]}{C_RESET}", end="", flush=True)
                    print(f"\n  {C('DIM')}───────────────────────────────────────{C_RESET}", end="", flush=True)
                    in_thought = False
                    buf = buf[te + len("</thought>"):]
                    if not response_shown:
                        print(f"\n  {C('RESP')}── Response ────────────────────────────{C_RESET}\n  ", end="", flush=True)
                        response_shown = True
                else:
                    break

        # Imprimir parte segura del buffer
        safe = len(buf)
        lt = buf.rfind('<')
        if lt != -1 and lt > len(buf) - 12: safe = lt
        to_print = buf[:safe]; buf = buf[safe:]

        if to_print:
            if in_thought:
                if not thought_shown and show_thinking:
                    print(f"\n  {C('THINK_L')}── Thinking ────────────────────────────{C_RESET}\n  {C('THINK')}", end="", flush=True)
                    thought_shown = True
                print(f"{C('THINK')}{to_print}{C_RESET}", end="", flush=True)
            else:
                if not response_shown and not thought_shown:
                    if show_thinking and session.thinking_mode != "OFF":
                        print(f"\n  {C('THINK_L')}── Thinking ────────────────────────────{C_RESET}\n  {C('THINK')}", end="", flush=True)
                        thought_shown = True; in_thought = True
                        print(f"{C('THINK')}{to_print}{C_RESET}", end="", flush=True)
                    else:
                        print(f"\n  {C('RESP')}── Response ────────────────────────────{C_RESET}\n  ", end="", flush=True)
                        response_shown = True
                        print(f"{C('RESP')}{to_print}{C_RESET}", end="", flush=True)
                else:
                    color = C('THINK') if in_thought else C('RESP')
                    print(f"{color}{to_print}{C_RESET}", end="", flush=True)

    if buf:
        color = C('THINK') if in_thought else C('RESP')
        print(f"{color}{buf}{C_RESET}", end="", flush=True)

    print(f"\n  {C('DIM')}───────────────────────────────────────{C_RESET}\n")
    return full_text

# ── STATUS BAR ────────────────────────────────────────────────────────────────
def print_status():
    active_t = sum(1 for v in session.tools_enabled.values() if v)
    active_s = sum(1 for v in session.skills_enabled.values() if v)
    skills_str = f"  {C('ACCENT')}skills:{active_s}{C_RESET}" if active_s else ""
    vision_str = f"  {C('OK')}👁 vision{C_RESET}" if is_vision_model(session.model) else ""
    print(f"  {C('INFO')}{session.model}  thinking:{session.thinking_mode}  tools:{active_t}/{len(session.tools_enabled)}{skills_str}  theme:{session.theme}{vision_str}{C_RESET}")
    img_hint = f" /img <ruta|url>" if is_vision_model(session.model) else ""
    print(f"  {C('DIM')}Commands: /exit /settings /tools /skills /search /pull <m> /history{img_hint}{C_RESET}\n")

# ── CHAT ───────────────────────────────────────────────────────────────────────
# ── VISION ────────────────────────────────────────────────────────────────────
VISION_KEYWORDS = ['llava', 'bakllava', 'moondream', 'vision', 'minicpm-v',
                   'llama3.2-vision', 'gemma3', 'qwen2-vl', 'cogvlm', 'phi3-vision',
                   'pixtral', 'idefics', 'internvl', 'deepseek-vl']

def is_vision_model(model_name):
    name = model_name.lower()
    return any(k in name for k in VISION_KEYWORDS)

def load_image_b64(path):
    """Carga una imagen desde ruta o URL y devuelve base64."""
    path = path.strip().strip('"').strip("'")
    # URL
    if path.startswith('http://') or path.startswith('https://'):
        resp = requests.get(path, timeout=15)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode()
    # Ruta local — expandir ~ y variables
    path = os.path.expandvars(os.path.expanduser(path))
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró: {path}")
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

IMG_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif', '.avif')

def parse_image_input(inp):
    """
    Detecta si el input contiene una imagen. Formatos:
      /img <ruta|url> [texto]     — comando explícito
      /image <ruta|url> [texto]   — alias
      <ruta_imagen>               — arrastrar archivo al terminal (ruta suelta)
      <ruta_imagen> <texto>       — ruta + pregunta
      file://<ruta>               — prefijo file:// que algunos terminales añaden
    Devuelve (texto, ruta) o (inp, None).
    """
    IMG_EXTS_SET = set(IMG_EXTS)

    # 1. Comando explícito /img o /image
    for prefix in ('/img ', '/image '):
        if inp.lower().startswith(prefix):
            rest = inp[len(prefix):].strip()
            parts = rest.split(' ', 1)
            return (parts[1] if len(parts) > 1 else "Describe esta imagen."), parts[0]

    # 2. Prefijo file:// (drag desde algunos file managers)
    clean = inp.strip().strip("'\"")
    if clean.startswith('file://'):
        from urllib.parse import unquote
        path = unquote(clean[7:])
        if os.path.splitext(path)[1].lower() in IMG_EXTS_SET:
            return "Describe esta imagen.", path

    # 3. Ruta suelta — puede tener texto después
    #    Find the first "palabra" que sea un path de imagen existente
    #    (cubre rutas con espacios escapados que el terminal pega con \ )
    unescaped = clean.replace('\\ ', ' ')
    # Intentar el input completo primero, luego la primera "palabra"
    candidates = [unescaped]
    if ' ' in unescaped:
        # primera parte podría ser ruta, resto texto
        # recorre de derecha a izquierda buscando extensión de imagen
        for i in range(len(unescaped), 0, -1):
            part = unescaped[:i]
            if os.path.splitext(part)[1].lower() in IMG_EXTS_SET:
                candidates.insert(0, part)
                break

    for cand in candidates:
        cand_exp = os.path.expandvars(os.path.expanduser(cand))
        if os.path.splitext(cand_exp)[1].lower() in IMG_EXTS_SET and os.path.exists(cand_exp):
            text_after = unescaped[len(cand):].strip()
            return (text_after if text_after else "Describe esta imagen."), cand_exp

    return inp, None

def chat(preloaded_msgs=None):
    clear_screen(); print(get_banner()); print_status()
    msgs = list(preloaded_msgs) if preloaded_msgs else []
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    show_thinking = session.thinking_mode != "OFF"
    _last_ctrl_c = 0.0  # timestamp of last Ctrl+C

    while True:
        try:
            sys_msg = {"role": "system", "content": get_system_prompt()}
            if not msgs or msgs[0]['role'] != 'system': msgs.insert(0, sys_msg)
            else: msgs[0] = sys_msg

            inp = input(f"\n  {C('ACCENT')}[XYZ]{C_RESET} {C('DIM')}>{C_RESET} ").strip()
            if not inp: continue

            # Ctrl+Q → exit immediately (sent as \x11 by most terminals)
            if inp == '\x11':
                break

            # ── Comandos ──
            if inp.lower() == '/exit': break
            if inp.lower() == '/settings':
                open_settings(); show_thinking = session.thinking_mode != "OFF"
                clear_screen(); print(get_banner()); print_status(); continue
            if inp.lower() == '/tools':
                open_tools()
                clear_screen(); print(get_banner()); print_status(); continue
            if inp.lower() == '/skills':
                open_skills()
                clear_screen(); print(get_banner()); print_status(); continue
            if inp.lower() == '/search':
                search_models(); clear_screen(); print(get_banner()); print_status(); continue
            if inp.lower().startswith('/pull '):
                name = inp[6:].strip()
                if name: pull_model(name)
                else: print(f"  {C('WARN')}Usage: /pull <model>{C_RESET}")
                continue
            if inp.lower() == '/history':
                loaded = open_history()
                if loaded:
                    msgs = loaded
                    print(f"\n  {C('OK')}✓ Conversation loaded ({len([m for m in msgs if m['role']=='user'])} messages){C_RESET}\n")
                clear_screen(); print(get_banner()); print_status(); continue

            # ── Imagen ──
            text, img_path = parse_image_input(inp)
            img_b64 = None
            if img_path:
                if is_vision_model(session.model):
                    # Modelo vision nativo: cargar imagen en base64
                    try:
                        print(f"  {C('DIM')}Loading image…{C_RESET}", end="", flush=True)
                        img_b64 = load_image_b64(img_path)
                        print(f"\r  {C('OK')}✓ Image loaded ({len(img_b64)//1024}KB){C_RESET}\n")
                        inp = text
                    except Exception as e:
                        print(f"\r  {C('ERR')}✗ Could not load image: {e}{C_RESET}\n")
                        continue
                else:
                    # Modelo sin vision: redirigir a tool describe_image/ocr_image
                    tool_enabled_names = [t['function']['name'] for t in get_active_tools()]
                    if 'describe_image' in tool_enabled_names or 'ocr_image' in tool_enabled_names:
                        print(f"  {C('INFO')}Non-vision model — using tools to analyze image…{C_RESET}\n")
                        # Inyectar la ruta en el mensaje para que el modelo llame la tool
                        inp = f"{text}\nImage to analyze: {img_path}"
                        img_path = None  # no enviar como imagen nativa
                    else:
                        print(f"\n  {C('WARN')}⚠ Non-vision model and describe_image/ocr_image tools are disabled.")
                        print(f"  {C('DIM')}Enable tools in /tools or use a vision model.{C_RESET}\n")
                        continue

            # Guard: modelo seleccionado
            if not session.model:
                print(f"\n  {C('ERR')}✗ No model selected. Use /settings to choose one.{C_RESET}")
                continue

            # Construir mensaje de usuario
            if img_b64:
                user_msg = {'role': 'user', 'content': inp, 'images': [img_b64]}
            else:
                user_msg = {'role': 'user', 'content': inp}
            msgs.append(user_msg)

            # ── Llamada al modelo ──
            active_tools = get_active_tools()
            # Los modelos vision no suelen soportar tools simultáneamente
            use_tools = active_tools if (active_tools and not img_b64) else None
            try:
                response = client.chat(
                    model=session.model,
                    messages=msgs,
                    tools=use_tools,
                    stream=True,
                )
                full_content = stream_response(response, show_thinking=show_thinking)
            except Exception as e:
                msgs.pop()  # quitar el mensaje del usuario que falló
                print(f"\n  {C('ERR')}✗ Error communicating with model: {e}{C_RESET}")
                if 'model' in str(e).lower() or 'not found' in str(e).lower():
                    print(f"  {C('WARN')}Model '{session.model}' may not be available. Use /settings to change it.{C_RESET}")
                elif 'connect' in str(e).lower() or 'refused' in str(e).lower():
                    print(f"  {C('WARN')}Cannot connect to Ollama. Is it running?{C_RESET}")
                continue

            ast_msg = {'role': 'assistant', 'content': full_content}
            msgs.append(ast_msg)

            # ── Tool calls: siempre verificar cuando hay tools activas ──
            # El stream no expone tool_calls chunk a chunk — hay que re-invocar sin stream
            if active_tools and not img_b64:
                try:
                    r2 = client.chat(model=session.model, messages=msgs[:-1], tools=active_tools, stream=False)
                    m2 = r2.message if hasattr(r2, 'message') else r2['message']
                    if hasattr(m2, 'tool_calls') and m2.tool_calls:
                        tools_called = list(m2.tool_calls)
                        msgs[-1]['content'] = m2.content or full_content
                        msgs[-1]['tool_calls'] = tools_called

                        print(f"\n  {C('DIM')}── Executing tools ────────────────────{C_RESET}")
                        for t in tools_called:
                            f = funcs.get(t.function.name)
                            if f:
                                try:
                                    res = f(**t.function.arguments)
                                except Exception as te:
                                    res = f"Error in tool {t.function.name}: {te}"
                                    print(f"\n  {C('ERR')}✗ {res}{C_RESET}")
                                msgs.append({'role': 'tool', 'content': str(res), 'name': t.function.name})
                            else:
                                print(f"\n  {C('WARN')}⚠ Unknown tool: {t.function.name}{C_RESET}")

                        final = client.chat(model=session.model, messages=msgs, stream=True)
                        final_text = stream_response(final, show_thinking=show_thinking)
                        msgs.append({'role': 'assistant', 'content': final_text})
                except Exception as e:
                    print(f"\n  {C('ERR')}✗ Error processing tool calls: {e}{C_RESET}")

            # Autoguardado
            save_session(msgs, session_id)

        except KeyboardInterrupt:
            import time
            now = time.time()
            if now - _last_ctrl_c < 2.0:
                # Double Ctrl+C within 2 seconds → exit
                save_session(msgs, session_id)
                print(f"\n  {C('DIM')}Bye.{C_RESET}\n")
                break
            _last_ctrl_c = now
            print(f"\n  {C('DIM')}Ctrl+C again or Ctrl+Q to quit.{C_RESET}")
        except Exception as e:
            print(f"\n  {C('ERR')}✗ Unexpected error: {e}{C_RESET}")

    save_session(msgs, session_id)

# ── OLLAMA SERVE AUTO-START ────────────────────────────────────────────────────
_ollama_proc = None  # proceso ollama serve lanzado por nosotros

def _get_ollama_install_hint():
    """Instrucciones de instalación según el SO."""
    if sys.platform == 'win32':
        return "Download at: https://ollama.com/download/windows"
    elif sys.platform == 'darwin':
        return "Install it with: brew install ollama  o  https://ollama.com/download/mac"
    else:
        return "Install it with: curl -fsSL https://ollama.com/install.sh | sh"

def ensure_ollama_running():
    """Comprueba si ollama está corriendo; si no, lo arranca en segundo plano."""
    global _ollama_proc
    import time

    # 1. Intentar conectar
    try:
        client.list()
        return True
    except Exception:
        pass

    # 2. Comprobar si el binario existe
    if not shutil.which('ollama'):
        clear_screen(); print(get_banner())
        print(f"\n  {C('ERR')}✗ Ollama is not installed.{C_RESET}")
        print(f"  {C('INFO')}{_get_ollama_install_hint()}{C_RESET}")
        print(f"  {C('DIM')}Or run the installer:{C_RESET}  ./install.sh\n")
        input(f"  {C('DIM')}[Enter to exit]{C_RESET}")
        return False

    # 3. Arrancarlo en segundo plano
    clear_screen(); print(get_banner())
    print(f"\n  {C('WARN')}Ollama is not running. Starting in background…{C_RESET}\n")
    try:
        kwargs = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if sys.platform == 'win32':
            # Windows: sin consola nueva visible
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        else:
            kwargs['start_new_session'] = True
        _ollama_proc = subprocess.Popen(['ollama', 'serve'], **kwargs)
    except Exception as e:
        print(f"  {C('ERR')}✗ Could not start ollama serve: {e}{C_RESET}\n")
        input(f"  {C('DIM')}[Enter]{C_RESET}")
        return False

    # 4. Esperar hasta que responda (máx 15s)
    bar_width = 30
    for i in range(30):
        time.sleep(0.5)
        filled = int(bar_width * (i + 1) / 30)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"\r  {C('THINK')}[{bar}]{C_RESET} {C('DIM')}waiting for ollama…{C_RESET}  ", end="", flush=True)
        try:
            client.list()
            print(f"\n\n  {C('OK')}✓ Ollama ready.{C_RESET}\n")
            return True
        except Exception:
            pass

    print(f"\n\n  {C('ERR')}✗ Ollama did not respond. Try manually: ollama serve{C_RESET}\n")
    input(f"  {C('DIM')}[Enter]{C_RESET}")
    return False

def stop_ollama_if_we_started():
    """Si nosotros arrancamos ollama serve, lo detenemos al exit."""
    global _ollama_proc
    if _ollama_proc and _ollama_proc.poll() is None:
        _ollama_proc.terminate()
        _ollama_proc = None

# ── ENTRY POINT ────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) >= 3 and sys.argv[1].lower() == 'pull':
        if not ensure_ollama_running(): return
        pull_model(sys.argv[2]); return
    if len(sys.argv) >= 2 and sys.argv[1].lower() == 'search':
        search_models(); return

    if not ensure_ollama_running():
        return

    try:
        if not session.model:
            session.model = select_model() or ""
            if not session.model: return
            session.save_config()
        else:
            try:
                available = [m.model for m in client.list().models]
                if session.model not in available:
                    session.model = select_model() or ""
                    if not session.model: return
                    session.save_config()
            except Exception:
                session.model = select_model() or ""
                if not session.model: return

        chat()
    finally:
        stop_ollama_if_we_started()

if __name__ == "__main__":
    main()
