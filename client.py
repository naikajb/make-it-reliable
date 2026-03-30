import sys
import socket
from protocol import (get_connection_id, create_packet, MSG_REQUEST)


def send_request(sock,server_addr, connection_id, filename, timeout, segment_size):
    """
    Sends a REQUEST packet and then waits for the response
    """

    payload = filename.encode('utf-8') #the create packet function takes in bytes
    packet = create_packet(connection_id, 0, MSG_REQUEST, payload, segment_size)
    print(f"[CLIENT]    Packet has been created ............. ")
    print(f"[CLIENT]    Sending REQUEST connection_id={connection_id}, file={filename}")
    sock.sendto(packet, server_addr)
    
    try:
        data, addr = sock.recvfrom(65535)

    except socket.timeout:
        print(f"[CLIENT]    Request timed-out while waiting for response.")

    return None, None




def start_client(args):
    print('[CLIENT]     Starting Client...... ')

    server_addr = (args.host, args.port)
    connection_id = get_connection_id()

    print(f"[CLIENT]     Connection ID  :  {connection_id}")
    print(f"[CLIENT]     Sever          :  {server_addr}")
    print(f"[CLIENT]     Requesting     :  {args.filename}")
    print(f"[CLIENT]     Segment Size   :  {args.segment_size}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(args.timeout)

    try:
        first_packet, server_addr = send_request(sock, server_addr, connection_id, args.filename, args.timeout, args.segment_size)

    except socket.error:
        print(socket.error.strerror)
    finally:
        sock.close()
        print('[CLIENT] socket closed.')
