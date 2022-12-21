# The code is subject to Purdue University copyright policies.
# DO NOT SHARE, DISTRIBUTE, OR POST ONLINE
#

import sys
import time
from collections import defaultdict
from router import Router
from packet import Packet
from json import dumps, loads


class DVrouter(Router):
    """Distance vector routing and forwarding implementation"""

    # DONE
    def __init__(self, addr, heartbeatTime, infinity):
        Router.__init__(self, addr, heartbeatTime)  # initialize superclass - don't remove
        self.infinity = infinity
        """add your own class fields and initialization code here"""
        self.graph = {self.addr: [self.addr, 0]}  # Initialize Graph

    def handlePacket(self, port, packet):
        """process incoming packet"""
        """parameters:
        port : the router port on which the packet was received
        packet : the received packet"""
        # DATA Packet
        if packet.isData():
            # Check Infinity and update accordingly
            self.handlePeriodicOps()
            # If destination is found within graph
            if packet.dstAddr in self.graph:
                temp_port = -1
                # Send to all other ports
                for ports in self.links:
                    # Piazza Post @191
                    if self.links[ports].get_e2(self.addr) == self.graph[packet.dstAddr][0]:
                        temp_port = ports
                # Edge Case??
                if temp_port != port:
                    self.send(temp_port, packet)

        # CONTROL packet
        if packet.isControl():
            # Load content
            data = loads(packet.content)
            # Copy previous graph
            prev_graph = self.graph
            for routers in data:
                # Check current router address matches own
                if data[routers][0] != self.addr:
                    if routers in self.graph.keys():
                        # Piazza Post @191
                        if (self.links[port].get_e2(self.addr) == self.graph[routers][0]) or (
                                self.graph[routers][1] >= (data[routers][1] + self.links[port].get_cost())):
                            current_address = self.links[port].get_e2(self.addr)
                            current_cost = data[routers][1] + self.links[port].get_cost()
                            self.graph[routers] = [current_address, current_cost]
                    else:
                        current_address = self.links[port].get_e2(self.addr)
                        current_cost = data[routers][1] + self.links[port].get_cost()
                        self.graph[routers] = [current_address, current_cost]

            # Iterate through routers
            for routers in self.graph:
                # Max Infinity Threshold
                if self.graph[routers][1] >= self.infinity:
                    self.graph[routers] = [None, self.infinity - 1]

            # Check if Graphs match
            if prev_graph != self.graph:
                # Send on all other ports
                for ports in self.links:
                    if ports != port:
                        self.send(ports, packet)

    # DONE
    # Piazza Post @169
    # Every time a new link is created handleNewlink gets called, even the initial links.
    # For example, in 01.json, when link 1-2 is created handleNewLink gets called.
    def handleNewLink(self, port, endpoint, cost):
        """a new link has been added to router port and initialized, or an existing
        link cost has been updated. This information has already been updated in the
        "links" data structure in router.py. Implement any routing/forwarding action
        that you might want to take under such a scenario"""
        """parameters:
        port : router port of the new link / the existing link whose cost has been updated
        endpoint : the node at the other end of the new link / the existing link whose cost has been updated
        (this end of the link is self.addr)
        cost : cost of the new link / new cost of the existing link whose cost has been updated"""
        # Update Endpoints
        self.graph[endpoint] = [endpoint, cost]
        self.handlePeriodicOps()
        pass

    def handleRemoveLink(self, port, endpoint):
        """an existing link has been removed from the router port. This information
        has already been updated in the "links" data structure in router.py. Implement any 
        routing/forwarding action that you might want to take under such a scenario"""
        """parameters:
        port : router port from which the link has been removed
        endpoint : the node at the other end of the removed link
        (this end of the link is self.addr)"""
        for routers in self.graph:  # route niggas
            if self.graph[routers][0] == endpoint:
                self.graph[routers] = [endpoint, self.infinity]
        self.handlePeriodicOps()
        pass

    # DONE
    def handlePeriodicOps(self):
        """handle periodic operations. This method is called every heartbeatTime.
        You can change the value of heartbeatTime in the json file"""
        # Check Max Infinity Threshold
        for routers in self.graph:
            if self.graph[routers][1] >= self.infinity:
                self.graph[routers] = [None, self.infinity - 1]
        # Free Graph
        content = dumps(self.graph)
        # Set New Packet
        new_packet = Packet(2, str(self.addr), "0", content)
        # Send on all other ports
        for ports in self.links:
            self.send(ports, new_packet)
        pass
