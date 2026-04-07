package client;

import protocol.Protocol;
import protocol.Packet;

import java.io.*;
import java.net.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * UDP File Transfer client.Client.
 *
 * Implements stop-and-wait reliable delivery on top of UDP.
 *
 * Run: java -cp out client.client.Client --host HOST --port PORT
 *           --filename FILE --segment-size N [--timeout SECONDS] [--max-tries N]
 *
 *           java -cp out Main get --host 127.0.0.1 --port 5005 --filename Final-Project-Guidelines.pdf --segment-size 512
 */
public class Client {

    // -------------------------------------------------------------------------
    // Request phase
    // -------------------------------------------------------------------------

    /**
     * Send a REQUEST packet and wait for the server's first DATA response.
     *
     * @return the first DATA packet, or null if all attempts timed out / errored
     */
    private static Packet sendRequest(DatagramSocket sock, InetSocketAddress serverAddr,
                                      long connectionId, String filename,
                                      int segmentSize, int maxTries) throws IOException {
        byte[] payload = filename.getBytes("UTF-8");
        byte[] packet  = Protocol.createPacket(connectionId, 0, Protocol.MSG_REQUEST, payload, segmentSize);
        byte[] buf     = new byte[65535];

        System.out.println("[CLIENT]    Request packet created.");

        for (int attempt = 1; attempt <= maxTries; attempt++) {
            sock.send(new DatagramPacket(packet, packet.length,
                    serverAddr.getAddress(), serverAddr.getPort()));
            System.out.printf("[CLIENT]    Sent REQUEST conn=%d file=%s attempt=%d/%d%n",
                    connectionId, filename, attempt, maxTries);

            try {
                DatagramPacket dp = new DatagramPacket(buf, buf.length);
                sock.receive(dp);
                byte[] received = new byte[dp.getLength()];
                System.arraycopy(dp.getData(), 0, received, 0, dp.getLength());

                Packet pkt = Protocol.unpackPacket(received);

                if (pkt.connectionId != connectionId) {
                    System.out.println("[CLIENT]    Unknown connection ID. Dropping packet.");
                    return null;
                }
                if (pkt.msgType == Protocol.MSG_DATA) {
                    System.out.printf("[CLIENT]    server.Server responded on attempt %d/%d. Starting transfer.%n",
                            attempt, maxTries);
                    return pkt;
                }
                if (pkt.msgType == Protocol.MSG_ERROR) {
                    System.out.println("[CLIENT]    Received ERROR from server: " +
                            new String(pkt.payload, "UTF-8"));
                }

            } catch (SocketTimeoutException e) {
                System.out.printf("[CLIENT]    Timeout waiting for response (attempt %d/%d)%n",
                        attempt, maxTries);
            }
        }
        return null;
    }

    // -------------------------------------------------------------------------
    // Receive phase
    // -------------------------------------------------------------------------

