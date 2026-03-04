"""
OcularLimbs Setup Configuration
"""

from setuptools import setup, find_packages
import os

# 读取 README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取依赖
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ocularlimbs",
    version="0.1.0",
    author="Claude",
    author_email="noreply@anthropic.com",
    description="Eyes and Hands for AI - Computer Vision and Automation Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anthropics/ocularlimbs",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ocularlimbs=ocularlimbs.agent:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
