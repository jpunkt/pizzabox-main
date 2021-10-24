import re
import ast

from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('pizzactrl/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))
    setup(
        name='raspibox-mc',
        version=version,
        description='raspberry pi controller for sound, light and motors',
        url='https://github.com/jpunkt/pizzabox-mc.git',
        author='jpunkt',
        author_email='johannes@arg-art.org',
        platforms='any',

        packages=[
            'pizzactrl',
            'pizzactrl.sounds'
        ],

        install_requires=[
            'gpiozero',
            'picamera',
            'click',
            'sounddevice',
            'soundfile',
            'scipy',
            'pyserial'
        ],

        entry_points='''
            [console_scripts]
            pizzabox=pizzactrl.main:main
            pizza-rewind=pizzactrl.main:rewind
        ''',

        include_package_data=True

    )

