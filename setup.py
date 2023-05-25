from setuptools import setup

setup(
    name='beets-tidal',
    version='0.1',
    description='beets plugin to use Tidal for metadata',
    long_description=open('README.md').read(),
    author='Alok Saboo',
    author_email='',
    url='https://github.com/arsaboo/beets-tidal',
    license='MIT',
    platforms='ALL',
    packages=['beetsplug'],
    install_requires=[
        'beets>=1.6.0',
        'tidalapi',
        'requests',
        'pillow',
    ],
)
