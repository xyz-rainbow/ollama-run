from setuptools import setup

setup(
    name="ollama-run",
    version="4.9.1",
    py_modules=["main"],
    install_requires=[
        "ollama",
        "psutil",
        "duckduckgo-search",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "ollama-run=main:main",
        ],
    },
)
