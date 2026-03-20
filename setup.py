from setuptools import setup

setup(
    name="ollama-run",
    version="4.3.0",
    py_modules=["main"],
    install_requires=[
        "ollama",
        "psutil",
        "duckduckgo-search",
    ],
    entry_points={
        "console_scripts": [
            "ollama-run=main:main",
        ],
    },
)
