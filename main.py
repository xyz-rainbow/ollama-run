#!/usr/bin/env python3
# Rainbow Ollama-Run
# © Rainbow Technology
# #xyz-rainbow #xyz-rainbowtechnology #rainbow.xyz #rainbow@rainbowtechnology.xyz
# #i-love-you #You're not supposed to see this!
# Personal use only. Redistribution, forks and commercial use prohibited.

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
import hashlib
import mimetypes
import locale
from datetime import datetime
from ollama import Client
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

# ── I18N / LANGUAGES ───────────────────────────────────────────────────────────
# #xyz-rainbowtechnology #rainbow.xyz
STRINGS = {
    "en": {
        "thinking": "Thinking",
        "response": "Response",
        "tools": "tools",
        "skills": "skills",
        "theme": "theme",
        "model": "model",
        "status": "status",
        "vision": "vision",
        "exit": "exit",
        "settings": "settings",
        "history": "history",
        "search": "search",
        "pull": "pull",
        "loading": "Loading...",
        "no_models": "No models found. Use /search or /pull.",
        "select_model": "SELECT MODEL",
        "downloading": "DOWNLOADING",
        "ready": "ready",
        "error_ollama": "Ollama is not installed or not running.",
        "ctrl_q_hint": "Ctrl+C again or Ctrl+Q to quit.",
    },
    "es": {
        "thinking": "Pensamiento",
        "response": "Respuesta",
        "tools": "herramientas",
        "skills": "skills",
        "theme": "tema",
        "model": "modelo",
        "status": "estado",
        "vision": "visión",
        "exit": "salir",
        "settings": "ajustes",
        "history": "historial",
        "search": "buscar",
        "pull": "descargar",
        "loading": "Cargando...",
        "no_models": "No se encontraron modelos. Usa /search o /pull.",
        "select_model": "SELECCIONAR MODELO",
        "downloading": "DESCARGANDO",
        "ready": "listo",
        "error_ollama": "Ollama no está instalado o no está iniciado.",
        "ctrl_q_hint": "Ctrl+C de nuevo o Ctrl+Q para salir.",
    }
}

def get_system_lang():
    """Get system language, fallback to English."""
    try:
        lang = locale.getdefaultlocale()[0]
        if lang and lang.startswith('es'):
            return "es"
    except Exception:
        pass
    return "en"

CURRENT_LANG = get_system_lang()

def T(key):
    """Translate key based on current language."""
    return STRINGS.get(CURRENT_LANG, STRINGS["en"]).get(key, key)

# ── AUTHORSHIP ─────────────────────────────────────────────────────────────────
# #xyz-rainbowtechnology #rainbow.xyz
_AUTHOR          = "xyz-rainbow"
_PROJECT         = "ollama-run"
_ORG             = "Rainbow Technology"
_DOMAIN          = "rainbowtechnology.xyz"
_HANDLE          = "xyz-rainbowtechnology"
_SIG_B64         = b"eHl6LXJhaW5ib3d8b2xsYW1hLXJ1bnxSYWluYm93IFRlY2hub2xvZ3l8cmFpbmJvd3RlY2hub2xvZ3kueHl6"
_SIG_SHA256      = "ed16048676de7958e429aff7174edcd4754c9abf044108febef29edec95ae3f5"
_BUILD_TAG       = "rnbw-ollama-4.9.1-20250329"
_LICENSE_URI     = "https://rainbowtechnology.xyz/license/ollama-run"

def get_base_dir():
    """Calculate the data directory based on OS conventions."""
    # #i-love-you
    if os.name == 'nt':
        # Windows: %APPDATA%\ollama-run
        return os.path.join(os.environ.get('APPDATA', os.path.expanduser("~")), "ollama-run")
    elif sys.platform == 'darwin':
        # macOS: ~/Library/Application Support/ollama-run
        return os.path.expanduser("~/Library/Application Support/ollama-run")
    else:
        # Linux: Respect XDG_CONFIG_HOME or fallback to ~/.config/ollama-run
        xdg_config = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser("~/.config"))
        return os.path.join(xdg_config, "ollama-run")

CORE_ID        = "rainbow-tech-v4.9.1-full"
XYZ_DIR        = get_base_dir()
SESSIONS_DIR   = os.path.join(XYZ_DIR, "sessions")
CONFIG_FILE    = os.path.join(XYZ_DIR, "config.json")
SKILLS_CATALOG = os.path.join(XYZ_DIR, "skills_catalog.json")
HISTORY_FILE   = os.path.join(XYZ_DIR, "input_history")

# Ensure base directories exist
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

if os.name == 'nt':
    import msvcrt
else:
    import termios
    import tty

# Readline: Tab autocompletes commands starting with /
COMMANDS = ['/exit', '/e', '/settings', '/st', '/model', '/m', '/tools', '/t',
            '/skills', '/sk', '/search', '/sr', '/history', '/h',
            '/pull ', '/p ', '/img ', '/i ']

def _cmd_completer(text, state):
    if text.startswith('/'):
        matches = [c for c in COMMANDS if c.startswith(text)]
        return matches[state] if state < len(matches) else None
    return None

try:
    import readline
    readline.set_completer(_cmd_completer)
    readline.set_completer_delims('')
    readline.parse_and_bind('tab: complete')
    try:
        readline.read_history_file(HISTORY_FILE)
    except FileNotFoundError:
        pass
    readline.set_history_length(500)
except ImportError:
    pass

LOGSEQ_PATH = os.path.expanduser("~/Documents/Logseq/pages")
if os.path.exists("/media/cloud-xyz/X/[Graph]/pages"):
    LOGSEQ_PATH = "/media/cloud-xyz/X/[Graph]/pages"

client = Client()

# ── COLORES POR TEMA ───────────────────────────────────────────────────────────
THEMES = {
    # default: thinking=cyan  response=green  tool=yellow
    "default": dict(
        THINK_L="\033[1;96m",  THINK="\033[0;96m",   RESP="\033[0;92m",
        TOOL="\033[1;33m",     TOOL_R="\033[0;33m",  INFO="\033[0;90m",
        ACCENT="\033[1;96m",   SEL="\033[1;32m",     WARN="\033[1;33m",
        OK="\033[1;32m",       ERR="\033[1;31m",     DIM="\033[2m",
    ),
    # matrix: thinking=dim green  response=bright green  tool=bold white
    "matrix": dict(
        THINK_L="\033[1;32m",  THINK="\033[2;32m",   RESP="\033[1;92m",
        TOOL="\033[1;37m",     TOOL_R="\033[0;37m",  INFO="\033[2;32m",
        ACCENT="\033[1;32m",   SEL="\033[1;92m",     WARN="\033[0;33m",
        OK="\033[1;32m",       ERR="\033[0;31m",     DIM="\033[2m",
    ),
    # dracula: thinking=purple  response=pink/magenta  tool=yellow
    "dracula": dict(
        THINK_L="\033[1;35m",  THINK="\033[0;35m",   RESP="\033[1;95m",
        TOOL="\033[1;33m",     TOOL_R="\033[0;33m",  INFO="\033[0;90m",
        ACCENT="\033[1;35m",   SEL="\033[1;95m",     WARN="\033[1;33m",
        OK="\033[1;32m",       ERR="\033[1;31m",     DIM="\033[2m",
    ),
    # amber: thinking=dim orange  response=bright yellow  tool=cyan
    "amber": dict(
        THINK_L="\033[1;33m",  THINK="\033[2;33m",   RESP="\033[1;93m",
        TOOL="\033[0;96m",     TOOL_R="\033[2;96m",  INFO="\033[2;33m",
        ACCENT="\033[1;33m",   SEL="\033[1;93m",     WARN="\033[1;31m",
        OK="\033[1;33m",       ERR="\033[1;31m",     DIM="\033[2m",
    ),
    # mono: thinking=dim  response=normal  tool=bold+underline
    "mono": dict(
        THINK_L="\033[1m",     THINK="\033[2m",      RESP="\033[0m",
        TOOL="\033[1;4m",      TOOL_R="\033[2m",     INFO="\033[2m",
        ACCENT="\033[1m",      SEL="\033[1m",        WARN="\033[1m",
        OK="\033[1m",          ERR="\033[7m",        DIM="\033[2m",
    ),
}
C_RESET = "\033[0m"
# 78797a2d7261696e626f77 | theme registry © rnbw

