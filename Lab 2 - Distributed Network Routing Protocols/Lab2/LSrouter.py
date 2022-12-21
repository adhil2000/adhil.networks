# The code is subject to Purdue University copyright policies.
# DO NOT SHARE, DISTRIBUTE, OR POST ONLINE
#

import sys
import time
from collections import defaultdict
from router import Router
from packet import Packet
from json import dumps, loads


class PQEntry:

    def __init__(self, addr, cost, next_hop):
        self.addr = addr
        self.cost = cost
        self.next_hop = next_hop

    def __lt__(self, other):
        return self.cost < other.cost

    def __eq__(self, other):
        return self.cost == other.cost


# Link State Routing Protocol
class LSrouter(Router):
    """Link state routing and forwarding implementation"""

    # DONE
    def __init__(self, addr, heartbeatTime):
        Router.__init__(self, addr, heartbeatTime)  # initialize superclass - don't remove
        self.graph = {}  # A dictionary with KEY = router
        # VALUE = a list of lists of all its neighbor routers/clients and the cost to each neighbor
        # {router: [[neighbor_router_or_client, cost]]}
        self.graph[self.addr] = []
        """add your own class fields and initialization code here"""
        self.paths = self.dijkstra()
        self.sequence = 1
        self.sequence_vector = {self.addr: self.sequence}

    # COMMENT
    # handlePacket
    def handlePacket(self, port, packet):
        """process incoming packet"""
        """parameters:
        port : the router port on which the packet was received
        packet : the received packet"""

        if packet.isData():
            hop, temp_port = -1, -1
            for j in self.paths:
                if j.addr == packet.dstAddr:
                    hop = j.next_hop

            if hop != -1:
                for ports in self.links:
                    if self.links[ports].get_e2(self.addr) == hop:  # Piazza Post @191
                        temp_port = ports

            if temp_port != -1:
                self.send(temp_port, packet)

        if packet.isControl():
            data = loads(packet.content)
            dest_addr = packet.dstAddr
            in_sequence = int(dest_addr)
            src_addr = packet.srcAddr
            if (src_addr in self.sequence_vector.keys()) and (in_sequence <= self.sequence_vector[src_addr]):
                return
            self.sequence_vector[src_addr] = in_sequence

            addr = self.addr
            if addr in data.keys():
                data.pop(addr)
                data[addr] = []
                for ports in self.links:
                    data[addr].append([self.links[ports].get_e2(addr), self.links[ports].get_cost()]) # Piazza Post @191
            self.graph[packet.srcAddr] = data[packet.srcAddr]

            self.paths = self.dijkstra()

            for ports in self.links:
                self.send(ports, packet)
    pass

    # DONE
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
        for neighbor in self.graph[self.addr]:
            if neighbor[0] == endpoint:
                self.graph[self.addr].remove(neighbor)
        self.graph[self.addr].append([endpoint, cost])
        self.dijkstra()
        self.handlePeriodicOps()
        pass

    # DONE
    def handleRemoveLink(self, port, endpoint):
        """an existing link has been removed from the router port. This information
        has already been updated in the "links" data structure in router.py. Implement any 
        routing/forwarding action that you might want to take under such a scenario"""
        """parameters:
        port : router port from which the link has been removed
        endpoint : the node at the other end of the removed link
        (this end of the link is self.addr)"""
        for neighbor in self.graph[self.addr]:
            if neighbor[0] == endpoint:
                self.graph[self.addr].remove(neighbor)
        self.dijkstra()
        self.handlePeriodicOps()
        pass

    # handlePeriodicOps
    def handlePeriodicOps(self):
        """handle periodic operations. This method is called every heartbeatTime.
        You can change the value of heartbeatTime in the json file"""
        content = dumps(self.graph)
        addr = self.addr
        self.graph.pop(addr)
        self.graph[addr] = []
        for ports in self.links:
            self.graph[addr].append([self.links[ports].get_e2(addr), self.links[ports].get_cost()]) # Piazza Post @191
        addr_str = str(addr)
        sequence_str = str(self.sequence)
        packet = Packet(2, addr_str, sequence_str, content)
        for ports in self.links:
            self.send(ports, packet)
        self.sequence = self.sequence + 1
        pass

    # DONE
    # Given Function for Dijkstra
    def dijkstra(self):
        """An implementation of Dijkstra's shortest path algorithm.
        Operates on self.graph datastructure and returns the cost and next hop to
        each destination node in the graph as a List (finishedQ) of type PQEntry"""
        priorityQ = []
        finishedQ = [PQEntry(self.addr, 0, self.addr)]
        for neighbor in self.graph[self.addr]:
            priorityQ.append(PQEntry(neighbor[0], neighbor[1], neighbor[0]))
        priorityQ.sort(key=lambda x: x.cost)

        while len(priorityQ) > 0:
            dst = priorityQ.pop(0)
            finishedQ.append(dst)
            if not (dst.addr in self.graph.keys()):
                continue
            for neighbor in self.graph[dst.addr]:
                # neighbor already exists in finishedQ
                found = False
                for e in finishedQ:
                    if e.addr == neighbor[0]:
                        found = True
                        break
                if found:
                    continue
                newCost = dst.cost + neighbor[1]
                # neighbor already exists in priorityQ
                found = False
                for e in priorityQ:
                    if e.addr == neighbor[0]:
                        found = True
                        if newCost < e.cost:
                            e.cost = newCost
                            e.next_hop = dst.next_hop
                        break
                if not found:
                    priorityQ.append(PQEntry(neighbor[0], newCost, dst.next_hop))

                priorityQ.sort(key=lambda x: x.cost)

        return finishedQ
