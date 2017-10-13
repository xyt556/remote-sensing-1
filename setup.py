"""
Remote Sensing!.
"""

from codecs import open
from os.path import abspath, dirname, join
from setuptools import find_packages, setup

this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.md'), encoding='utf-8') \
        as package_readme_file:
    long_description = package_readme_file.read()


setup(
    name='remote-sensing',
    version=__version__,
    description='Remote Sensing',
    long_description=long_description,
    url='https://github.com/barnabygordon/remote-sensing',
    author='Barney Gordon',
    author_email='barney@hummingbirdtech.com',
    license='copyright',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: Copyright',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='imageprocessing',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=[
        'folium',
        'gdal',
        'geopandas',
        'matplotlib',
        'numpy',
        'pandas',
        'pillow',
        'pyproj',
        'scipy',
        'shapely',
        'sklearn',
        'scikit-image',
        'tqdm',
    ],
    namespace_packages=['remotesensing']
)