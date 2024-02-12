# mikro-manager

[![codecov](https://codecov.io/gh/jhnnsrs/gucker/branch/master/graph/badge.svg?token=UGXEA2THBV)](https://codecov.io/gh/jhnnsrs/gucker)
[![PyPI version](https://badge.fury.io/py/gucker.svg)](https://pypi.org/project/gucker/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://pypi.org/project/gucker/)
![Maintainer](https://img.shields.io/badge/maintainer-jhnnsrs-blue)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/gucker.svg)](https://pypi.python.org/pypi/gucker/)
[![PyPI status](https://img.shields.io/pypi/status/gucker.svg)](https://pypi.python.org/pypi/gucker/)

mikro-manager allows you to control micro-manager through Arkitekt


## Idea

This is a standalone desktop application that allows you to control micro-manager and your microscope through Arkitekt. It is build on top of the [pycromanager](https://pycro-manager.readthedocs.io/en/latest/) package, abstracting the micro-manager api to be used by [Arkitekt](https://arkitekt.live)


## Prerequisites

To use this application, you need to have micro-manager installed on your computer. You can download micro-manager from [here](https://micro-manager.org/). Importantly you need to make sure that your micro-manager installation matches the version of the mikro-manager python package. Currently
(version 2.0.1 2023.05.23 (later versions might work as well))


You also need to have Arkitekt installed on a network accessible computer. To learn more about Arkitekt, visit the documentation [here](https://arkitekt.live).

## Installation

The easiest way to install this application is via their pre-built binaries. You can download the latest release from the [releases page](https://github.com/arkitektio-apps/gucker/releases).

Alternatively, you can install this application via pip. 

```bash
pip install mikro-manager
```

## Usage

Before you start the application, make sure that you have micro-manager installed and that you have a working configuration. And ensure that micro-manager is running and that the "Micro-Manager Server" is running. You can have a look at the [pycromanager](https://pycro-manager.readthedocs.io/en/latest/) documentation to learn more about how to set up micro-manager.



Start the Application by running the installed binary or by running the following command in your terminal (within the environment where you installed mikro-manager).

```bash
mikro-manager
```

Now you can connect to your Arkitekt server through the Provide Button. This is similiar to all Arkitekt applications. 