    private static boolean receiveFile(DatagramSocket sock, long connectionId,
                                       InetSocketAddress serverAddr, String outputPath,
                                       Packet firstPacket, int segmentSize) throws IOException {
        ByteArrayOutputStream fileStream  = new ByteArrayOutputStream();
        int expectedSeqNum = 0;

        // Handle the first packet we already have from sendRequest()
        if (firstPacket.seqNum == expectedSeqNum) {
            fileStream.write(firstPacket.payload);

            byte[] ack = Protocol.createPacket(connectionId, 0, Protocol.MSG_ACK, new byte[0], segmentSize);
            sock.send(new DatagramPacket(ack, ack.length,
                    serverAddr.getAddress(), serverAddr.getPort()));
            System.out.println("[CLIENT]    ACK sent seq=0  chunk=1");

            expectedSeqNum = 1;

            // Single-chunk transfer?
            if (firstPacket.payload.length < segmentSize) {
                System.out.println("[CLIENT]    Single chunk transfer complete.");
                writeToFile(outputPath, fileStream.toByteArray());
                return true;
            }
        }
        // If the first packet had the wrong seq, the loop below will re-request

        byte[] buf = new byte[65535];

        while (true) {
            DatagramPacket dp = new DatagramPacket(buf, buf.length);
            try {
                sock.receive(dp);
            } catch (SocketTimeoutException e) {
                System.out.printf("[CLIENT]    Timed out waiting for DATA seq=%d%n", expectedSeqNum);
                return false;
            }

            byte[] received = new byte[dp.getLength()];
            System.arraycopy(dp.getData(), 0, received, 0, dp.getLength());

            Packet pkt;
            try {
                pkt = Protocol.unpackPacket(received);
            } catch (Exception e) {
                System.out.println("[CLIENT]    Malformed packet, discarding: " + e.getMessage());
                continue;
            }

            if (pkt.connectionId != connectionId) {
                System.out.printf("[CLIENT]    Unknown conn id=%d. Dropping.%n", pkt.connectionId);
                continue;
            }
            if (pkt.msgType == Protocol.MSG_ERROR) {
                System.out.println("[CLIENT]    Received ERROR packet. Dropping.");
                continue;
            }
            if (pkt.msgType != Protocol.MSG_DATA) {
                continue;
            }

            int seqNum = pkt.seqNum;

            // Wrong sequence number: re-ACK what we last got
            if (seqNum != expectedSeqNum) {
                System.out.printf("[CLIENT]    Got seq=%d but expected seq=%d. Re-ACKing seq=%d.%n",
                        seqNum, expectedSeqNum, seqNum);
                byte[] ack = Protocol.createPacket(connectionId, seqNum, Protocol.MSG_ACK,
                        new byte[0], segmentSize);
                sock.send(new DatagramPacket(ack, ack.length,
                        serverAddr.getAddress(), serverAddr.getPort()));
                continue;
            }

            // Valid in-order chunk
            fileStream.write(pkt.payload);
            System.out.printf("[CLIENT]    DATA received seq=%d  chunk=%d  %dB%n",
                    seqNum, fileStream.size() / segmentSize + 1, pkt.payload.length);

            byte[] ack = Protocol.createPacket(connectionId, seqNum, Protocol.MSG_ACK,
                    new byte[0], segmentSize);
            sock.send(new DatagramPacket(ack, ack.length,
                    serverAddr.getAddress(), serverAddr.getPort()));

            expectedSeqNum = 1 - expectedSeqNum;

            // Last chunk is indicated by a payload smaller than the segment size
            if (pkt.payload.length < segmentSize) {
                System.out.println("[CLIENT]    Final chunk received. Transfer complete.");
                break;
            }
        }

        writeToFile(outputPath, fileStream.toByteArray());
        return true;
    }

    // -------------------------------------------------------------------------
    // File writer
    // -------------------------------------------------------------------------

    private static void writeToFile(String outputPath, byte[] data) throws IOException {
        Path path = Paths.get(outputPath);
        if (path.getParent() != null) {
            Files.createDirectories(path.getParent());
        }
        Files.write(path, data);
        System.out.printf("[CLIENT]    File saved → %s  (%dB)%n", outputPath, data.length);
    }

    // -------------------------------------------------------------------------
    // Entry point
    // -------------------------------------------------------------------------

    public static void startClient(String host, int port, String filename,
                                   int segmentSize, double timeoutSecs, int maxTries) {
        System.out.println("[CLIENT]    Starting client...");

        InetSocketAddress serverAddr = new InetSocketAddress(host, port);
        long connectionId = Protocol.getConnectionId();

        System.out.printf("[CLIENT]    Connection ID  : %d%n", connectionId);
        System.out.printf("[CLIENT]    server.Server         : %s:%d%n", host, port);
        System.out.printf("[CLIENT]    Requesting     : %s%n", filename);
        System.out.printf("[CLIENT]    Segment Size   : %d%n", segmentSize);

        int timeoutMs = (int)(timeoutSecs * 1000);

        try (DatagramSocket sock = new DatagramSocket()) {
            sock.setSoTimeout(timeoutMs);

            Packet firstPacket = sendRequest(sock, serverAddr, connectionId,
                    filename, segmentSize, maxTries);
            if (firstPacket == null) {
                System.out.println("[CLIENT]    Transfer aborted — no response from server.");
                System.exit(1);
            }

            String outputPath = "received_files/Received_" + filename;

            boolean ok = receiveFile(sock, connectionId, serverAddr,
                    outputPath, firstPacket, segmentSize);
            if (!ok) {
                System.out.println("[CLIENT]    Transfer failed.");
                System.exit(1);
            }

        } catch (SocketException e) {
            System.out.println("[CLIENT]    Socket error: " + e.getMessage());
        } catch (IOException e) {
            System.out.println("[CLIENT]    IO error: " + e.getMessage());
        } finally {
            System.out.println("[CLIENT]    Socket closed.");
        }
    }
}
