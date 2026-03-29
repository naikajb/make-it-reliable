import struct
import random


# FORMAT OF HEADER:
#   Connection ID: rnd generated
#   Sequence Number: 0 or 1
#   Message Type: REQ, ACK, DATA, or ERR
#   Payload Length: in bytes



def get_connection_id() -> int:
    """return: randly generates 4-byte connection id"""
    return random.randint(0, 0xffffffff)

def create_packet(connection_id:int, seq_num:int, msg_type:str, payload:bytes)->bytes:
    """Serialize the packet: header + payload"""
    header = struct.pack(
        "!IB7sI",
        connection_id,
        seq_num,
        msg_type.encode(),
        len(payload)
    )

    return header + payload


def unpack_header(data:bytes):
    """Deserialize the header"""
    