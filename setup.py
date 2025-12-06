from setuptools import setup, find_packages

setup(
    name="ums-arsip",
    version="0.1.0",
    description="Custom Django Storage backend and FileField for UMS ARSIP API integration",
    author="Muhammad Hammam Islami",
    author_email="mhi595@ums.ac.id",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "django>=1.11",
        "requests>=2.19",
    ],
    keywords=["django", "storage", "filefield", "arsip"],
    url="https://github.com/mhi595/ums-arsip",
)
