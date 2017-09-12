#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='check_puppet_nodesync',
	version='0.10',
	description='Nagios Check for Puppet Node synchronization using PuppetDB',
	author='Dr. Torge Szczepanek',
	author_email='info@cygnusnetworks.de',
	license='Apache 2.0',
	py_modules=['check_puppet_nodesync'],
	entry_points={'console_scripts': ['check_puppet_nodesync = check_puppet_nodesync:main']},
	install_requires=['nagiosplugin', 'pypuppetdb'])