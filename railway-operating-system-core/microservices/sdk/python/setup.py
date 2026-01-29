from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="railway-os-sdk",
    version="1.0.0",
    author="Railway Operating System Team",
    author_email="admin@railwayos.com",
    description="Python SDK for Railway Operating System microservices platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/railway-os/sdk-python",
    packages=find_packages(),
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
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=1.8.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.15.0",
            "black>=21.0.0",
            "isort>=5.0.0",
            "flake8>=3.9.0",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    keywords="railway transportation api sdk microservices",
    project_urls={
        "Bug Reports": "https://github.com/railway-os/sdk-python/issues",
        "Source": "https://github.com/railway-os/sdk-python",
        "Documentation": "https://railway-os-sdk.readthedocs.io/",
    },
)