import socket
from protocol import (unpack_packet, create_packet, MSG_ACK, MSG_ERROR, MSG_REQUEST, get_message_type)

def handle_request(sock, client_addr,  connection_id, parsed ):
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
        print(f"[SERVER]    Malformed REQUEST payload from {client_addr}, cannot decode filename")
        return
    
    
    # we try to get the file
    try:
        with  open("./server_files/"+filename, "rb") as f:
            file_content = f.read()
        print(f'[SERVER]    {filename} was found and read. Preparing to transfer file....')
    except FileNotFoundError as e:
        print(f"[server]    failed to read '{filename}': {e}")

    
    # set up to send file chunks



    

    

    



def start_server(args):
    host      = args.host
    port      = args.port
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))

    print(f"[SERVER]    listening on {host}:{port}")
    print(f"[SERVER]    waiting for requests...\n")

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
                    parsed
                )
            else:
                print(f"[SERVER] Received {msg_type} type message. Not implemented yet.")

    except KeyboardInterrupt:
        print(f"\n[server] shutting down")
    finally:
        sock.close()
        print(f"[server] socket closed")