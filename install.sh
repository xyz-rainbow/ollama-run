#!/bin/bash
echo "--- Instalando Rainbow Ollama-Run (Universal) ---"
pip install . --break-system-packages 2>/dev/null || pip install .
echo "¡Instalación completada! Escribe 'ollama-run' para empezar."
