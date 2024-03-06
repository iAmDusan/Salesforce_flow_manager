import socket
import struct
import binascii
import netifaces
import select

# Function to get the IP address of the first available network interface
def get_interface_ip():
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        addresses = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addresses:
            return addresses[netifaces.AF_INET][0]['addr']
    return None

# Function to print detailed information about each network interface
def print_interface_info():
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        print(f"Interface: {interface}")
        addresses = netifaces.ifaddresses(interface)
        for address_family in addresses:
            print(f"    Address Family: {address_family}")
            for address_info in addresses[address_family]:
                for key, value in address_info.items():
                    print(f"        {key}: {value}")

# Initialize `s` to None to ensure it's defined outside the try-except blocks
s = None

try:
    print_interface_info()

    # Get the IP address of the network interface
    interface_ip = get_interface_ip()
    if not interface_ip:
        print("Failed to retrieve the IP address of any network interface.")
        exit()

    # Create a raw socket and bind it to the network interface
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
    s.bind((interface_ip, 0))
    # Include IP headers
    s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    # Enable promiscuous mode
    s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

    print("Packet sniffer started. Press Ctrl+C to stop.")

    while True:
        ready = select.select([s], [], [], 1)
        if ready[0]:
            packet_data, addr = s.recvfrom(65565)

            if len(packet_data) < 14:
                print("Received packet is too short to process")
                continue

            ethernet_header = packet_data[0:14]
            eth_header = struct.unpack("!6s6s2s", ethernet_header)

            # Extract Ethernet type and convert from network byte order to host byte order
            eth_type = socket.ntohs(struct.unpack('!H', ethernet_header[12:14])[0])
            if eth_type == 0x0800:  # IPv4
                if len(packet_data) < 34:
                    print("Packet too short for an IPv4 header")
                    continue

                ipheader = packet_data[14:34]
                if len(ipheader) == 20:
                    ip_header = struct.unpack("!BBHHHBBH4s4s", ipheader)
                    print("\nIPv4 Packet")
                    print("Ethernet Header")
                    print("Destination MAC: {} Source MAC: {} Type: {}".format(
                        binascii.hexlify(eth_header[0]).decode(),
                        binascii.hexlify(eth_header[1]).decode(),
                        hex(eth_type)))
                    print("IP Header")
                    print("Version: {} IP Header Length: {} TTL: {} Protocol: {} Source IP: {} Destination IP: {}".format(
                        ip_header[0] >> 4, (ip_header[0] & 0xF) * 4, ip_header[5],
                        ip_header[6], socket.inet_ntoa(ip_header[8]), socket.inet_ntoa(ip_header[9])))
                else:
                    print("Invalid IPv4 header length, packet skipped.")
            elif eth_type == 0x86DD:  # IPv6
                print("IPv6 Packet received")
                # Handle IPv6 packet processing here
                pass
            else:
                print("Non-IPv4/IPv6 packet received, skipping...")

except KeyboardInterrupt:
    print("\nExiting...")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if s is not None:
        try:
            # Disable promiscuous mode
            s.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
        except Exception as e:
            print(f"Error disabling promiscuous mode: {e}")
        s.close()
