package server;

import protocol.Protocol;
import protocol.Packet;
import transfer.Transfer;

import java.io.IOException;
import java.net.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.Iterator;

/**
 * UDP File Transfer Server.
 *
 * Implements stop-and-wait reliable delivery on top of UDP.
 * Supports multiple concurrent transfers (one per connection ID).
 *
 * Run: java -cp out server.Server [--host HOST] [--port PORT]
 */
public class Server {

    private static final int MAX_RETRANSMITS = 10;
    private static final int SO_TIMEOUT_MS   = 3000;  // 3 second socket timeout

    // -------------------------------------------------------------------------
    // Request handler
    // -------------------------------------------------------------------------

    private static void handleRequest(DatagramSocket sock, InetSocketAddress clientAddr,
                                      long connectionId, Packet parsed,
                                      Map<Long, Transfer> activeTransfers) throws IOException {
        // 1. Decode the requested filename
        String filename;
        try {
            filename = new String(parsed.payload, "UTF-8").trim();
            if (filename.isEmpty()) throw new IllegalArgumentException("empty filename");
            System.out.printf("[SERVER]    Looking for file \"%s\"%n", filename);
        } catch (Exception e) {
            System.out.printf("[SERVER]    Malformed REQUEST from %s: %s%n", clientAddr, e.getMessage());
            return;
        }

        // 2. Try to read the file
        byte[] fileContent;
        try {
            fileContent = Files.readAllBytes(Paths.get("server_files", filename));
            System.out.printf("[SERVER]    \"%s\" found and read. Preparing to transfer....%n", filename);
        } catch (IOException e) {
            System.out.printf("[SERVER]    File not found: \"%s\". Sending ERROR.%n", filename);
            byte[] errPayload = ("File not Found: " + filename).getBytes("UTF-8");
            byte[] errPacket  = Protocol.createPacket(connectionId, 0, Protocol.MSG_ERROR, errPayload, 0);
            sock.send(new DatagramPacket(errPacket, errPacket.length,
                    clientAddr.getAddress(), clientAddr.getPort()));
            return;
        }

        // 3. Create transfer state and send the first chunk
        Transfer state = new Transfer(
                connectionId, clientAddr, filename, fileContent,
                parsed.segmentSize, activeTransfers.size() + 1
        );
        activeTransfers.put(connectionId, state);
        System.out.printf("[SERVER][TRANSFER #%d] Added to active transfers.%n", state.transferNumber);

        sendData(sock, state);
    }

    // -------------------------------------------------------------------------
    // ACK handler
    // -------------------------------------------------------------------------

    private static void handleAck(DatagramSocket sock, Packet parsed,
                                  Map<Long, Transfer> activeTransfers) throws IOException {
        long connectionId = parsed.connectionId;
        int  seqNum       = parsed.seqNum;

        Transfer state = activeTransfers.get(connectionId);
        if (state == null) {
            System.out.println("[SERVER]    Unknown connection ID. Dropping packet.");
            return;
        }

        // Wrong sequence number -> retransmit current chunk
        if (seqNum != state.seqNum) {
            System.out.printf("[SERVER][Transfer #%d]    ACK seq=%d does not match expected seq=%d." +
                            " Retransmitting chunk %d.%n",
                    state.transferNumber, seqNum, state.seqNum, state.currentChunk);
            sendData(sock, state);
            return;
        }

        // ACK for the last chunk -> transfer complete
        if (state.currentChunk == state.totalChunks - 1) {
            System.out.printf("[SERVER][Transfer #%d]    ACK for last chunk received." +
                            " Removing transfer (conn=%d).%n",
                    state.transferNumber, state.connectionId);
            state.isComplete = true;
            activeTransfers.remove(connectionId);
            return;
        }

        // Normal case: advance and send next chunk
        state.next();
        System.out.printf("[SERVER][Transfer #%d]    ACK received seq=%d. Sending next chunk.%n",
                state.transferNumber, seqNum);
        sendData(sock, state);
    }

    // -------------------------------------------------------------------------
    // Data sender
    // -------------------------------------------------------------------------

    private static void sendData(DatagramSocket sock, Transfer state) throws IOException {
        byte[] packet = Protocol.createPacket(
                state.connectionId,
                state.seqNum,
                Protocol.MSG_DATA,
                state.getCurrentChunk(),
                state.segmentSize
        );
        sock.send(new DatagramPacket(packet, packet.length,
                state.clientAddr.getAddress(), state.clientAddr.getPort()));
        System.out.printf("[SERVER]    DATA sent seq=%d  chunk=%d/%d%n",
                state.seqNum, state.currentChunk + 1, state.totalChunks);
    }

    // -------------------------------------------------------------------------
    // Main server loop
    // -------------------------------------------------------------------------

    public static void startServer(String host, int port) {
        try (DatagramSocket sock = new DatagramSocket(new InetSocketAddress(host, port))) {
            sock.setSoTimeout(SO_TIMEOUT_MS);
            System.out.printf("[SERVER]    Listening on %s:%d%n", host, port);
            System.out.println("[SERVER]    Waiting for requests...\n");

            Map<Long, Transfer> activeTransfers = new HashMap<>();
            byte[] buf = new byte[65535];

            while (true) {
                DatagramPacket dp = new DatagramPacket(buf, buf.length);
                try {
                    sock.receive(dp);
                } catch (SocketTimeoutException e) {
                    // Retransmit for all stalled transfers
                    Iterator<Map.Entry<Long, Transfer>> it = activeTransfers.entrySet().iterator();
                    while (it.hasNext()) {
                        Map.Entry<Long, Transfer> entry = it.next();
                        Transfer state = entry.getValue();
                        state.retransmissions++;
                        if (state.retransmissions > MAX_RETRANSMITS) {
                            System.out.printf("[SERVER]    Transfer #%d exceeded max retransmits. Giving up.%n",
                                    state.transferNumber);
                            it.remove();
                        } else {
                            System.out.printf("[SERVER]    Timeout — retransmitting chunk %d (attempt %d)%n",
                                    state.currentChunk, state.retransmissions);
                            sendData(sock, state);
                        }
                    }
                    continue;
                }

                // Copy received bytes
                byte[] received = new byte[dp.getLength()];
                System.arraycopy(dp.getData(), 0, received, 0, dp.getLength());

                InetSocketAddress clientAddr =
                        new InetSocketAddress(dp.getAddress(), dp.getPort());

                Packet parsed;
                try {
                    parsed = Protocol.unpackPacket(received);
                } catch (Exception e) {
                    System.out.printf("[SERVER]    Dropping malformed packet: %s%n", e.getMessage());
                    continue;
                }

                long connectionId = parsed.connectionId;

                if (parsed.msgType == Protocol.MSG_REQUEST) {
                    System.out.println("[SERVER]    Received REQUEST.");
                    handleRequest(sock, clientAddr, connectionId, parsed, activeTransfers);

                } else if (parsed.msgType == Protocol.MSG_ACK) {
                    System.out.println("[SERVER]    Received ACK.");
                    handleAck(sock, parsed, activeTransfers);

                } else {
                    System.out.printf("[SERVER]    Received %s — not handled.%n",
                            Protocol.getMessageType(parsed.msgType));
                }
            }

        } catch (SocketException e) {
            System.out.println("[SERVER]    Socket error: " + e.getMessage());
        } catch (IOException e) {
            System.out.println("[SERVER]    IO error: " + e.getMessage());
        }
    }
}