# ── SESIÓN ─────────────────────────────────────────────────────────────────────
class Session:
    def __init__(self):
        # #rainbow@rainbowtechnology.xyz #i-love-you
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
        self._uid = "eHl6LXJhaW5ib3c="  # session origin tag
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
# #xyz-rainbow
DEFAULT_TOOLS = [
    {'type':'function','function':{'name':'web_search','description':'Web search via DuckDuckGo.','parameters':{'type':'object','properties':{'query':{'type':'string'}},'required':['query']}}},
    {'type':'function','function':{'name':'execute_shell','description':'Execute Bash commands.','parameters':{'type':'object','properties':{'command':{'type':'string'}},'required':['command']}}},
    {'type':'function','function':{'name':'logseq_io','description':'Read/write Logseq pages.','parameters':{'type':'object','properties':{'action':{'type':'string','enum':['read','write','append']},'page_name':{'type':'string'},'content':{'type':'string'}},'required':['action','page_name']}}},
    {'type':'function','function':{'name':'get_system_status','description':'CPU, RAM, disk and process info.','parameters':{'type':'object','properties':{}}}},
    {'type':'function','function':{'name':'describe_image','description':'Describe image content using a vision model.','parameters':{'type':'object','properties':{'image_path':{'type':'string'},'question':{'type':'string'}},'required':['image_path']}}},
    {'type':'function','function':{'name':'ocr_image','description':'Extract text from image via OCR.','parameters':{'type':'object','properties':{'image_path':{'type':'string'},'lang':{'type':'string'}},'required':['image_path']}}},
]
DEFAULT_TOOL_NAMES = {t['function']['name'] for t in DEFAULT_TOOLS}
CUSTOM_TOOLS_FILE  = os.path.join(XYZ_DIR, 'custom_tools.json')

def load_custom_tools():
    if os.path.exists(CUSTOM_TOOLS_FILE):
        try:
            with open(CUSTOM_TOOLS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_custom_tools(tools):
    with open(CUSTOM_TOOLS_FILE, 'w') as f:
        json.dump(tools, f, indent=2)

def get_all_tools():
    return DEFAULT_TOOLS + load_custom_tools()

ALL_TOOLS = DEFAULT_TOOLS  # backward compat alias — rebuilt each call via get_all_tools()

def get_active_tools():
    return [t for t in get_all_tools() if session.tools_enabled.get(t['function']['name'], True)]

BUILTIN_TOOL_CATALOG = [
    {"name": "http_fetch",      "description": "Fetch a URL and return its content",
     "parameters": {"url": "string", "method": "string(GET/POST)"}},
    {"name": "read_file",       "description": "Read a local file and return its content",
     "parameters": {"path": "string"}},
    {"name": "write_file",      "description": "Write content to a local file",
     "parameters": {"path": "string", "content": "string"}},
    {"name": "list_directory",  "description": "List files and folders in a directory",
     "parameters": {"path": "string"}},
    {"name": "git_status",      "description": "Run git status in a repo directory",
     "parameters": {"path": "string"}},
    {"name": "git_log",         "description": "Show recent git commits",
     "parameters": {"path": "string", "n": "int"}},
    {"name": "run_python",      "description": "Execute a Python snippet and return output",
     "parameters": {"code": "string"}},
    {"name": "get_weather",     "description": "Get current weather for a location",
     "parameters": {"location": "string"}},
    {"name": "calculator",      "description": "Evaluate a math expression",
     "parameters": {"expression": "string"}},
    {"name": "translate_text",  "description": "Translate text between languages",
     "parameters": {"text": "string", "target_lang": "string"}},
    {"name": "summarize_url",   "description": "Fetch and summarize a webpage",
     "parameters": {"url": "string"}},
    {"name": "diff_files",      "description": "Show diff between two files",
     "parameters": {"file_a": "string", "file_b": "string"}},
    {"name": "json_query",      "description": "Query JSON data with a JMESPath expression",
     "parameters": {"data": "string", "query": "string"}},
    {"name": "send_notification","description": "Send a desktop notification",
     "parameters": {"title": "string", "message": "string"}},
    {"name": "clipboard_read",  "description": "Read current clipboard content",
     "parameters": {}},
    {"name": "clipboard_write", "description": "Write text to clipboard",
     "parameters": {"text": "string"}},
    {"name": "screenshot",      "description": "Take a screenshot and return image path",
     "parameters": {"output": "string"}},
    {"name": "cron_add",        "description": "Add a cron job",
     "parameters": {"schedule": "string", "command": "string"}},
    {"name": "docker_ps",       "description": "List running Docker containers",
     "parameters": {}},
    {"name": "sql_query",       "description": "Run a SQL query on a local SQLite database",
     "parameters": {"db_path": "string", "query": "string"}},
]

def search_tools_online(query):
    q = query.lower()
    matches = [t for t in BUILTIN_TOOL_CATALOG
               if q in t['name'].lower() or q in t['description'].lower()]
    if matches:
        return matches
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"AI tool function {query} JSON schema", max_results=3))
        tools = []
        for r in results:
            name = re.sub(r'[^a-z0-9_]', '_', query.lower()[:30]).strip('_')
            tools.append({
                "name": name,
                "description": r['body'][:120],
                "parameters": {},
            })
        seen = set(); unique = []
        for t in tools:
            if t['name'] not in seen:
                seen.add(t['name']); unique.append(t)
        return unique
    except Exception:
        return []

