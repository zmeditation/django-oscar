"""
Installation script:

To release a new version to PyPi:
- Ensure the version is correctly set in oscar.__init__.py
- Run: python setup.py sdist upload
"""

from setuptools import setup
from setuptools import find_packages

from oscar import get_version

setup(name='django-oscar',
      version=get_version().replace(' ', '-'),
      url='https://github.com/tangentlabs/django-oscar',
      author="Tangent Labs",
      author_email="david.winterbottom@tangentlabs.co.uk",
      description="A domain-driven e-commerce framework for Django 1.3+",
      long_description=open('README.rst').read(),
      license='BSD',
      platforms=['linux'],
      packages=['oscar',
                'oscar.apps',
                'oscar.apps.address',
                'oscar.apps.analytics',
                'oscar.apps.analytics.management',
                'oscar.apps.analytics.management.commands',
                'oscar.apps.basket',
                'oscar.apps.basket.templatetags',
                'oscar.apps.catalogue',
                'oscar.apps.catalogue.templatetags',
                'oscar.apps.catalogue.management',
                'oscar.apps.catalogue.management.commands',
                'oscar.apps.catalogue.reviews',
                'oscar.apps.checkout',
                'oscar.apps.customer',
                'oscar.apps.customer.templatetags',
                'oscar.apps.discount',
                'oscar.apps.dynamic_images',
                'oscar.apps.dynamic_images.templatetags',
                'oscar.apps.offer',
                'oscar.apps.order',
                'oscar.apps.order_management',
                'oscar.apps.partner',
                'oscar.apps.partner.management',
                'oscar.apps.partner.management.commands',
                'oscar.apps.partner.tests',
                'oscar.apps.payment',
                'oscar.apps.payment.datacash',
                'oscar.apps.payment.tests',
                'oscar.apps.promotions',
                'oscar.apps.promotions.templatetags',
                'oscar.apps.reports',
                'oscar.apps.search',
                'oscar.apps.shipping',
                'oscar.apps.voucher',
                'oscar.core',
                'oscar.core.logging',
                'oscar.forms',
                'oscar.templatetags',
                'oscar.test',
                'oscar.views',
                'oscar.models',],
      package_data={'oscar': ['README.rst',
                              'templates/basket/*.html',
                              'templates/catalogue/*.html',
                              'templates/checkout/*.html',
                              'templates/customer/*.html',
                              'templates/customer/history/*.html',
                              'templates/order_management/*.html',
                              'templates/promotions/*.html',
                              'templates/reports/*.html',
                              'templates/reviews/*.html',
                              'templates/search/*.html',
                              'templates/search/indexes/*/*.txt',],
                    'oscar.apps.address': ['fixtures/*'],
                    'oscar.apps.catalogue': ['fixtures/*'],
                    'oscar.apps.catalogue.reviews': ['fixtures/*'],
                    'oscar.apps.dynamic_images': ['test_fixtures/*'],
                    'oscar.apps.offer': ['fixtures/*'],
                    'oscar.apps.order': ['fixtures/*'],
                    'oscar.apps.partner': ['fixtures/*'],
                    'oscar.apps.search': ['fixtures/*'],
                    'oscar.apps.shipping': ['fixtures/*'],},
      install_requires=[
          'django-extra-views==0.1.0',
          'django-haystack>=1.2.0',
          'django-treebeard>=1.6.1',
          'sorl-thumbnail>=11.05.1',
          ],
      dependency_links = [
          'http://github.com/AndrewIngram/django-extra-views/tarball/master#egg=django-extra-views-0.1.0',
      ],
      # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: Unix',
                   'Programming Language :: Python']
      )
