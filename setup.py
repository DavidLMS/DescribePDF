from setuptools import setup, find_packages

# Read requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="describepdf",
    version="0.1.0",
    description="Convert PDFs to detailed Markdown descriptions using Vision-Language Models",
    author="David Romero",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'describepdf=describepdf.cli:run_cli',
            'describepdf-web=describepdf.ui:launch_app',
        ],
    },
    python_requires='>=3.8',
)