# ── SKILLS CATALOG ─────────────────────────────────────────────────────────────
# #You're not supposed to see this!
BUILTIN_SKILLS = [
    # ── Code & Dev ──────────────────────────────────────────────────────────────
    {"name": "code_review",     "description": "Review code for bugs, style and improvements",       "prompt": "You are a senior code reviewer. Analyze the presented code for bugs, performance issues, readability and best practices. Be precise and constructive. Show fixed snippets when relevant."}, 
    {"name": "refactor",        "description": "Refactor code for clarity and maintainability",      "prompt": "You are a refactoring expert. Improve the given code's structure, naming and readability without changing behavior. Explain each change."}, 
    {"name": "debug",           "description": "Find and fix bugs step by step",                     "prompt": "You are an expert debugger. Analyze the code or error, identify the root cause step by step, and provide a clear fix with explanation."}, 
    {"name": "test_writer",     "description": "Write unit and integration tests",                   "prompt": "You are a testing expert. Write comprehensive unit and integration tests for the given code. Use the project's existing test framework. Cover edge cases and failure paths."}, 
    {"name": "doc_writer",      "description": "Generate technical documentation",                   "prompt": "You are a technical writer. Generate clear, complete documentation with examples in the requested format (README, docstring, wiki, JSDoc, etc)."},
    {"name": "sql_expert",      "description": "Generate and optimize SQL queries",                  "prompt": "You are a database expert. Generate optimized SQL queries, explain execution plans and suggest indexes. Support PostgreSQL, MySQL and SQLite."}, 
    {"name": "regex_builder",   "description": "Build and explain regular expressions",              "prompt": "You are a regex expert. Build the requested regex, explain each part and provide match/non-match examples."}, 
    {"name": "git_helper",      "description": "Help with Git commands and workflows",               "prompt": "You are a Git expert. Provide exact commands, explain their effects and warn about destructive operations."}, 
    {"name": "api_designer",    "description": "Design and document REST/GraphQL APIs",              "prompt": "You are an API architect. Design RESTful endpoints or GraphQL schemas following best practices, with request/response examples and auth considerations."}, 
    {"name": "security_audit",  "description": "Audit code for vulnerabilities (OWASP)",             "prompt": "You are an application security expert (OWASP Top 10). Analyze code for injection, XSS, CSRF, auth issues and more. Classify by severity and suggest mitigations."}, 
    {"name": "performance",     "description": "Profile and optimize code performance",              "prompt": "You are a performance engineer. Identify bottlenecks, suggest algorithmic improvements, caching strategies and profiling approaches for the given code."}, 
    {"name": "architect",       "description": "System design and architecture decisions",           "prompt": "You are a senior software architect. Design scalable, maintainable systems. Discuss trade-offs, patterns (microservices, event-driven, CQRS) and draw ASCII diagrams when helpful."}, 
    {"name": "devops",          "description": "CI/CD, Docker, Kubernetes, infrastructure",         "prompt": "You are a DevOps engineer. Help with Docker, Kubernetes, CI/CD pipelines, Terraform and cloud infrastructure. Provide production-ready configs."}, 
    {"name": "shell_expert",    "description": "Write and explain bash/shell scripts",               "prompt": "You are a shell scripting expert. Write robust bash scripts with error handling, explain each part and warn about portability issues."}, 
    {"name": "python_expert",   "description": "Python best practices and idiomatic code",           "prompt": "You are a Python expert. Write idiomatic, Pythonic code following PEP 8. Use type hints, dataclasses, generators and other modern Python features where appropriate."}, 
    {"name": "javascript",      "description": "Modern JS/TS, React, Node.js",                      "prompt": "You are a JavaScript/TypeScript expert. Write modern ES2024+ code, use proper async patterns, and apply React/Node.js best practices."}, 
    {"name": "rust_expert",     "description": "Rust ownership, lifetimes and idioms",               "prompt": "You are a Rust expert. Write safe, idiomatic Rust. Explain ownership, borrowing and lifetimes clearly. Prefer zero-cost abstractions and avoid unnecessary clones."}, 
    {"name": "go_expert",       "description": "Go idioms, goroutines and interfaces",               "prompt": "You are a Go expert. Write idiomatic Go: simple interfaces, goroutines, channels and proper error handling. Follow effective Go guidelines."}, 
    # ── AI & Data ───────────────────────────────────────────────────────────────
    {"name": "prompt_engineer", "description": "Craft effective prompts for LLMs",                  "prompt": "You are a prompt engineering expert. Design clear, effective prompts for LLMs. Apply techniques like chain-of-thought, few-shot, role prompting and output structuring."}, 
    {"name": "data_analyst",    "description": "Analyze data, statistics and visualizations",       "prompt": "You are a data analyst. Analyze datasets, identify patterns, suggest visualizations and provide statistical insights. Use Python (pandas, matplotlib) when showing code."}, 
    {"name": "ml_engineer",     "description": "Machine learning models and pipelines",              "prompt": "You are an ML engineer. Design and debug machine learning pipelines, choose appropriate models, tune hyperparameters and explain evaluation metrics."}, 
    # ── Writing & Communication ─────────────────────────────────────────────────
    {"name": "translate",       "description": "Precise translation between languages",              "prompt": "You are a professional translator. Detect the source language automatically and translate with precision, preserving tone and context."}, 
    {"name": "summarize",       "description": "Summarize long texts concisely",                    "prompt": "You are a summarization expert. Summarize the given text clearly and structurally, extracting key points without losing critical information."}, 
    {"name": "copywriter",      "description": "Persuasive marketing and UX copy",                  "prompt": "You are a professional copywriter. Write clear, persuasive copy for landing pages, ads, emails or UX microcopy. Adapt tone to the brand voice."}, 
    {"name": "email_writer",    "description": "Write professional emails and responses",           "prompt": "You are an expert at professional communication. Write concise, clear and appropriately-toned emails. Ask for missing context if needed."}, 
    {"name": "interviewer",     "description": "Mock technical interview practice",                  "prompt": "You are a technical interviewer at a top tech company. Conduct a realistic mock interview for the requested role. Ask one question at a time, evaluate answers and give feedback."}, 
    # ── Math & Science ──────────────────────────────────────────────────────────
    {"name": "math_solver",     "description": "Solve math problems step by step",                  "prompt": "You are a math expert. Solve each problem step by step, showing full reasoning and verifying the result. Use LaTeX notation for formulas when helpful."}, 
    {"name": "latex_helper",    "description": "Write and format LaTeX documents",                  "prompt": "You are a LaTeX expert. Write well-formatted LaTeX for math, papers and presentations. Explain the structure and fix compilation errors."}, 
    # ── Productivity ────────────────────────────────────────────────────────────
    {"name": "brainstorm",      "description": "Generate and expand creative ideas",                "prompt": "You are a creative thinking facilitator. Generate diverse, original ideas using techniques like SCAMPER, lateral thinking and mind mapping. Push beyond the obvious."},  # PB4XULLSMFUW4YTPO56G63DM
    {"name": "planner",         "description": "Break goals into actionable plans",                 "prompt": "You are a productivity expert. Break down goals into concrete, prioritized action steps with time estimates. Identify dependencies and potential blockers."}, 
    {"name": "linux_admin",     "description": "Linux system administration and troubleshooting",   "prompt": "You are a Linux sysadmin. Provide exact commands for system administration, explain what they do and warn about risks. Cover permissions, networking, processes and logs."}, 
]

_CATALOG_SIG = b'\x78\x79\x7a\x2d\x72\x61\x69\x6e\x62\x6f\x77'  # catalog integrity

def load_skills_catalog():
    catalog = list(BUILTIN_SKILLS)
    if os.path.exists(SKILLS_CATALOG):
        try:
            with open(SKILLS_CATALOG) as _f:
                extra = json.load(_f)
            catalog += [s for s in extra if s.get('name') not in [x['name'] for x in catalog]]
        except Exception: pass
    return catalog

def search_skills_online(query):
    """Search skills: filter builtin catalog + web fallback for unknown topics."""
    q = query.lower()
    # 1. Match from full builtin catalog (not just currently installed)
    matches = [
        s for s in BUILTIN_SKILLS
        if q in s['name'].lower() or q in s['description'].lower()
    ]
    if matches:
        return matches
    # 2. Web fallback: synthesize a skill from DuckDuckGo snippet
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"AI assistant expert {query} system prompt", max_results=3))
        skills = []
        for r in results:
            name = re.sub(r'[^a-z0-9_]', '_', query.lower()[:30]).strip('_')
            skills.append({
                "name": name,
                "description": r['body'][:100],
                "prompt": f"You are an expert in {query}. {r['body'][:300]}",
            })
        # Deduplicate by name
        seen = set()
        unique = []
        for s in skills:
            if s['name'] not in seen:
                seen.add(s['name']); unique.append(s)
        return unique
    except Exception:
        return []

def get_active_skill_prompt():
    catalog = load_skills_catalog()
    active = [s for s in catalog if session.skills_enabled.get(s['name'], False)]
    if not active: return ""
    parts = [f"[SKILL: {s['name']}] {s['prompt']}" for s in active]
    return "\n\n" + "\n\n".join(parts)

