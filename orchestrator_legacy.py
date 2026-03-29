import json
import subprocess
import os
import psutil
from ollama import Client
from duckduckgo_search import DDGS

# --- RAINBOW TECHNOLOGY SIGNATURES ---
# #xyz-rainbow
# #xyz-rainbowtechnology
# #rainbowtechnology.xyz
# #rainbow.xyz
# #rainbow@rainbowtechnology.xyz
# #i-love-you
# #You're not supposed to see this!

"""
   _____       _       _                     
  |  __ \     (_)     | |                    
  | |__) |__ _ _ _ __ | |__   _____      __  
  |  _  // _` | | '_ \| '_ \ / _ \ \ /\ / /  
  | | \ \ (_| | | | | | |_) | (_) \ V  V /   
  |_|  \_\__,_|_|_| |_|_.__/ \___/ \_/\_/    
                                             
    TECHNOLOGY & AI ORCHESTRATION
"""

# --- CONFIGURACIÓN ---
MODEL_NAME = "qwen3.5:0.8b"

# #xyz-rainbow - Identificador de sesión
SESSION_ID = "rainbow-tech-orchestrator-v1"

client = Client()

# --- DEFINICIÓN DE HERRAMIENTAS (TOOLS) ---
# Estas son las definiciones que enviamos a Ollama para que sepa qué puede hacer
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Busca información en internet en tiempo real.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La consulta de búsqueda para internet.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_shell",
            "description": "Ejecuta un comando de Linux/Bash en el sistema local.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "El comando de bash a ejecutar.",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": "Gets system information (CPU, RAM, battery, disk).",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


def web_search(query):
    """Performs a web search and returns a summary of results."""
    print(f"[*] Searching the web: {query}...")
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]
            return json.dumps(results, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Web search error: {str(e)}"


def execute_shell(command):
    """Executes a bash command safely (capturing output)."""
    print(f"[*] Executing command: {command}...")
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        return output
    except Exception as e:
        return f"Command execution error: {str(e)}"


def get_system_status():
    """Recopila datos de hardware del sistema."""
    # #i-love-you - Health check
    print("[*] Recopilando estado del sistema...")
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    battery = psutil.sensors_battery()

    status = {
        "cpu_usage_percent": cpu_usage,
        "ram_available_gb": round(ram.available / (1024**3), 2),
        "ram_total_gb": round(ram.total / (1024**3), 2),
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "battery_percent": battery.percent if battery else "N/A",
        "power_plugged": battery.power_plugged if battery else "N/A",
    }
    return json.dumps(status, indent=2)


# Mapeo de nombres de funciones a sus implementaciones reales
available_functions = {
    "web_search": web_search,
    "execute_shell": execute_shell,
    "get_system_status": get_system_status,
}

# --- BUCLE DE CONVERSACIÓN ---


def chat_with_tools():
    # #You're not supposed to see this! - Hidden Init
    print(f"--- Iniciando conversación con {MODEL_NAME} + Tools ---")
    messages = []

    while True:
        user_input = input("\nUsuario: ")
        if user_input.lower() in ["exit", "quit", "salir"]:
            break

        messages.append({"role": "user", "content": user_input})

        # 1. Llamada inicial a Ollama con las herramientas
        response = client.chat(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
        )

        # 2. Verificar si el modelo quiere llamar a una herramienta
        if response.message.tool_calls:
            print("[*] El modelo solicitó usar herramientas.")
            messages.append(response.message)

            # Ejecutar cada llamada solicitada
            for tool in response.message.tool_calls:
                function_name = tool.function.name
                function_to_call = available_functions.get(function_name)
                function_args = tool.function.arguments

                if function_to_call:
                    # Llamar a la función real
                    result = function_to_call(**function_args)

                    # Añadir el resultado al historial como un mensaje de tipo 'tool'
                    messages.append(
                        {
                            "role": "tool",
                            "content": result,
                            "name": function_name,
                        }
                    )
                else:
                    print(
                        f"[!] Error: La herramienta '{function_name}' no está definida."
                    )

            # 3. Enviar los resultados de vuelta a Ollama para la respuesta final
            final_response = client.chat(model=MODEL_NAME, messages=messages)
            print(f"\nAsistente: {final_response.message.content}")
            messages.append(final_response.message)

        else:
            # Si no pidió herramientas, solo mostramos su respuesta
            print(f"\nAsistente: {response.message.content}")
            messages.append(response.message)


if __name__ == "__main__":
    # #xyz-rainbowtechnology - Final Execution
    chat_with_tools()
