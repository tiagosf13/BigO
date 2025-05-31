from setuptools import setup


with open('README.rst') as readme_file:
    long_description = readme_file.read()


setup(
    name='BigO',
    version='0.11.0',
    description='Empirical estimation of time complexity from execution time. Extended and actively maintained fork of big_O (Python complexity analysis)',
    author='Tiago Fonseca',
    author_email='t.fonseca@ua.pt',
    url='https://github.com/tiagosf13/BigO',
    license='LICENSE.txt',
    notice='NOTICE.md',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    packages=['big_o', 'big_o.test'],
    install_requires=['numpy', 'pydantic', 'typing', 'random', 'exectimeit', 'ast']
)
