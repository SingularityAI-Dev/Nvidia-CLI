"""Legacy setup.py for editable installs."""

from setuptools import setup, find_packages

setup(
    name="nv-cli",
    version="7.0.0",
    packages=find_packages(),
    install_requires=[
        "typer>=0.12.0",
        "rich>=13.0.0",
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
        "pathspec>=0.12.0",
        "prompt-toolkit>=3.0.0",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "nv=nv_cli.cli:app",
        ],
    },
    description="NVIDIA AI CLI Tool v7.0 - OpenClaw-inspired multi-agent framework",
    author="NVIDIA CLI",
)