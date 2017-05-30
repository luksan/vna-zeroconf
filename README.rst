============
vna_zeroconf
============

This utility uses the zeroconf Python library to send out DNS-SD information about a measurement instrument.

If it is not run directly on the instrument a file named `vna_mdns_ip.txt` can be placed next to the executable, the file should contain one line with the IP address of the instrument.

Development
-----------

Run `pyinstaller --onefile vna_zeroconf.py` to build a standalone executable.
