#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
import netifaces
import socket
_LOGGER = logging.getLogger(__name__)


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
        _LOGGER.debug("Interfaces found: %s", self.ip_to_interface)
        _LOGGER.debug("Looking for IP: %s", ip)

        mac_addr = None
        if_name = self.ip_to_interface.get(ip)

        try:
            link = netifaces.ifaddresses(if_name)[netifaces.AF_LINK]
        except (KeyError, TypeError):
            _LOGGER.warning('Could not determine MAC for: %s', if_name)
        else:
            _LOGGER.debug("Found link: %s", link)
            if len(link) > 1:
                _LOGGER.warning(
                    'Conflict: Multiple interfaces found for IP: %s!', ip)
            mac_addr = link[0].get('addr')
        return mac_addr
