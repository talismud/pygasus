import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pygasus",
    version="0.4",
    author="Vincent Le Goff",
    author_email="vincent.legoff.srs@gmail.com",
    description="A lightweight, Sqlite ORM built on top of Pydantic.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/talismud/pygasus/",
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
    install_requires = [
        "pydantic==1.8.2",
        "SQLAlchemy==1.4.22",
     ],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
