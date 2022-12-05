import setuptools


with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="algofi-python-sdk",
    description="The official Algofi Python SDK",
    author="Algofi",
    author_email="founders@algofi.org",
    version="2.4.3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    project_urls={
        "Source": "https://github.com/Algofiorg/algofi-python-sdk",
    },
    packages=setuptools.find_packages(),
    python_requires=">=3.8",
    include_package_data=True,
)
