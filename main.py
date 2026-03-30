# to run server: python main.py serve --port 5005
# to run client: python main.py get --host 127.0.0.1 --port 5005 --filename COMP445_TA4_W26.pdf --segment-size 512 --timeout 4.0

import argparse
from client import start_client
from server import start_server


def parse_args():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="mode", required=True)

    # parser for CLIENT side
    client_parser = subparser.add_parser('get', help='Request a file from server')
    client_parser.add_argument('--host', help='Server IP address')
    client_parser.add_argument('--port', type=int, help='Server UDP port number')
    client_parser.add_argument('--filename', help='Name of file to retrieve from server')
    client_parser.add_argument('--segment-size', type=int, help='maximum payload size for each data packet')
    client_parser.add_argument('--timeout', default=5.0, type = float, help='Timeout in seconds')

    # parser for SERVER side
    server_parser = subparser.add_parser('serve', help='Listen for file requests')
    server_parser.add_argument('--host', default="0.0.0.0")
    server_parser.add_argument('--port', type=int, default=5005, help='Server UDP port number to listen from')

    return parser.parse_args()

def main():
    args = parse_args()

    if args.mode == "get":
        print(f'[Make-It-Reliable] Client Server           : {args.host}:{args.port}')
        print(f'[Make-It-Reliable] File             : {args.filename}')
        print(f'[Make-It-Reliable] Segment Size     : {args.segment_size} bytes')
        print(f'[Make-It-Reliable] Timeout          : {args.timeout} seconds\n')
        start_client(args)
    else:
        print(f"[Make-It-Reliable] Server   : {args.host}:{args.port}")
        start_server(args)

    

if __name__ == "__main__":
    main()