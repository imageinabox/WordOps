
import glob
import os
import sys

from setuptools import find_packages, setup

# read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    LONG = f.read()

conf = []
templates = []

for name in glob.glob('config/plugins.d/*.conf'):
    conf.insert(1, name)

for name in glob.glob('wo/cli/templates/*.mustache'):
    templates.insert(1, name)

if os.geteuid() == 0:
    if not os.path.exists('/var/log/wo/'):
        os.makedirs('/var/log/wo/')

    if not os.path.exists('/var/lib/wo/tmp/'):
        os.makedirs('/var/lib/wo/tmp/')

setup(name='wordops',
      version='3.16.3',
      description='An essential toolset that eases server administration',
      long_description=LONG,
      long_description_content_type='text/markdown',
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Development Status :: 5 - Production/Stable",
          "Environment :: Console",
          "Natural Language :: English",
          "Topic :: System :: Systems Administration",
      ],
      keywords='nginx automation wordpress deployment CLI',
      author='WordOps',
      author_email='contact@wordops.io',
      url='https://github.com/imageinabox/WordOps',
      license='MIT',
      project_urls={
          'Documentation': 'https://docs.wordops.net',
          'Forum': 'https://community.wordops.net',
          'Source': 'https://github.com/imageinabox/WordOps',
          'Tracker': 'https://github.com/imageinabox/WordOps/issues',
      },
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests',
                                      'templates']),
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      python_requires='>=3.4',
      install_requires=[
          # Required to build documentation
          # "Sphinx >= 1.0",
          # Required to function
          'cement == 2.10.14',
          'pystache',
          'pynginxconfig',
          'PyMySQL >= 1.0.2',
          'psutil',
          'sh',
          'SQLAlchemy == 1.4.54',
          'requests',
          'distro',
          'argcomplete',
          'colorlog',
      ],
      extras_require={  # Optional
          'testing': ['nose', 'coverage'],
      },
      data_files=[('/etc/wo', ['config/wo.conf']),
                  ('/etc/wo/plugins.d', conf),
                  ('/usr/lib/wo/templates', templates),
                  ('/etc/bash_completion.d/',
                   ['config/bash_completion.d/wo_auto.rc']),
                  ('/usr/share/man/man8/', ['docs/wo.8'])],
      setup_requires=[],
      entry_points="""
          [console_scripts]
          wo = wo.cli.main:main
      """,
      namespace_packages=[],
      )