"""Setup script for cli-anything-figma."""
from setuptools import setup, find_packages

setup(
    name="cli-anything-figma",
    version="1.0.0",
    description="Figma CLI for AI Agents — Agent-native interface to the Figma platform",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="CLI-Anything Community",
    license="MIT",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
        "requests>=2.31.0",
        "rich>=13.0.0",
        "prompt-toolkit>=3.0.0",
        "tabulate>=0.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-mock>=3.10.0",
            "responses>=0.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cli-anything-figma=cli_anything_figma.cli:main",
            "figma-cli=cli_anything_figma.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Intended Audience :: Developers",
    ],
)
