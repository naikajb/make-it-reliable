import sys
import os
import socket
from protocol import (get_connection_id, create_packet, unpack_packet,  MSG_DATA, MSG_REQUEST, MSG_ERROR, MSG_ACK)


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
        packet_received = unpack_packet(data)

        if packet_received['connection_id'] != connection_id:
            print(f"[CLIENT]    Received an unknown connection id. Dropping packet.")
            return None, None
        
        if packet_received['msg_type'] == MSG_DATA:
            print(f"[CLIENT]    Received DATA for connection_id={packet_received['connection_id']}, with seq_num={packet_received['seq_num']}")
            return packet_received, addr
        
        if packet_received['msg_type'] == MSG_ERROR:
            print(f"[CLIENT]    Received ERROR.")
        
    
    except socket.timeout:
        print(f"[CLIENT]    Request timed-out while waiting for response.")

    return None, None


def receive_file (sock, connection_id, seq_num, server_addr, output_path, timeout, first_packet , segment_size):
    file_chunks = []
    expected_seq_num = 0 #first segment we receive should be seq_num 0 always bcz its the first repsonse to our intial request

    # handle the first packet we already have
    file_chunks.append(first_packet['payload'])
    ack_packet = create_packet(connection_id, 0, MSG_ACK, b"", segment_size ) # ACK packet so empty payload
    sock.sendto(ack_packet, server_addr)
    print(f"[CLIENT]    ACK sent  seq=0  chunk=1")

    expected_seq_num = 1

    while True: 
        try:
            data , addr = sock.recvfrom(65535)
            received_packet = unpack_packet(data)
        except socket.timeout:
            print(f"[CLIENT]    Timed out waiting for DATA seq={expected_seq_num}")
            return False


        # IF  connection_id !Valid --> drop packet
        if received_packet['connect_id'] != connection_id:
            print(f'[CLIENT]     Did not recognize connection_id={received_packet['connect_id']}. Dropping packet.')
            continue

        # IF  msg_type == MSG_ERROR --> drop packet
        if received_packet['msg_type'] == MSG_ERROR:
            print(f'[CLIENT]     Received packet with msg_type = MSG_ERROR Dropping packet. NO ACTION IMPLEMENTED')
            continue

        # IF  msg_type != MSG_DATA --> drop packet 
        if received_packet['msg_type'] != MSG_DATA:
            continue

        seq = received_packet["seq_num"]
        # IF seq_num != expected_sequence_num
        # TODO: drop? or resend an ACK? 

        #what you received is valid --> send ACK
        file_chunks.append(received_packet["payload"])
        ack_packet = create_packet(connection_id,  MSG_ACK, b"", segment_size )
        sock.sendto(ack_packet, server_addr)

        expected_seq_num = 1 - expected_seq_num # alternate the expected sequence number

        if len(received_packet["payload"]) < segment_size:
            print(f"[CLIENT]    Final chunk received — transfer complete")
            break
    
    write_to_file(output_path, file_chunks)
    return True

def write_to_file(output_path, file_chunks):
    """ Write the received data chunks to output path"""
    file_data = b"".join(file_chunks)
    with open(output_path, "wb") as f:
        f.write(file_chunks)

    print(f"[CLIENT]    File saved → {output_path}  ({len(file_data)}B)")
    

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

        if first_packet is None:
            print("[client] transfer aborted")
            sys.exit(1)


        # with first received packe we can set up to receive the rest and send ACK
        seq = first_packet['seq_num']
        output_path = f"./received_files/File_{connection_id}"

        receive_file(
            sock            = sock, 
            connection_id   = connection_id, 
            seq_num         = seq, 
            server_addr     = server_addr, 
            output_path     = output_path, 
            timeout         = args.timeout,
            first_packet    = first_packet,
            segment_size    = args.segment_size
         )
        
    except socket.error:
        print(socket.error.strerror)
    finally:
        sock.close()
        print('[CLIENT] socket closed.')
