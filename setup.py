import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pimondrian",
    version="1.1.0",
    author="Allan Psicobyte",
    author_email="psicobyte@gmail.com",
    description="Draw Paintings as Mondrian",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/psicobyte/pimondrian_module",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or "
        "later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Topic :: Artistic Software",
    ],
    keywords=['mondrian', 'art', 'painting'],
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": ["pimondrian = pimondrian.__main__:main"]
    },
    package_data={
        'pimondrian': ['colors.txt', '10000pi.txt'],
    },
    install_requires=['pillow'],
    python_requires='>=3.6'
)
