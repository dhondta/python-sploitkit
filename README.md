[![PyPi](https://img.shields.io/pypi/v/sploitkit.svg)](https://pypi.python.org/pypi/sploitkit/)
[![Read The Docs](https://readthedocs.org/projects/sploitkit/badge/?version=latest)](https://sploitkit.readthedocs.io/en/latest/?badge=latest)
[![Known Vulnerabilities](https://snyk.io/test/github/dhondta/sploitkit/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/dhondta/sploitkit?targetFile=requirements.txt)
[![Requirements Status](https://requires.io/github/dhondta/sploitkit/requirements.svg?branch=master)](https://requires.io/github/dhondta/sploitkit/requirements/?branch=master)
[![Python Versions](https://img.shields.io/pypi/pyversions/sploitkit.svg)](https://pypi.python.org/pypi/sploitkit/)
[![License](https://img.shields.io/pypi/l/sploitkit.svg)](https://pypi.python.org/pypi/sploitkit/)
[![Beerpay](https://img.shields.io/beerpay/hashdog/scrapfy-chrome-extension.svg)](https://beerpay.io/dhondta/sploitkit)
[![Donate](https://img.shields.io/badge/donate-paypal-orange.svg)](https://www.paypal.me/dhondta)


# SploitKit

This toolkit is aimed to easilly build framework consoles in a Metasploit-like style. It provides a comprehensive interface to define CLI commands, modules and models for its storage database.

## Quick Start

### Setup

```
pip install -r requirements
```

### Create a project

```sh
$ sploitkit-new my_app
```

### Usage



```python
#!/usr/bin/python3
from sploitkit import FrameworkConsole


if __name__ == '__main__':
    MyRootConsole("my_app").start()
```
