#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
import netifaces
import socket


class NetworkInformation(object):
    """Util for getting a interface' ip to a specific host and the corresponding mac address."""

    def __init__(self):
        self.ip_to_interface = self.__buildIpToInterfaceDict()

    def __buildIpToInterfaceDict(self):
        """Build a map of IPv4-Address to Interface-Name (like 'eth0')"""
        map = {}
        for interface in netifaces.interfaces():
            try:
                ifInfo = netifaces.ifaddresses(interface)[netifaces.AF_INET]
                for addrInfo in ifInfo:
                    addr = addrInfo.get('addr')
                    if addr:
                        map[addr] = interface
            except Exception:
                pass
        return map

    def getLocalIp(self, targetHost, targetPort):
        """Gets the local ip to reach the given ip.
        That can be influenced by the system's routing table.
        A socket is opened and closed immediately to achieve that."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((targetHost, targetPort))
        except Exception as e:
            logging.exception("Cannot create socket to target " + targetHost + ":" + targetPort)
        else:
            ip = s.getsockname()[0]
            s.close()
        return ip

    def getLocalMacForIp(self, ip):
        """Get the mac address for that given ip."""
        if not self.ip_to_interface[ip]:
            raise ValueError('could not find interface for local ip ' + ip)
        link = netifaces.ifaddresses(self.ip_to_interface[ip])[netifaces.AF_LINK]
        if len(link) > 1:
            raise ValueError('Found more than one interface with that ip, conflict!')
        return link[0].get('addr')