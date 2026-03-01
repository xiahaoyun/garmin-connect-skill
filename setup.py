#!/usr/bin/env python3
"""
Garmin Connect Skill 安装脚本

使用方法:
    python3 setup.py install
    
或:
    pip3 install -e .
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="garmin-connect-skill",
    version="1.0.0",
    author="Haoyun",
    author_email="",
    description="Garmin Connect data retrieval skill for OpenClaw",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/haoyun/garmin-connect-skill",
    packages=find_packages(where="scripts"),
    package_dir={"": "scripts"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "garth>=0.4.46",
        "python-dotenv>=1.0.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "garmin-skill=garmin_skill:main",
        ],
    },
)
