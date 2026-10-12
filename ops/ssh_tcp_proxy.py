"""Small TCP segments for SSH over paths with packet-size problems.

Use only as OpenSSH's ProxyCommand. SSH still verifies the server and performs
all authentication/encryption itself; this relay never reads private keys.
"""
import argparse
import os
import select
import socket


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host")
    parser.add_argument("port", type=int, choices=range(1, 65536), metavar="PORT")
    args = parser.parse_args()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(10)
        # Before connect: advertise smaller incoming segments. Reapply after
        # connect because macOS can replace the outgoing MSS during negotiation.
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG, 512)
        sock.connect((args.host, args.port))
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG, 512)
        sock.settimeout(None)
        while True:
            ready, _, _ = select.select([sock, 0], [], [])
            if sock in ready:
                data = sock.recv(16384)
                if not data:
                    break
                pending = memoryview(data)
                while pending:
                    pending = pending[os.write(1, pending):]
            if 0 in ready:
                data = os.read(0, 16384)
                if not data:
                    break
                sock.sendall(data)


if __name__ == "__main__":
    main()
