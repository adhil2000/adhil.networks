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
        return (self.cost < other.cost)

    def __eq__(self, other):
        return (self.cost == other.cost)


class LSrouter(Router):
    """Link state routing and forwarding implementation"""

    def __init__(self, addr, heartbeatTime):
        Router.__init__(self, addr, heartbeatTime)  # initialize superclass - don't remove
        self.graph = {}  # A dictionary with KEY = router
        # VALUE = a list of lists of all its neighbor routers/clients and the cost to each neighbor
        # {router: [[neighbor_router_or_client, cost]]}
        self.graph[self.addr] = []
        """add your own class fields and initialization code here"""
        # --------------
        self.paths = self.dijkstra()
        self.seq = 1
        self.seqvec = {}
        self.seqvec[self.addr] = self.seq

    def handlePacket(self, port, packet):
        """process incoming packet"""
        """parameters:
        port : the router port on which the packet was received
        packet : the received packet"""

        if (packet.isControl() == True):
            data = loads(packet.content)
            inseq = int(packet.dstAddr)
            if packet.srcAddr in self.seqvec.keys():
                if inseq <= self.seqvec[packet.srcAddr]:
                    return
            self.seqvec[packet.srcAddr] = inseq

            if self.addr in data.keys():
                data.pop(self.addr)
                data[self.addr] = []
                for j in self.links:
                    data[self.addr].append([self.links[j].get_e2(self.addr), self.links[j].get_cost()])
            self.graph[packet.srcAddr] = data[packet.srcAddr]

            self.paths = self.dijkstra()

            for ports in self.links:
                self.send(ports, packet)

        else:
            hop = -1
            p = -1
            for i in self.paths:
                if i.addr == packet.dstAddr:
                    hop = i.next_hop

            if hop != -1:
                for ports in self.links:
                    if self.links[ports].get_e2(self.addr) == hop:
                        p = ports

            if p != -1:
                self.send(p, packet)

    def handleNewLink(self, port, endpoint, cost):
        """a new link has been added to router port and initialized, or an existing
        link cost has been updated. This information has already been updated in the
        "links" data structure in router.py. Implement any routing/forwarding action
        that you might want to take under such a scenario"""
        """parameters:
        port : router port of the new link / the existing link whose cost has been updated
        endpoint : the node at the other end of the new link / the exisitng link whose cost has been updated
        (this end of the link is self.addr)
        cost : cost of the new link / new cost of the exisitng link whose cost has been updated"""
        for neighbor in self.graph[self.addr]:
            if neighbor[0] == endpoint:
                self.graph[self.addr].remove(neighbor)
        self.graph[self.addr].append([endpoint, cost])

        self.dijkstra()
        self.handlePeriodicOps()

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

    def handlePeriodicOps(self):
        """handle periodic operations. This method is called every heartbeatTime.
        You can change the value of heartbeatTime in the json file"""
        content = dumps(self.graph)
        self.graph.pop(self.addr)
        self.graph[self.addr] = []
        for j in self.links:
            self.graph[self.addr].append([self.links[j].get_e2(self.addr), self.links[j].get_cost()])
        packet = Packet(Packet.CONTROL, str(self.addr), str(self.seq), content)
        for ports in self.links:
            self.send(ports, packet)
        self.seq = self.seq + 1
        # if self.addr == "6" :
        # print(self.graph)
        pass

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