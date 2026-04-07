package protocol;


import java.nio.ByteBuffer;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

/**
 * Protocol constants and packet serialization/deserialization.
 *
 * Packet header format (big-endian):
 *   connection_id  : 4 bytes (unsigned int)
 *   seq_num        : 1 byte
 *   msg_type       : 1 byte
 *   payload_length : 4 bytes (unsigned int)
 *   segment_size   : 4 bytes (unsigned int)
 *   ---
 *   Total header   : 14 bytes
 */
public class Protocol {

    public static final int MSG_REQUEST = 1;
    public static final int MSG_ACK     = 2;
    public static final int MSG_ERROR   = 3;
    public static final int MSG_DATA    = 4;

    // 4 (conn id) + 1 (seq) + 1 (type) + 4 (payload len) + 4 (segment size)
    public static final int HEADER_SIZE = 14;

    private static final Map<Integer, String> MSG_TYPES = new HashMap<>();
    static {
        MSG_TYPES.put(MSG_REQUEST, "REQUEST");
        MSG_TYPES.put(MSG_ACK,     "ACK");
        MSG_TYPES.put(MSG_ERROR,   "ERROR");
        MSG_TYPES.put(MSG_DATA,    "DATA");
    }

    /** Generate a random 4-byte connection ID. */
    public static long getConnectionId() {
        return Integer.toUnsignedLong(new Random().nextInt());
    }

    /** Human-readable message type name. */
    public static String getMessageType(int msgType) {
        return MSG_TYPES.getOrDefault(msgType, String.format("UNKNOWN(0x%02x)", msgType));
    }

    /**
     * Serialize a packet into bytes: header + payload.
     */
    public static byte[] createPacket(long connectionId, int seqNum, int msgType,
                                      byte[] payload, int segmentSize) {
        ByteBuffer buf = ByteBuffer.allocate(HEADER_SIZE + payload.length);
        buf.putInt((int) connectionId);   // 4 bytes
        buf.put((byte) seqNum);           // 1 byte
        buf.put((byte) msgType);          // 1 byte
        buf.putInt(payload.length);       // 4 bytes
        buf.putInt(segmentSize);          // 4 bytes
        buf.put(payload);
        return buf.array();
    }

    /**
     * Deserialize raw bytes into a Packet object.
     */
    public static Packet unpackPacket(byte[] data) {
        if (data.length < HEADER_SIZE) {
            throw new IllegalArgumentException(
                    String.format("Packet (%d bytes) is smaller than header size (%d)", data.length, HEADER_SIZE));
        }
        ByteBuffer buf = ByteBuffer.wrap(data);
        long   connectionId   = Integer.toUnsignedLong(buf.getInt());
        int    seqNum         = Byte.toUnsignedInt(buf.get());
        int    msgType        = Byte.toUnsignedInt(buf.get());
        int    payloadLength  = buf.getInt();
        int    segmentSize    = buf.getInt();

        byte[] payload = new byte[payloadLength];
        buf.get(payload);

        return new Packet(connectionId, seqNum, msgType, payloadLength, payload, segmentSize);
    }
}
