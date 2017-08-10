# -*- coding: utf-8 -*-
"""

@author: Lukas Sandström
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import socket
import sys
from time import sleep
import telnetlib
from pprint import pprint

import zeroconf
from zeroconf import ServiceInfo, Zeroconf

# Python 2 compatibility
try:
    import __builtin__
    input = getattr(__builtin__, 'raw_input')
except (ImportError, AttributeError):
    pass

_zc_list = []


def get_vna_idn(host):
    try:
        tel = telnetlib.Telnet(host, 5025, 5)
    except socket.timeout:
        return None
    except socket.error:
        return None

    tel.write(b"*IDN?\n")
    idn = tel.read_until("\n", 5).strip()
    tel.close()

    (vendor, instr, id_, fw_rev) = idn.split(",")
    ret = {'ip': host, 'Manufacturer': vendor, 'instr': instr, 'id': id_, 'FirmwareVersion': fw_rev, 'IDN': idn}

    if vendor == "Rohde-Schwarz" or vendor == "Rohde&Schwarz":
        ret['SerialNumber'] = id_[-6:]
        ret['Manufacturer'] = "Rohde & Schwarz"
        ret['MaterialNumber'] = "%s.%sK%s" % (id_[:4], id_[4:8], id_[8:10])
    else:
        ret['serial'] = id_
    return ret


def init_zeroconf():
    """
    Sets up a Zeroconf instance for each network interface.
    """
    for addr in zeroconf.get_all_addresses(socket.AF_INET):
        _zc_list.append((addr, Zeroconf([addr])))


def register_vna_service(idn):
    fqdn = idn['instr'].split("-")[0] + "-" + idn['SerialNumber'] + ".local."
    idn['fqdn'] = fqdn
    service_type = "_vxi-11._tcp.local."
    service_name = idn['Manufacturer'] + " " + idn['instr'] + " #" + idn['SerialNumber'] + "." + service_type
    print("Registering service " + service_name)
    pprint(idn)
    for (addr, zc) in _zc_list:
        print("Registering", addr)
        orig_ip = idn['ip']
        if idn['ip'] != "localhost" and idn['ip'] != "127.0.0.1":
            addr = idn['ip']
        else:
            idn['ip'] = addr
        info = ServiceInfo(service_type,
                           service_name,
                           socket.inet_aton(addr), 5025, 0, 0,
                           idn, fqdn)
        zc.register_service(info, allow_name_change=False)
        idn['ip'] = orig_ip


def unregister_services():
    for (_, zc) in _zc_list:
        zc.unregister_all_services()
        zc.close()


def main():
    vna_ip = "localhost"
    try:
        print("Checking for intrument ip in vna_mdns_ip.txt")
        with open(b'vna_mdns_ip.txt', b'r') as f:
            vna_ip = f.readline().strip()
            print("Found:", vna_ip)
    except IOError:
        print("No file found, using %s." % vna_ip)

    idn = None
    try:
        while idn is None:
            idn = get_vna_idn(vna_ip)
            if not idn:
                print("Waiting for VNA *IDN? from", vna_ip)
                sleep(1)
    except KeyboardInterrupt:
        sys.exit(1)

    init_zeroconf()

    register_vna_service(idn)

    input("Press enter to unregister")
    print("Unregistering...", end="")
    unregister_services()
    print("done.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
