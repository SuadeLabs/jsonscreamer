from setuptools import setup, find_packages

setup(
    name="json-screamer",
    version="0.1",
    author="Oliver Margetts",
    packages=find_packages(),
    description="Fast JSON Schema Validator",
    install_requires=[],
    extras_require={"tests": ["black", "flake8", "pytest"]},
)
