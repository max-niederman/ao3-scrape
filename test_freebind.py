import socket
import sys
import ipaddress

local_addr = ipaddress.ip_address(sys.argv[1])

sock = socket.socket(
    family=socket.AF_INET if local_addr.version == 4 else socket.AF_INET6
)
sock.setsockopt(socket.SOL_IP, 15, 1)

print("binding...")
sock.bind((str(local_addr), 0))
print("connecting...")
sock.connect(("ip.me", 80))

print("sending request...")
sock.send(
    b"""
GET / HTTP/1.0
Host: ip.me

"""
)

print("receiving response...")
res = sock.recv(1024)
print(res.decode())
