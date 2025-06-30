from setuptools import setup, find_packages
import os

# Read README
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

# Read version
def get_version():
    with open('rapidcaptcha/__init__.py', 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('"')[1]
    return '1.0.0'

setup(
    name="rapidcaptcha",
    version=get_version(),
    author="Galkurta",
    author_email="support@rapidcaptcha.xyz",
    description="Official Python SDK for RapidCaptcha API - Solve Turnstile and reCAPTCHA with high success rates",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/RapidCaptcha-SDK/RapidCaptcha-Python",
    project_urls={
        "Bug Tracker": "https://github.com/RapidCaptcha-SDK/RapidCaptcha-Python/issues",
        "Documentation": "https://app.rapidcaptcha.xyz",
        "Homepage": "https://app.rapidcaptcha.xyz",
        "API Documentation": "https://app.rapidcaptcha.xyz",
        "Source": "https://github.com/RapidCaptcha-SDK/RapidCaptcha-Python",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "async": ["aiohttp>=3.8.0"],
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=3.0.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
            "pre-commit>=2.15.0",
            "bandit>=1.7.0",
            "safety>=2.0.0",
        ],
        "test": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "pytest-mock>=3.6.0",
            "pytest-cov>=3.0.0",
            "responses>=0.18.0",
            "aioresponses>=0.7.0",
        ],
    },
    keywords=[
        "captcha",
        "turnstile", 
        "recaptcha",
        "cloudflare",
        "automation",
        "bot",
        "solver",
        "api",
        "bypass",
        "challenge",
        "python",
        "sdk",
        "rapidcaptcha",
    ],
    include_package_data=True,
    zip_safe=False,
)