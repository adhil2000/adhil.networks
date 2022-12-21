# The code is subject to Purdue University copyright policies.
# DO NOT SHARE, DISTRIBUTE, OR POST ONLINE
#
import sys
import time
from switch import Switch
from link import Link
from client import Client
from packet import Packet


class STPswitch(Switch):
    """STP, MAC learning and MAC forwarding implementation"""

    # Piazza Post @85 Set Max Infinity to 20
    INFINITY_THRESHOLD = 20

    # DONE
    def __init__(self, addr, heartbeatTime):
        Switch.__init__(self, addr, heartbeatTime)  # initialize superclass - don't remove
        """add your own class fields and initialization code here"""
        self.addr = addr  # Address of switch
        self.links = {}  # Switch Links
        self.mac_addr = {}  # MAC Addresses
        self.view = (self.addr, 0, self.addr, self.addr)  # Each switch X maintains a view (R, cost(X, R), X, H):
        self.hop_cost = 0  # Hop Cost - "I'm very particular about the format" -  Adhil Akbar
        self.next_hop = 0  # Next Hop - obviously

    # DONE
    def handlePacket(self, port, packet):
        """process incoming packet"""

        # DONE
        if packet.isData():  # Check if Packet is DATA
            self.mac_addr[packet.srcAddr] = port  # Update Port of current Packet
            if packet.dstAddr == "X":
                # Switch X sends control packet (X, 0, X, X) to all its neighbors
                for ports in self.links:
                    link_status = self.links[ports].status  # Get Link Status
                    if (link_status == 1) and (ports != port):  # Is Active?
                        # "port = incoming port" - tHoMaS sMiTh
                        # Broadcast to all ports except incoming port
                        self.send(ports, packet)
            if packet.dstAddr != "X":
                if (packet.dstAddr in self.mac_addr) and (self.mac_addr[packet.dstAddr] != port):
                    self.send(self.mac_addr[packet.dstAddr], packet)
                else:
                    for ports in self.links:
                        link_status = self.links[ports].status  # Get Link Status
                        if (link_status == 1) and (ports != port):  # Is Active?
                            # "port = incoming port" - tHoMaS sMiTh
                            # Broadcast to all ports except incoming port
                            self.send(ports, packet)

        if packet.isControl():  # Check if Packet is CONTROL
            packet_view = packet.content.split()  # Split packet content
            packet_view = map(int, packet_view)  # Iterate packet_view into (int)
            packet_view = list(packet_view)  # Transform packet_view into list
            packet_source = int(packet.srcAddr)  # Packet Source Address
            view = list(map(int, self.view))  # View??
            address = int(self.addr)  # Address of Switch
            cost = int(self.links[port].get_cost())  # Cost of each Port

            # Lecture 9 stuff
            if packet_source == view[3]:
                if packet_view[0] < address:
                    # (R, cost(X, R), X, H) - for the stuff below
                    X1 = str(packet_view[0])
                    X2 = str(cost + packet_view[1])
                    X3 = packet.srcAddr
                    self.view = (X1, X2, self.addr, X3)  # make this stuff easier to read
                    self.next_hop = port
                else:
                    self.view = (self.addr, "0", self.addr, self.addr)
                    self.next_hop = 0
                self.handleNewLink(port, self.INFINITY_THRESHOLD, cost)
            # Case 2 : Advertisement from a switch not the current next hop to root (slide 9)
            else:
                # Update if smaller root advertised, i.e., R < R1
                if packet_view[0] < view[0]:
                    self.update_View(packet_view, packet, port, cost)  # Update View

                # Or, update if the same root (i.e., R1 == R) but smaller cost path to root via Y
                if (packet_view[0] == view[0]) & (view[1] > (packet_view[1] + cost)):
                    self.update_View(packet_view, packet, port, cost)  # Update View

                # Or, update if the same root (i.e., R1 == R) and same cost to root
                # (i.e, cost(X, R1) == cost(X, Y) + cost(Y, R)) but Y < Z (tie break)
                if (packet_view[0] == view[0]) & (view[1] == (packet_view[1] + cost)):
                    if packet_source < view[3]:
                        self.update_View(packet_view, packet, port, cost)  # Update View
            # Slide 12 helped with this
            #  X stops forwarding data packets on link X—Y (makes it “Inactive”) if and only if...
            # next hop of X != Y AND next hop of Y, i.e., H != X
            if (view[3] != packet_source) & (packet_view[3] != address):
                inactive_links = []
                self.links[port].status = 2  # set to INACTIVE?
                for addresses in self.mac_addr:
                    if self.mac_addr[addresses] == port:
                        inactive_links.append(addresses)
                for i in inactive_links:
                    self.mac_addr.pop(i)
            else:
                self.links[port].status = 1  # set to ACTIVE?

    # DONE
    # Cost??
    def handleNewLink(self, port, endpoint, cost):
        """a new link has been added to switch port and initialized, or an existing
        link cost has been updated. Implement any routing/forwarding action that
        you might want to take under such a scenario"""
        current_threshold = int(self.view[1])
        if current_threshold >= self.INFINITY_THRESHOLD:  # "self.20" - tHoMaS sMiTh
            self.view = (self.addr, "0", self.addr, self.addr)
        self.update_Neighbors()
        pass

    # DONDA
    def handleRemoveLink(self, port, endpoint):
        """an existing link has been removed from the switch port. Implement any
        routing/forwarding action that you might want to take under such a scenario"""
        if port == self.next_hop:
            self.view = (self.addr, "0", self.addr, self.addr)
        # Handle New Link after removal
        self.handleNewLink(port, endpoint, self.INFINITY_THRESHOLD)
        pass

    # DONE
    def handlePeriodicOps(self):
        """handle periodic operations. This method is called every heartbeatTime.
        You can change the value of heartbeatTime in the json file"""
        # Ask in TA office hours???????????????????????
        for ports in self.links:
            port_cost = int(self.links[ports].get_cost())
            if (self.next_hop == ports) and (self.hop_cost != port_cost):
                self.hop_cost = port_cost
                for i in self.links:
                    self.links[i].status = 1  # set to ACTIVE
        self.update_Neighbors()
        pass

    def update_View(self, packet_view, packet, port, cost):
        # no cap, this do be the same as above, aka (R, cost(X, R), X, H)
        X1 = str(packet_view[0])
        X2 = str(cost + packet_view[1])
        X3 = packet.srcAddr
        self.view = (X1, X2, self.addr, X3)
        self.next_hop = port
        self.links[port].status = 1  # set to ACTIVE
        self.handleNewLink(port, self.INFINITY_THRESHOLD, cost)

    # UPdating the Neigbors
    def update_Neighbors(self):
        content = ""
        for i in range(4):
            content += " " + str(self.view[i])
        for ports in self.links:
            self.send(ports, Packet(Packet.CONTROL, str(self.addr), "0", content))
        pass
