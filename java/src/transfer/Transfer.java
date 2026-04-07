package transfer;

import java.net.InetSocketAddress;
import java.util.ArrayList;
import java.util.List;

/**
 * Tracks the state of a single file transfer on the server side.
 * The server can handle multiple concurrent transfers (one per connection ID),
 * so each active transfer is represented by one Transfer object.
 */
public class Transfer {

    public final long              connectionId;
    public final InetSocketAddress clientAddr;
    public final String            filename;
    public final byte[]            fileData;
    public final int               fileLength;
    public final int               segmentSize;
    public final int               transferNumber;

    public boolean isComplete    = false;
    public int     currentChunk  = 0;   // index into chunks list
    public int     seqNum        = 0;   // alternates 0/1 for stop-and-wait
    public int     retransmissions = 0;

    private final List<byte[]> chunks;
    public  final int          totalChunks;

    public Transfer(long connectionId, InetSocketAddress clientAddr,
                    String filename, byte[] fileData,
                    int segmentSize, int transferNumber) {
        this.connectionId   = connectionId;
        this.clientAddr     = clientAddr;
        this.filename       = filename;
        this.fileData       = fileData;
        this.fileLength     = fileData.length;
        this.segmentSize    = segmentSize;
        this.transferNumber = transferNumber;

        this.chunks      = splitData(fileData);
        this.totalChunks = chunks.size();

        System.out.printf("[SERVER]    Initiated a Transfer object with %d chunks of data. " +
                "Each chunk will be up to %d bytes%n", totalChunks, segmentSize);
    }

    /** Split file bytes into fixed-size chunks. */
    private List<byte[]> splitData(byte[] data) {
        List<byte[]> result = new ArrayList<>();
        int len = Math.max(data.length, 1);
        for (int i = 0; i < len; i += segmentSize) {
            int end = Math.min(i + segmentSize, data.length);
            byte[] chunk = new byte[end - i];
            System.arraycopy(data, i, chunk, 0, chunk.length);
            result.add(chunk);
        }
        // Edge case: empty file -> one empty chunk
        if (data.length == 0) {
            result.add(new byte[0]);
        }
        return result;
    }

    /** Return the chunk we are currently waiting to have acknowledged. */
    public byte[] getCurrentChunk() {
        return chunks.get(currentChunk);
    }

    /** Advance to the next chunk and flip the sequence number. */
    public void next() {
        currentChunk++;
        seqNum = 1 - seqNum;
    }
}
