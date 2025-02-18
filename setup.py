import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='autodoc-django',
    version='0.1.1',
    author='Marcos Gomes',
    author_email='gomes.marcosjf@gmail.com',
    description="Provide an automatic documentation for Django's Apps",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/GomesMarcos/autodoc-django',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=[
        'asgiref>=3.8.1',
        'Django>=4.2.19',
        'python-decouple>=3.8',
        'ruff>=0.7.1',
        'sqlparse>=0.5.1',
    ],
)
