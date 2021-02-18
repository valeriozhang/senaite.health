# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.HEALTH
#
# Copyright 2017-2019 by it's authors

from setuptools import setup, find_packages


version = '1.2.4rc9'

setup(
    name='valer.health',
    version=version,
    description="Valer Health",
    long_description=open("README.rst").read() + "\n" +
    open("CHANGES.rst").read() + "\n",
    # Get more strings from
    # http://pypi.python.org/pypi?:action=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Zope2",
        "Programming Language :: Python",
    ],
    keywords=['lims', 'lis', 'senaite', 'opensource', 'health','Valer'],
    author="Valer Group LLC",
    author_email="valerio.zhang@valer.us",
    url="https://github.com/valeriozhang/senaite.health",
    
    license='GPLv2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['bika'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "archetypes.schemaextender",
        "valer.lims==1.3.4rc9",
        "valer.panic==1.0.1rc9",
    ],
    extras_require={
        'test': [
            'unittest2',
            'plone.app.testing',
        ]
    },
    entry_points="""
        # -*- Entry points: -*-
        [z3c.autoinclude.plugin]
        target = plone
        """,
)
