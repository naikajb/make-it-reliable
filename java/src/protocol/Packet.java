/** Simple data-holder returned by unpackPacket(). */
package  protocol;

public class Packet {
    public final long   connectionId;
    public final int    seqNum;
    public final int    msgType;
    public final int    payloadLength;
    public final byte[] payload;
    public final int    segmentSize;

    public Packet(long connectionId, int seqNum, int msgType,
                  int payloadLength, byte[] payload, int segmentSize) {
        this.connectionId  = connectionId;
        this.seqNum        = seqNum;
        this.msgType       = msgType;
        this.payloadLength = payloadLength;
        this.payload       = payload;
        this.segmentSize   = segmentSize;
    }
}