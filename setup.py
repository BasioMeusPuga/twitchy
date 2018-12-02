import sys
from setuptools import setup

MAJOR_VERSION = '3'
MINOR_VERSION = '4'
MICRO_VERSION = '0'
VERSION = "{}.{}.{}".format(MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION)

if sys.argv[-1] == 'test':
    from twitchy import twitchy_config
    twitchy_config.ConfigInit(True)

setup(name='twitchy',
      version=VERSION,
      description="Command line streamlink wrapper for twitch.tv",
      url='https://github.com/BasioMeusPuga/twitchy',
      author='BasioMeusPuga',
      author_email='disgruntled.mob@gmail.com',
      license='GPLv3',
      packages=['twitchy'],
      classifiers=[
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Unix',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.6',
          'Development Status :: 5 - Production/Stable',
          'Topic :: Multimedia :: Video :: Display'
      ],
      zip_safe=False,
      entry_points={'console_scripts': ['twitchy = twitchy.__main__:main']},
      platforms='any')
