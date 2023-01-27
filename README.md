# Magneto

Magneto is a Python library for controlling Magstim TMS hardware remotely over the serial port.

**NOTE: This is alpha software, and is still in active development.**

Magneto currently only supports Magstim 200 and BiStim hardware, but support for Rapid simulators may be added at a later date.


## Installation

To install the latest develmopent version of magneto, run the following command in a terminal:

```
pip install git+https://github.com/a-hurst/magneto.git
```

The only dependency for magneto (other than a Magstim 200 or BiStim) is a recent version of PySerial, which will be installed automatically when running the command above.