# ── ANIMATION ──────────────────────────────────────────────────────────────────
class Animation:
    @staticmethod
    def hide_cursor():
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    @staticmethod
    def show_cursor():
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    @staticmethod
    def clear_screen():
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    @staticmethod
    def get_letter_x():
        return [
            "█       █",
            "  █   █  ",
            "    █    ",
            "  █   █  ",
            "█       █",
        ]

    @staticmethod
    def get_letter_y():
        return [
            "█       █",
            "  █   █  ",
            "    █    ",
            "    █    ",
            "    █    ",
        ]

    @staticmethod
    def get_letter_z():
        return [
            "█████████",
            "      █  ",
            "    █    ",
            "  █      ",
            "█████████",
        ]

    @staticmethod
    def ease_out_expo(t):
        return 1 if t == 1 else 1 - pow(2, -10 * t)

    @staticmethod
    def ease_in_expo(t):
        return 0 if t == 0 else pow(2, 10 * t - 10)

    @staticmethod
    def draw_letter(screen, art, center_px, center_py, color, width, height, reset="\033[0m"):
        letter_width = len(art[0])
        letter_height = len(art)
        start_x = int(center_px - (letter_width // 2))
        start_y = int(center_py - (letter_height // 2))
        for i, row in enumerate(art):
            for j, char in enumerate(row):
                if char != " ":
                    sy = start_y + i
                    sx = start_x + j
                    if 0 <= sy < height and 0 <= sx < width:
                        screen[sy][sx] = f"{color}{char}{reset}"

    @staticmethod
    def draw_frame(screen, width, height, padding=2, style="rounded"):
        chars = {"rounded": ("\u256d", "\u256e", "\u2570", "\u256f", "\u2500", "\u2502", "\u2591", "\u2591")}
        tl, tr, bl, br, h, v, _, _ = chars.get(style, chars["rounded"])
        pw = width - padding * 2 - 2

        y = padding
        row = tl + h * pw + tr
        for x in range(padding, width - padding):
            if 0 <= y < height and 0 <= x < width:
                screen[y][x] = row[x - padding] if x - padding < len(row) else " "

        y = height - padding - 1
        row = bl + h * pw + br
        for x in range(padding, width - padding):
            if 0 <= y < height and 0 <= x < width:
                screen[y][x] = row[x - padding] if x - padding < len(row) else " "

        for y in range(padding + 1, height - padding - 1):
            if 0 <= y < height:
                screen[y][padding] = v
                screen[y][width - padding - 1] = v

    @classmethod
    def play_intro(cls):
        import math, random, time
        cls.hide_cursor()
        cls.clear_screen()

        term_width = min(shutil.get_terminal_size().columns, 120)
        term_height = shutil.get_terminal_size().lines
        width = term_width
        height = term_height - 2
        if height <= 0: return
        center_x = width // 2
        center_y = height // 2

        C_X = "\033[1;96m"
        C_Y = "\033[1;32m"
        C_Z = "\033[1;35m"
        C_FRAME = "\033[1;90m"
        RESET = "\033[0m"

        PARTICLE_COLORS = ["\033[1;96m", "\033[1;32m", "\033[1;35m", "\033[1;33m", "\033[1;97m", "\033[1;90m"]

        lx = cls.get_letter_x()
        ly = cls.get_letter_y()
        lz = cls.get_letter_z()

        particles = []
        for _ in range(150):
            particles.append({
                "x": random.randint(1, width - 1),
                "y": random.randint(1, height - 1),
                "char": random.choice([".", "*", "°", "`", "+", "·"]),
                "color": random.choice(PARTICLE_COLORS),
                "vx": 0, "vy": 0,
            })

        frames = 100
        for frame in range(frames):
            out = "\033[H"
            screen = [[" " for _ in range(width)] for _ in range(height)]
            phase = frame / frames

            if phase < 0.4:
                for p in particles:
                    dx = center_x - p["x"]
                    dy = center_y - p["y"]
                    dist = max(1, math.sqrt(dx * dx + dy * dy))
                    attraction = 120 / (dist + 5)
                    p["vx"] += (dx / dist) * attraction * 0.1
                    p["vy"] += (dy / dist) * attraction * 0.1
                    p["vx"] *= 0.92
                    p["vy"] *= 0.92
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    px_int, py_int = int(p["x"]), int(p["y"])
                    if 0 <= px_int < width and 0 <= py_int < height:
                        screen[py_int][px_int] = f"{p['color']}{p['char']}{RESET}"

                swirl_phase = phase / 0.4
                radius = int(4 * swirl_phase)
                for a in range(0, 360, 45):
                    rad = math.radians(a + frame * 15)
                    sx = int(center_x + radius * math.cos(rad))
                    sy = int(center_y + radius * math.sin(rad) * 0.5)
                    if 0 <= sy < height and 0 <= sx < width:
                        screen[sy][sx] = f"{C_X if a % 90 == 0 else C_Y}@{RESET}"
                if 0 <= center_y < height and 0 <= center_x < width:
                    screen[center_y][center_x] = f"{C_Z}O{RESET}"

            elif phase < 0.8:
                emerge_phase = (phase - 0.4) / 0.4
                eased = cls.ease_out_expo(emerge_phase)
                offset = int(18 * eased)
                cur_x = center_x - offset
                cur_z = center_x + offset

                cls.draw_letter(screen, lx, cur_x, center_y, C_X, width, height, RESET)
                cls.draw_letter(screen, ly, center_x, center_y, C_Y, width, height, RESET)
                cls.draw_letter(screen, lz, cur_z, center_y, C_Z, width, height, RESET)

                for p in particles[:40]:
                    p["x"] -= p["vx"] * 0.5
                    p["y"] -= p["vy"] * 0.5
                    px_int, py_int = int(p["x"]), int(p["y"])
                    if 0 <= px_int < width and 0 <= py_int < height:
                        screen[py_int][px_int] = f"{p['color']}{p['char']}{RESET}"

            else:
                cur_x = center_x - 18
                cur_z = center_x + 18
                cls.draw_letter(screen, lx, cur_x, center_y, C_X, width, height, RESET)
                cls.draw_letter(screen, ly, center_x, center_y, C_Y, width, height, RESET)
                cls.draw_letter(screen, lz, cur_z, center_y, C_Z, width, height, RESET)

                frame_phase = (phase - 0.8) / 0.2
                if frame_phase > 0.1:
                    out_frame = [[" " for _ in range(width)] for _ in range(height)]
                    cls.draw_frame(out_frame, width, height, padding=2, style="rounded")
                    for y in range(height):
                        for x in range(width):
                            if out_frame[y][x] != " ":
                                color = "\033[1;97m" if frame_phase < 0.4 else C_FRAME
                                screen[y][x] = f"{color}{out_frame[y][x]}{RESET}"

            for row in screen:
                out += "".join(row) + "\n"

            sys.stdout.write(out)
            sys.stdout.flush()
            time.sleep(0.045)

        cls.clear_screen()
        cls.show_cursor()

    @classmethod
    def play_outro(cls):
        import math, random, time
        cls.hide_cursor()
        cls.clear_screen()

        term_width = min(shutil.get_terminal_size().columns, 120)
        term_height = shutil.get_terminal_size().lines
        width = term_width
        height = term_height - 2
        if height <= 0: return
        center_x = width // 2
        center_y = height // 2

        C_X = "\033[1;96m"
        C_Y = "\033[1;32m"
        C_Z = "\033[1;35m"
        C_FRAME = "\033[1;90m"
        RESET = "\033[0m"

        lx = cls.get_letter_x()
        ly = cls.get_letter_y()
        lz = cls.get_letter_z()

        PARTICLE_COLORS = ["\033[1;96m", "\033[1;32m", "\033[1;35m", "\033[1;33m", "\033[1;97m", "\033[1;90m"]
        particles = []
        
        frames = 70
        for frame in range(frames):
            out = "\033[H"
            screen = [[" " for _ in range(width)] for _ in range(height)]
            phase = frame / frames

            if phase < 0.3:
                cur_x = center_x - 18
                cur_z = center_x + 18
                cls.draw_letter(screen, lx, cur_x, center_y, C_X, width, height, RESET)
                cls.draw_letter(screen, ly, center_x, center_y, C_Y, width, height, RESET)
                cls.draw_letter(screen, lz, cur_z, center_y, C_Z, width, height, RESET)
                
                fade = 1.0 - (phase / 0.3)
                out_frame = [[" " for _ in range(width)] for _ in range(height)]
                cls.draw_frame(out_frame, width, height, padding=2, style="rounded")
                for y in range(height):
                    for x in range(width):
                        if out_frame[y][x] != " ":
                            if random.random() < fade:
                                color = "\033[1;97m" if random.random() < 0.1 else C_FRAME
                                screen[y][x] = f"{color}{out_frame[y][x]}{RESET}"

            elif phase < 0.7:
                collapse_phase = (phase - 0.3) / 0.4
                eased = cls.ease_in_expo(collapse_phase)
                
                offset = int(18 * (1 - eased))
                cur_x = center_x - offset
                cur_z = center_x + offset
                
                cls.draw_letter(screen, lx, cur_x, center_y, C_X, width, height, RESET)
                cls.draw_letter(screen, ly, center_x, center_y, C_Y, width, height, RESET)
                cls.draw_letter(screen, lz, cur_z, center_y, C_Z, width, height, RESET)
                
                radius = int(4 * eased)
                for a in range(0, 360, 45):
                    rad = math.radians(a - frame * 15)
                    sx = int(center_x + radius * math.cos(rad))
                    sy = int(center_y + radius * math.sin(rad) * 0.5)
                    if 0 <= sy < height and 0 <= sx < width:
                        screen[sy][sx] = f"{C_X if a % 90 == 0 else C_Y}@{RESET}"
                if 0 <= center_y < height and 0 <= center_x < width:
                    screen[center_y][center_x] = f"{C_Z}O{RESET}"

            else:
                explode_phase = (phase - 0.7) / 0.3
                if explode_phase < 0.2 and len(particles) < 150:
                    for _ in range(30):
                        px = center_x + random.randint(-2, 2)
                        py = center_y + random.randint(-1, 1)
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(2.0, 5.0)
                        particles.append({
                            "x": px, "y": py,
                            "color": random.choice(PARTICLE_COLORS),
                            "vx": math.cos(angle) * speed,
                            "vy": math.sin(angle) * speed * 0.5,
                            "char": random.choice([".", "*", "°", "`", "+", "·"])
                        })
                        
                for p in particles:
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    px_int, py_int = int(p["x"]), int(p["y"])
                    if 0 <= px_int < width and 0 <= py_int < height:
                        screen[py_int][px_int] = f"{p['color']}{p['char']}{RESET}"

            for row in screen:
                out += "".join(row) + "\n"

            sys.stdout.write(out)
            sys.stdout.flush()
            time.sleep(0.04)

        cls.clear_screen()
        cls.show_cursor()

# ── UTILIDADES ─────────────────────────────────────────────────────────────────
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_banner(version="v4.9.1"):
    # #xyz-rainbow #rainbow.xyz
    return (
        f"\n  {C('ACCENT')}[XYZ]{C_RESET} \033[1;37mOLLAMA-RUN{C_RESET} {C('INFO')}{version}{C_RESET}"
        f"  {C('DIM')}© Rainbow Technology{C_RESET}"
    )

def print_tool_msg(msg):
    print(f"\n  {C('TOOL')}⚙  {msg}{C_RESET}")

def print_tool_result(name, preview):
    short = str(preview).strip().splitlines()[0][:120]
    print(f"  {C('TOOL_R')}↳ [{name}] {short}{C_RESET}\n")

# ── FUNCIONES DE HERRAMIENTAS ──────────────────────────────────────────────────
# #xyz-rainbowtechnology
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
    local_path = image_path.strip().strip("'").strip('"')
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

_HIST_MARKER = "cmFpbmJvd3RlY2hub2xvZ3kueHl6"  # history module tag
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
            if key in ('\x1b', '\x11'): return ('\x11' if key == '\x11' else None)
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

def _viewport(idx, total, reserved_lines=7):
    """Return (scroll_offset, page_size) so idx is always visible."""
    rows = os.get_terminal_size().lines if hasattr(os, 'get_terminal_size') else 24
    page = max(3, rows - reserved_lines)
    offset = max(0, min(idx - page // 2, total - page))
    return offset, page

def interactive_menu(options, title, right_action=None, right_hint=None):
    idx = 0
    while True:
        clear_screen()
        print(get_banner())
        print(f"\n  {C('ACCENT')}{title}{C_RESET}\n")
        offset, page = _viewport(idx, len(options))
        visible = options[offset:offset + page]
        if offset > 0:
            print(f"  {C('DIM')}  ↑ {offset} more above{C_RESET}")
        for i, opt in enumerate(visible):
            gi = i + offset
            if gi == idx: print(f"  {C('SEL')}> {opt}{C_RESET}")
            else:         print(f"    {opt}")
        below = len(options) - offset - page
        if below > 0:
            print(f"  {C('DIM')}  ↓ {below} more below{C_RESET}")
        if right_hint:
            print(f"\n  {C('INFO')}[→] {right_hint}{C_RESET}")
        key = get_key()
        if   key == '\x11': return '\x11'
        elif key == '\x1b': return None
        elif key == '\x1b[A':  idx = (idx - 1) % len(options)
        elif key == '\x1b[B':  idx = (idx + 1) % len(options)
        elif key in ['\r','\n','\r\n']: return options[idx]
        elif key == '\x1b[C' and right_action: right_action(idx)

# ── TOGGLE LIST (para /tools y /skills) ───────────────────────────────────────
def toggle_list_menu(title, items, state_dict, default_state=False, extra_top=None,
                     deletable_key=None, on_delete=None):
    """
    Menú de lista con toggle por ESPACIO.
    items: list of {"name": str, "description": str}
    state_dict: dict mutable name→bool
    extra_top: lista de opciones especiales al inicio
    deletable_key: item field that marks an item as deletable (bool)
    on_delete: callback(name) called when Del is pressed on a deletable item
    """
    idx = 0
    all_options = (extra_top or []) + items
    n_extra = len(extra_top) if extra_top else 0

    def _rebuild():
        return (extra_top or []) + items  # caller must reassign items before calling

    while True:
        clear_screen()
        print(get_banner())
        can_del = any(
            isinstance(item, dict) and (deletable_key is None or item.get(deletable_key, True))
            for item in all_options[n_extra:]
        )
        del_hint = f"  {C('ERR')}[Del] delete{C_RESET}" if can_del else ""
        print(f"\n  {C('ACCENT')}{title}{C_RESET}  {C('INFO')}[SPACE] toggle  [Enter] select  [ESC] exit{C_RESET}{del_hint}\n")

        offset, page = _viewport(idx, len(all_options))
        if offset > 0:
            print(f"  {C('DIM')}  ↑ {offset} more above{C_RESET}")
        for i, item in enumerate(all_options[offset:offset + page]):
            gi = i + offset
            is_extra = gi < n_extra
            selected = (gi == idx)
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
                deletable = deletable_key is None or item.get(deletable_key, False)
                lock_hint  = f" {C('DIM')}[default]{C_RESET}" if not deletable else ""
                print(f"{marker} [{status_color}{status_text}{C_RESET}]  {C('RESP')}{name}{C_RESET}  {C('DIM')}{desc}{C_RESET}{lock_hint}")
        below = len(all_options) - offset - page
        if below > 0:
            print(f"  {C('DIM')}  ↓ {below} more below{C_RESET}")

        key = get_key()
        if key == '\x11': return '\x11'
        elif key == '\x1b': break
        elif key == '\x1b[A': idx = (idx - 1) % len(all_options)
        elif key == '\x1b[B': idx = (idx + 1) % len(all_options)
        elif key == ' ':
            if idx >= n_extra:
                name = all_options[idx]['name']
                state_dict[name] = not state_dict.get(name, default_state)
                session.save_config()
        elif key == '\x1b[3~':  # Delete/Supr
            if idx >= n_extra and isinstance(all_options[idx], dict):
                item = all_options[idx]
                name = item['name']
                deletable = deletable_key is None or item.get(deletable_key, False)
                if deletable:
                    if on_delete:
                        on_delete(name)
                    else:
                        # Default: skills catalog removal
                        if os.path.exists(SKILLS_CATALOG):
                            try:
                                with open(SKILLS_CATALOG) as _f:
                                    catalog = json.load(_f)
                                catalog = [s for s in catalog if s.get('name') != name]
                                with open(SKILLS_CATALOG, 'w') as f: json.dump(catalog, f, indent=2)
                            except Exception:
                                pass
                        state_dict.pop(name, None)
                        session.save_config()
                    all_options = (extra_top or []) + [
                        x for x in all_options[n_extra:] if x.get('name') != name
                    ]
                    idx = min(idx, len(all_options) - 1)
        elif key in ['\r','\n','\r\n']:
            if idx < n_extra:
                return all_options[idx]  # retorna la opción especial seleccionada
            else:
                name = all_options[idx]['name']
                state_dict[name] = not state_dict.get(name, default_state)
                session.save_config()

# ── /TOOLS ────────────────────────────────────────────────────────────────────
def open_tools():
    while True:
        all_t = get_all_tools()
        items = [{'name': t['function']['name'], 'description': t['function']['description'],
                  '_deletable': t['function']['name'] not in DEFAULT_TOOL_NAMES}
                 for t in all_t]
        result = toggle_list_menu(
            "TOOLS",
            items,
            session.tools_enabled,
            default_state=True,
            extra_top=["[Search tools]"],
            deletable_key='_deletable',
            on_delete=_delete_custom_tool,
        )
        if result == "[Search tools]":
            clear_screen()
            print(get_banner())
            print(f"\n  {C('ACCENT')}SEARCH TOOLS{C_RESET}\n")
            q = input(f"  {C('INFO')}Search:{C_RESET} ").strip()
            if q:
                clear_screen()
                print(get_banner())
                print(f"\n  {C('DIM')}Searching tools for '{q}'…{C_RESET}\n")
                found = search_tools_online(q)
                if found:
                    existing = load_custom_tools()
                    names = {t['function']['name'] for t in get_all_tools()}
                    added = 0
                    for ft in found:
                        tname = ft['name']
                        if tname not in names:
                            existing.append({'type': 'function', 'function': {
                                'name': tname,
                                'description': ft.get('description', ''),
                                'parameters': {'type': 'object', 'properties': {
                                    k: {'type': 'string'} for k in ft.get('parameters', {})
                                }, 'required': []},
                            }})
                            added += 1
                    save_custom_tools(existing)
                    print(f"  {C('OK')}✓ {added} tools added.{C_RESET}\n")
                else:
                    print(f"  {C('WARN')}No tools found.{C_RESET}\n")
                input(f"  {C('DIM')}[Enter]{C_RESET}")
        else:
            break

def _delete_custom_tool(name):
    custom = load_custom_tools()
    custom = [t for t in custom if t['function']['name'] != name]
    save_custom_tools(custom)
    session.tools_enabled.pop(name, None)
    session.save_config()

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
                        try:
                            with open(SKILLS_CATALOG) as _f: existing = json.load(_f)
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
            print(f"\n  {C('WARN')}{T('no_models')}{C_RESET}")
            input(f"  {C('DIM')}[Enter]{C_RESET}"); return None
        return interactive_menu(models, T('select_model'))
    except Exception as e:
        print(f"\n  {C('ERR')}Error: {e}{C_RESET}"); return None

def pull_model(model_name):
    clear_screen()
    print(get_banner())
    print(f"\n  {C('ACCENT')}{T('downloading')}{C_RESET}  {C('INFO')}{model_name}{C_RESET}\n")
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
        
        offset, page = _viewport(idx, len(tags), reserved_lines=14)
        visible = tags[offset:offset + page]
        
        if offset > 0:
            print(f"  {C('DIM')}  ↑ {offset} more above{C_RESET}")
            
        for i, tag in enumerate(visible):
            gi = i + offset
            if gi == idx:
                print(f"  {C('SEL')}> {tag}{C_RESET}")
            else:
                print(f"    {C('INFO')}{tag}{C_RESET}")
                
        below = len(tags) - offset - page
        if below > 0:
            print(f"  {C('DIM')}  ↓ {below} more below{C_RESET}")

        key = get_key()
        if key == '\x11': return # Global exit signal will bubble up
        elif key == '\x1b': break
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
            offset, page = _viewport(idx, len(models), reserved_lines=10)
            visible = models[offset:offset + page]
            
            if offset > 0:
                print(f"  {C('DIM')}  ↑ {offset} more above{C_RESET}")
                
            for i, m in enumerate(visible):
                gi = i + offset
                name = m.get('name', str(m)) if isinstance(m, dict) else str(m)
                desc = (m.get('description', '') if isinstance(m, dict) else '')[:60]
                upd  = m.get('updated', '') if isinstance(m, dict) else ''
                if gi == idx:
                    print(f"  {C('SEL')}> {name}{C_RESET}  {C('DIM')}{desc}{C_RESET}  {C('INFO')}{upd}{C_RESET}")
                else:
                    print(f"    {C('INFO')}{name}{C_RESET}  {C('DIM')}{desc}{C_RESET}")
                    
            below = len(models) - offset - page
            if below > 0:
                print(f"  {C('DIM')}  ↓ {below} more below{C_RESET}")

        key = get_key()
        if key == '\x11': return # Exit search
        elif key == '\x1b': break
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
    # ed16048676de7958e429aff7174edcd4754c9abf044108febef29edec95ae3f5
    while True:
        opts = [
            f"Model:    {session.model}",
            f"Thinking: {session.thinking_mode}",
            f"Level:    {session.thinking_level}",
            f"Theme:    {session.theme}",
            "Tools…",
            "Skills…",
            "History…",
            "Pull model…",
            "Search models…",
            "Chats…",
            "Back",
        ]
        opt = interactive_menu(opts, "SETTINGS")
        if opt == '\x11': return '\x11'
        if not opt or "Back" in opt: break
        if "Model"    in opt:
            new = select_model()
            if new == '\x11': return '\x11'
            if new: session.model = new; session.save_config()
        elif "Thinking" in opt:
            mode = interactive_menu(["OFF","ON","FORCE"], "THINKING MODE")
            if mode == '\x11': return '\x11'
            if mode: session.thinking_mode = mode; session.save_config()
        elif "Level"   in opt:
            lv = interactive_menu(["Low","Medium","High"], "THINKING LEVEL")
            if lv == '\x11': return '\x11'
            if lv: session.thinking_level = lv; session.save_config()
        elif "Theme"   in opt:
            th = interactive_menu(list(THEMES.keys()), "THEME")
            if th == '\x11': return '\x11'
            if th: session.theme = th; session.save_config()
        elif opt == "Tools…":
            if open_tools() == '\x11': return '\x11'
        elif opt == "Skills…":
            if open_skills() == '\x11': return '\x11'
        elif opt == "History…":
            if open_history() == '\x11': return '\x11'
        elif "Pull"    in opt:
            clear_screen(); print(get_banner())
            name = input(f"\n  {C('INFO')}Model name:{C_RESET} ").strip()
            if name: pull_model(name)
        elif "Search" in opt:
            if search_models() == '\x11': return '\x11'
        elif "Chats"   in opt:
            if open_history_settings() == '\x11': return '\x11'

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
        if choice == '\x11': return '\x11'
        if not choice or "Back" in choice: break
        if "Delete all" in choice:
            shutil.rmtree(SESSIONS_DIR); os.makedirs(SESSIONS_DIR, exist_ok=True)
            break
        # Find session and offer to delete
        for s in sessions_list:
            label = f"{s['date']}  {s['model']}  {s['preview']}"
            if choice == label:
                action = interactive_menu(["View preview", "Delete this chat", "Back"], f"CHAT: {s['date']}")
                if action == '\x11': return '\x11'
                if action == "Delete this chat":
                    os.remove(s['path'])
                break

# ── SYSTEM PROMPT ──────────────────────────────────────────────────────────────
def get_system_prompt():
    _sp_tag = "eHl6LXJhaW5ib3d8b2xsYW1hLXJ1bg=="  # prompt registry
    active_tool_names = [t['function']['name'] for t in get_active_tools()]
    tools_str = ", ".join(active_tool_names) if active_tool_names else "none"

    base = (
        "You are an elite AI assistant built by Rainbow Technology — precise, direct, and deeply capable.\n"
        "\n"
        "## Core behavior\n"
        "- Always match the user's language exactly (Spanish → Spanish, English → English, etc.)\n"
        "- Be concise but complete. Never pad responses. Never repeat the question back.\n"
        "- Prioritize actionable answers: code, commands, steps — not vague theory.\n"
        "- When uncertain, say so clearly and give your best reasoned answer.\n"
        "- Format output for readability: use markdown, code blocks, and lists where they help.\n"
        "\n"
        "## Tools available\n"
        f"Active: {tools_str}\n"
        "Use tools proactively when they improve the answer. After a tool call, synthesize the result — "
        "don't just dump raw output. If a tool fails, explain why and offer an alternative."
    )

    thinking = {
        "OFF": (
            "## Thinking\n"
            "Respond directly. Do not use <thought> tags."
        ),
        "ON": (
            "## Thinking\n"
            "Before every response, reason inside <thought>...</thought> tags.\n"
            "Use the thought block to: break down the problem, consider edge cases, plan your approach.\n"
            "After </thought>, write only the final polished response — no redundancy with the thought.\n"
            "Format:\n<thought>\n[reasoning]\n</thought>\n[response]"
        ),
        "FORCE": (
            "## Thinking (FORCED)\n"
            "Every single reply MUST use this exact structure — no exceptions:\n"
            "\n"
            "<thought>\n"
            "1. Restate the core question in your own words\n"
            "2. Identify what's known, unknown, and potentially ambiguous\n"
            "3. Consider multiple approaches and their trade-offs\n"
            "4. Choose the best path and explain why\n"
            "5. Note any caveats or follow-up the user should know\n"
            "</thought>\n"
            "[Final response — clear, complete, no repetition of the reasoning above]\n"
            "\n"
            "CRITICAL RULES:\n"
            "- ALWAYS close </thought> before writing the response\n"
            "- NEVER put the final answer inside <thought>\n"
            "- The response section must stand alone — a user who skips <thought> gets a complete answer"
        ),
    }[session.thinking_mode]

    communication = (
        "\n\n## Communication style\n"
        "- Lead with the answer or action, never with preamble ('Sure!', 'Great question', 'Of course').\n"
        "- Use the user's register: casual if they're casual, technical if they're technical.\n"
        "- For code: always use fenced code blocks with the correct language tag.\n"
        "- For lists of steps: number them. For options/comparisons: use a table or bullet list.\n"
        "- End responses cleanly — no filler sign-offs like 'I hope this helps!' or 'Let me know!'.\n"
        "- If the user's request is ambiguous, make a reasonable assumption, state it briefly, then proceed."
    )

    skill_prompt = get_active_skill_prompt()
    return f"{base}\n\n{thinking}{communication}{skill_prompt}"

# ── STREAMING MEJORADO ─────────────────────────────────────────────────────────
def stream_response(response_iter, show_thinking=True):
    full_text = ""
    thought_shown = False
    response_shown = False

    def _ensure_thinking_header():
        nonlocal thought_shown
        if not thought_shown and show_thinking:
            print(f"\n  {C('THINK_L')}── {T('thinking')} ────────────────────────────{C_RESET}\n  {C('THINK')}", end="", flush=True)
            thought_shown = True

    def _ensure_response_header():
        nonlocal response_shown
        if not response_shown:
            print(f"\n  {C('RESP')}── {T('response')} ────────────────────────────{C_RESET}\n  ", end="", flush=True)
            response_shown = True

    for chunk in response_iter:
        thinking_piece = chunk['message'].thinking
        content_piece  = chunk['message'].content

        if thinking_piece and show_thinking:
            _ensure_thinking_header()
            print(f"{C('THINK')}{thinking_piece}{C_RESET}", end="", flush=True)

        if content_piece:
            if thought_shown and not response_shown:
                print(f"\n  {C('DIM')}───────────────────────────────────────{C_RESET}", end="", flush=True)
            _ensure_response_header()
            print(f"{C('RESP')}{content_piece}{C_RESET}", end="", flush=True)
            full_text += content_piece

    if response_shown or thought_shown:
        print(f"\n  {C('DIM')}───────────────────────────────────────{C_RESET}\n")
    return full_text

# ── STATUS BAR ────────────────────────────────────────────────────────────────
def print_status():
    active_t = sum(1 for v in session.tools_enabled.values() if v)
    active_s = sum(1 for v in session.skills_enabled.values() if v)
    skills_str = f"  {C('ACCENT')}{T('skills')}:{active_s}{C_RESET}" if active_s else ""
    model_display = session.model if session.model else f"{C('ERR')}No model selected{C_RESET}"
    vision_str = f"  {C('OK')}👁 {T('vision')}{C_RESET}" if is_vision_model(session.model) else ""
    print(f"  {C('INFO')}{model_display}  {T('thinking')}:{session.thinking_mode}  {T('tools')}:{active_t}/{len(session.tools_enabled)}{skills_str}  {T('theme')}:{session.theme}{vision_str}{C_RESET}")
    img_hint = f" /img <path|url>" if is_vision_model(session.model) else ""
    print(f"  {C('DIM')}Commands: /exit(/e) /settings(/st) /model(/m) /tools(/t) /skills(/sk) /search(/sr) /pull(/p) /history(/h){img_hint}{C_RESET}\n")

# ── CHAT ───────────────────────────────────────────────────────────────────────
# ── VISION ────────────────────────────────────────────────────────────────────
VISION_KEYWORDS = ['llava', 'bakllava', 'moondream', 'vision', 'minicpm-v',
                   'llama3.2-vision', 'gemma3', 'qwen2-vl', 'cogvlm', 'phi3-vision',
                   'pixtral', 'idefics', 'internvl', 'deepseek-vl']

def is_vision_model(model_name):
    if not model_name: return False
    name = model_name.lower()
    return any(k in name for k in VISION_KEYWORDS)

def load_image_b64(path):
    """Load an image from path or URL and return base64."""
    path = path.strip().strip('"').strip("'")
    # URL
    if path.startswith('http://') or path.startswith('https://'):
        resp = requests.get(path, timeout=15)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode()
    # Local path — expand ~ and variables
    path = os.path.expandvars(os.path.expanduser(path))
    if not os.path.exists(path):
        raise FileNotFoundError(f"Not found: {path}")
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

IMG_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif', '.avif')

def parse_image_input(inp):
    """
    Detect if input contains an image. Formats:
      /img <path|url> [text]     — explicit command
      /image <path|url> [text]   — alias
      <image_path>               — drag file to terminal
      <image_path> <text>        — path + question
      file://<path>              — file:// prefix
    Returns (text, path) or (inp, None).
    """
    IMG_EXTS_SET = set(IMG_EXTS)

    # 1. Explicit command /img or /image or /i
    for prefix in ('/img ', '/image ', '/i '):
        if inp.lower().startswith(prefix):
            rest = inp[len(prefix):].strip()
            # #xyz-rainbow
            parts = rest.split(' ', 1)
            return (parts[1] if len(parts) > 1 else "Describe this image."), parts[0]

    # 2. file:// prefix
    clean = inp.strip().strip('"').strip("'")
    if clean.startswith('file://'):
        from urllib.parse import unquote
        path = unquote(clean[7:])
        if os.path.splitext(path)[1].lower() in IMG_EXTS_SET:
            return "Describe this image.", path

    # 3. Loose path
    unescaped = clean.replace('\\ ', ' ')
    candidates = [unescaped]
    if ' ' in unescaped:
        for i in range(len(unescaped), 0, -1):
            part = unescaped[:i]
            if os.path.splitext(part)[1].lower() in IMG_EXTS_SET:
                candidates.insert(0, part)
                break

    for cand in candidates:
        cand_exp = os.path.expandvars(os.path.expanduser(cand))
        if os.path.splitext(cand_exp)[1].lower() in IMG_EXTS_SET and os.path.exists(cand_exp):
            text_after = unescaped[len(cand):].strip()
            return (text_after if text_after else "Describe this image."), cand_exp

    return inp, None

def chat(preloaded_msgs=None):
    # #You're not supposed to see this!
    _chat_origin = bytes([0x72,0x6e,0x62,0x77,0x2d,0x78,0x79,0x7a]).decode()  # runtime watermark
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

            # Ctrl+Q → exit immediately
            if inp == '\x11':
                break

            # ── Commands ──
            if inp.startswith('/'):
                low_inp = inp.lower()
                cmd_parts = low_inp.split()
                cmd = cmd_parts[0]

                if cmd in ('/exit', '/e'): break
                elif cmd in ('/settings', '/st'):
                    res = open_settings(); show_thinking = session.thinking_mode != "OFF"
                    if res == '\x11': break
                    clear_screen(); print(get_banner()); print_status(); continue
                elif cmd in ('/tools', '/t'):
                    res = open_tools()
                    if res == '\x11': break
                    clear_screen(); print(get_banner()); print_status(); continue
                elif cmd in ('/skills', '/sk'):
                    res = open_skills()
                    if res == '\x11': break
                    clear_screen(); print(get_banner()); print_status(); continue
                elif cmd in ('/model', '/m'):
                    new = select_model()
                    if new == '\x11': break
                    if new: session.model = new; session.save_config()
                    clear_screen(); print(get_banner()); print_status(); continue
                elif cmd in ('/search', '/sr'):
                    res = search_models()
                    if res == '\x11': break
                    clear_screen(); print(get_banner()); print_status(); continue
                elif cmd in ('/pull', '/p'):
                    name = inp[len(cmd):].strip()
                    if name: pull_model(name)
                    else: print(f"  {C('WARN')}Usage: {cmd} <model>")
                    continue
                elif cmd in ('/history', '/h'):
                    loaded = open_history()
                    if loaded == '\x11': break
                    if loaded:
                        msgs = loaded
                        print(f"\n  {C('OK')}✓ Conversation loaded ({len([m for m in msgs if m['role']=='user'])} messages){C_RESET}\n")
                    clear_screen(); print(get_banner()); print_status(); continue
                elif cmd in ('/img', '/i'):
                    # Fallthrough to image parsing logic below but as a known command
                    pass
                else:
                    print(f"  {C('ERR')}Unknown command: {cmd}{C_RESET}")
                    continue

            # ── Image ──
            text, img_path = parse_image_input(inp)
            img_b64 = None
            if img_path:
                if is_vision_model(session.model):
                    try:
                        print(f"  {C('DIM')}Loading image…{C_RESET}", end="", flush=True)
                        img_b64 = load_image_b64(img_path)
                        print(f"\r  {C('OK')}✓ Image loaded ({len(img_b64)//1024}KB){C_RESET}\n")
                        inp = text
                    except Exception as e:
                        print(f"\r  {C('ERR')}✗ Could not load image: {e}{C_RESET}\n")
                        continue
                else:
                    active_tool_names = [t['function']['name'] for t in get_active_tools()]
                    if 'describe_image' in active_tool_names or 'ocr_image' in active_tool_names:
                        print(f"  {C('INFO')}Non-vision model — using tools to analyze image…{C_RESET}\n")
                        inp = f"{text}\nImage to analyze: {img_path}"
                        img_path = None
                    else:
                        print(f"\n  {C('WARN')}⚠ Non-vision model and describe_image/ocr_image tools are disabled.")
                        print(f"  {C('DIM')}Enable tools in /tools or use a vision model.{C_RESET}\n")
                        continue

            if not session.model:
                print(f"\n  {C('ERR')}✗ No model selected. Use /settings to choose one.{C_RESET}")
                continue

            if img_b64:
                user_msg = {'role': 'user', 'content': inp, 'images': [img_b64]}
            else:
                user_msg = {'role': 'user', 'content': inp}
            msgs.append(user_msg)

            active_tools = get_active_tools()
            use_tools = active_tools if (active_tools and not img_b64) else None

            try:
                response = client.chat(
                    model=session.model,
                    messages=msgs,
                    tools=use_tools,
                    stream=True,
                    think=show_thinking,
                )
                full_content = stream_response(response, show_thinking=show_thinking)

            except Exception as e:
                msgs.pop()
                print(f"\n  {C('ERR')}✗ Error communicating with model: {e}{C_RESET}")
                if 'model' in str(e).lower() or 'not found' in str(e).lower():
                    print(f"  {C('WARN')}Model '{session.model}' may not be available. Use /settings to change it.{C_RESET}")
                elif 'connect' in str(e).lower() or 'refused' in str(e).lower():
                    print(f"  {C('WARN')}Cannot connect to Ollama. Is it running?{C_RESET}")
                continue

            ast_msg = {'role': 'assistant', 'content': full_content}
            msgs.append(ast_msg)

            if active_tools and not img_b64:
                try:
                    r2 = client.chat(model=session.model, messages=msgs[:-1], tools=active_tools, stream=False)
                    m2 = r2.message if hasattr(r2, 'message') else r2['message']
                    if hasattr(m2, 'tool_calls') and m2.tool_calls:
                        tools_called = list(m2.tool_calls)
                        msgs[-1]['content'] = m2.content or full_content
                        msgs[-1]['tool_calls'] = tools_called

                        print(f"\n  {C('TOOL')}── Executing tools ────────────────────{C_RESET}")
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

                        final = client.chat(model=session.model, messages=msgs, stream=True, think=show_thinking)
                        final_text = stream_response(final, show_thinking=show_thinking)
                        msgs.append({'role': 'assistant', 'content': final_text})
                except Exception as e:
                    print(f"\n  {C('ERR')}✗ Error processing tool calls: {e}{C_RESET}")

            save_session(msgs, session_id)

        except KeyboardInterrupt:
            import time
            now = time.time()
            if now - _last_ctrl_c < 2.0:
                save_session(msgs, session_id)
                print(f"\n  {C('DIM')}Bye.{C_RESET}\n")
                break
            _last_ctrl_c = now
            print(f"\n  {C('DIM')}{T('ctrl_q_hint')}{C_RESET}")
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
        # #rainbow@rainbowtechnology.xyz
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
            print(f"\n\n  {C('OK')}✓ {T('ready')}.{C_RESET}\n")
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
    # #rainbow.xyz
    if len(sys.argv) >= 3 and sys.argv[1].lower() == 'pull':
        if not ensure_ollama_running(): return
        pull_model(sys.argv[2]); return
    if len(sys.argv) >= 2 and sys.argv[1].lower() == 'search':
        search_models(); return

    Animation.play_intro()

    if not ensure_ollama_running():
        return

    # Check if we have models installed and if the current model is valid
    try:
        models_list = client.list().models
        available = [m.model for m in models_list] if models_list else []
        if session.model and session.model not in available:
            session.model = "" # Reset if model is missing from system
    except Exception:
        pass

    try:
        chat()
    finally:
        Animation.play_outro()
        stop_ollama_if_we_started()
        try:
            import readline as _rl
            os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
            _rl.write_history_file(HISTORY_FILE)
        except Exception:
            pass

if __name__ == "__main__":
    # MFWWCLLSOVXHYUTBNFXGE33XEBKGKY3I | © Rainbow Technology
    main()
