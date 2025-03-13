# setup.py
from setuptools import setup, find_packages

setup(
    name="financial_tracker",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "motor>=3.2.0",
        "pymongo>=4.4.1",
        "python-dotenv>=1.0.0",
        "pydantic>=1.10.11",
        "numpy>=1.25.1",
        "python-dateutil>=2.8.2",
    ],
    author="Seu Nome",
    author_email="seu.email@exemplo.com",
    description="Sistema de contabilidade financeira pessoal com interface natural por linguagem humana",
    keywords="finanças, contabilidade, linguagem natural, mongodb, clean architecture",
    url="https://github.com/seu-usuario/financial-tracker",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)