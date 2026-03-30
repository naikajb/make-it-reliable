import socket
from protocol import (unpack_packet, create_packet, MSG_ACK, MSG_ERROR, MSG_REQUEST, MSG_DATA, get_message_type)
from transfer import Transfer

def handle_request(sock, client_addr,  connection_id, parsed, active_transfers ):
    """
    Process an incoming REQUEST packet.

    Steps:
      1. Extract the requested filename from the payload
      2. Validate the file exists and is readable
      3. Send ERROR back if not
      4. Otherwise create a TransferState and send the first DATA packet
    """
    # we get the filename
    try: 
        filename = parsed['payload'].decode("utf-8")

        if not filename:
            raise ValueError
        print(f"[SERVER]    Looking for file  \"{filename}\"")
    except UnicodeDecodeError:
        print(f"[SERVER]    Malformed REQUEST from {client_addr}, cannot decode filename")
        return
    
    
    # we try to get the file
    try:
        with  open("./server_files/"+filename, "rb") as f:
            file_content = f.read()
        print(f'[SERVER]    {filename} was found and read. Preparing to transfer file....')
    except FileNotFoundError as e:
        print(f"[server]    failed to read '{filename}': {e}")

    
    # set up to send file chunks
    transfer_state = Transfer(
        connection_id,
        client_addr,
        filename,
        file_content, 
        parsed['segment_size']
    )

    #add it to the list of transfers ongoing in server
    active_transfers[connection_id] = transfer_state

    # start sending data
    send_data(sock,transfer_state)


def send_data(sock, transfer_state):
    # you send the current chunk of data and then in
    packet = create_packet(
        connection_id = transfer_state.connection_id,
        seq_num = transfer_state.seq_num,
        msg_type = MSG_DATA,
        payload = transfer_state.get_current_chunk(),
        segment_size= transfer_state.segment_size
    )
    sock.sendto(packet, transfer_state.client_addr)
    print(f"[server] DATA sent  seq={transfer_state.seq_num}. Sent {transfer_state.current_chunk}/{transfer_state.total_chunks}")


def start_server(args):
    host      = args.host
    port      = args.port
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))

    print(f"[SERVER]    listening on {host}:{port}")
    print(f"[SERVER]    waiting for requests...\n")

    active_transfers = {}
    try: 
        while True:
            # receive the data
            try:
                data, client_addr  = sock.recvfrom(65535)
            except KeyboardInterrupt:
                raise
            except OSError as e:
                print(f"[SERVER]    socket error: {e}")
                continue

            # parse what you received to get the type and connection id
            try:

                parsed = unpack_packet(data)
            except ValueError as e:
                print(f"[SERVER]    dropping a packet because error occured: {e}")
                continue

            msg_type = parsed['msg_type']
            connection_id = parsed['connection_id']

            if msg_type == MSG_REQUEST:
                print(f"[SERVER]    Received {get_message_type(msg_type)} type message")
                handle_request(
                    sock,
                    client_addr,
                    connection_id,
                    parsed,
                    active_transfers
                )
            else:
                print(f"[SERVER] Received {msg_type} type message. Not implemented yet.")

    except KeyboardInterrupt:
        print(f"\n[server] shutting down")
    finally:
        sock.close()
        print(f"[server] socket closed")