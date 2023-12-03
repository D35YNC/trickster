#!/usr/bin/python3

from setuptools import setup, find_packages
from trickster.trickster import __version__

if __name__ == '__main__':
    setup(name="trickster",
          version=__version__,
          description="Trickster is an encapsulator of protocols into each other",
          long_description=open("./README.md", 'r').read(),
          long_description_content_type="text/markdown",
          author="D35YNC",
          url="https://github.com/d35ync/trickster",
          classifiers=[  # "Development Status :: 5 - Production/Stable",
                       "Environment :: Console",
                       "License :: OSI Approved :: MIT License",
                       "Topic :: Security",
                       "Programming Language :: Python",
                       "Programming Language :: Python :: 3.10"],
          python_requires=">=3.10",
          packages=find_packages(),
          install_requires=[line.strip() for line in open("./requirements.txt", "r").readlines()],
          entry_points={"console_scripts": ["trickster-tunnel = trickster.tunnel.__main__:tunnel_main",
                                            "trickster-client = trickster.client.__main__:client_main",
                                            "trickster-server = trickster.server.__main__:server_main"]})
