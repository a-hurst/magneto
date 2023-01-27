from setuptools import setup

setup(
	name='magneto',
	version='0.0.1',
	description='A Python library for controlling Magstim TMS hardware.',
	author='Austin Hurst',
	author_email='mynameisaustinhurst@gmail.com',
	url='http://github.com/a-hurst/magneto',
	packages=['magneto'],
	python_requires='>=3.6',
	install_requires=[
		'pyserial>=3.4',
	],
)
