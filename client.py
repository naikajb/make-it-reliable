import os
import sys
import socket
import datetime
from protocol import (get_connection_id, create_packet, unpack_packet,  MSG_DATA, MSG_REQUEST, MSG_ERROR, MSG_ACK)


def send_request(sock,server_addr, connection_id, filename, timeout, segment_size, max_tries):
    """
        Sends a REQUEST packet and then waits for the response

        max_tries: sets the maximum number of times we will retry to get a file
    """

    payload = filename.encode('utf-8') # the create packet function takes in bytes
    packet = create_packet(connection_id, 0, MSG_REQUEST, payload, segment_size)
    print(f"[CLIENT]    Packet has been created ............. ")
    
    for attempt in range(1, max_tries + 1):
        sock.sendto(packet, server_addr)
        print(f"[CLIENT]    Sent REQUEST connection_id={connection_id}, file={filename}, attempt = {attempt}/{max_tries}")

        try:
            data, addr = sock.recvfrom(65535)
            packet_received = unpack_packet(data)

            if packet_received['connection_id'] != connection_id:
                print(f"[CLIENT]    Received an unknown connection id. Dropping packet.")
                return None, None
        
            if packet_received['msg_type'] == MSG_DATA:
                print(f"[CLIENT]    Server responsded on attempt {attempt} / {max_tries}. Starting file transfer.")
                return packet_received, addr
        
            if packet_received['msg_type'] == MSG_ERROR:
                print(f"[CLIENT]    Received ERROR.")
        
    
        except socket.timeout:
            print(f"[CLIENT]    Request timed-out while waiting for response on attempt = {attempt}/{max_tries}")

    return None, None


def receive_file (sock, connection_id, server_addr, output_path, timeout, first_packet , segment_size):
    file_chunks = []
    expected_seq_num = 0 #first segment we receive should be seq_num 0 always bcz its the first repsonse to our intial request

    # handle the first packet we already have
    if first_packet['seq_num'] == expected_seq_num:
        file_chunks.append(first_packet['payload'])
        ack_packet = create_packet(connection_id, 0, MSG_ACK, b"", segment_size ) # ACK packet so empty payload
        sock.sendto(ack_packet, server_addr)
        print(f"[CLIENT]    ACK sent  seq=0  chunk=1")

        expected_seq_num = 1

        # need to check if we receive a file that only takes one chunk to send
        if len(first_packet['payload']) < segment_size:
            print(f"[CLIENT]    Single chunk transfer complete")
            write_to_file(output_path, file_chunks)
            return True

    # if that first packet was not valid, then the regular look will start until seq_num = 0 is received
    while True: 
        try:
            data , addr = sock.recvfrom(65535)
        except socket.timeout:
            print(f"[CLIENT]    Timed out waiting for DATA seq={expected_seq_num}")
            return False
        
        try:
            received_packet = unpack_packet(data)
        except ValueError as e:
            print(f"[CLIENT]    Malformed packet received, discarding: {e}")
            continue

        # IF  connection_id !Valid --> drop packet
        if received_packet['connection_id'] != connection_id:
            print(f'[CLIENT]     Did not recognize connection_id={received_packet['connect_id']}. Dropping packet.')
            continue

        # IF  msg_type == MSG_ERROR --> drop packet
        if received_packet['msg_type'] == MSG_ERROR:
            print(f'[CLIENT]     Received packet with msg_type = MSG_ERROR Dropping packet. NO ACTION IMPLEMENTED')
            continue

        # IF  msg_type != MSG_DATA --> drop packet 
        if received_packet['msg_type'] != MSG_DATA:
            continue

        seq_num= received_packet["seq_num"]
        # IF seq_num != expected_sequence_num --> resend the ack for the seq_num we received
        if seq_num != expected_seq_num:
            print(f"[Client] Received packet w/ seq_num = {seq_num}, but expecteq seq_number was {expected_seq_num}. Retransmitting ACK for seq_num = {seq_num}")
            ack_packet = create_packet(connection_id, seq_num, MSG_ACK, b"", segment_size)
            sock.sendto(ack_packet, server_addr)
            continue

        # what you received is valid --> store the chunk and send ACK
        file_chunks.append(received_packet["payload"])
        print(f"[CLIENT]    DATA received  seq={seq_num}  chunk={len(file_chunks)}  {len(received_packet['payload'])}B")
        
        ack_packet = create_packet(connection_id, seq_num, MSG_ACK, b"", segment_size )
        sock.sendto(ack_packet, server_addr)

        expected_seq_num = 1 - expected_seq_num # alternate the expected sequence number

        if len(received_packet["payload"]) < segment_size:
            print(f"[CLIENT]    Final chunk received. Transfer complete")
            break
    
    write_to_file(output_path, file_chunks)
    return True

def write_to_file(output_path, file_chunks):
    """ Write the received data chunks to output path"""
    try: 
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    except OSError as e:
        print(f"[CLIENT] Error writing file to path={output_path}. {e}")
    file_data = b"".join(file_chunks)
    with open(output_path, "wb") as f:
        f.write(file_data)

    print(f"[CLIENT]    File saved \u21D2 {output_path}  ({len(file_data)}B)")
    

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
        first_packet, server_addr = send_request(sock, server_addr, connection_id, args.filename, args.timeout, args.segment_size, max_tries = 3)

        if first_packet is None:
            print("[client] transfer aborted")
            sys.exit(1)
        
        # output_path = f"./received_files/File_{connection_id}_{datetime.datetime.today().strftime("%d-%b-%H:%M")}"
        output_path = f"./received_files/Received_{args.filename}"

        receive_file(
            sock            = sock, 
            connection_id   = connection_id, 
            server_addr     = server_addr, 
            output_path     = output_path, 
            timeout         = args.timeout,
            first_packet    = first_packet,
            segment_size    = args.segment_size
        )
        
    except socket.error as e:
        print(e)
    finally:
        sock.close()
        print('[CLIENT] socket closed.')
