from setuptools import setup

setup(
    name="opencode-dashboard",
    version="2.0.0",
    description="Terminal token consumption dashboard for AI CLI agents. Mahjong tile heatmaps, cross-platform (Win/Mac/Linux), supports OpenCode, Claude Code, Codex.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Ken",
    url="https://github.com/Ken1301225/opencode-dashboard",
    py_modules=["opencode_dashboard"],
    entry_points={
        "console_scripts": [
            "opencode-dashboard=opencode_dashboard:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
    ],
)