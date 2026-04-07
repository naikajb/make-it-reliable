import server.Server;

/**
 * Entry point for the UDP File Transfer application.
 *
 * Usage:
 *   server.Server: java -cp out Main serve [--host HOST] [--port PORT]
 *   client.Client: java -cp out Main get   --host HOST --port PORT
 *                                   --filename FILE --segment-size N
 *                                   [--timeout SECS] [--max-tries N]
 *
 * Examples:
 *   java -cp out Main serve --port 5005
 *   java -cp out Main get --host 127.0.0.1 --port 5005 --filename test.pdf --segment-size 512
 */
public class Main {

    public static void main(String[] args) {
        if (args.length == 0) {
            printUsage();
            System.exit(1);
        }

        String mode = args[0];

        if (mode.equals("serve")) {
            // --- server.Server mode ---
            String host = "0.0.0.0";
            int    port = 5005;

            for (int i = 1; i < args.length; i++) {
                switch (args[i]) {
                    case "--host": host = args[++i]; break;
                    case "--port": port = Integer.parseInt(args[++i]); break;
                    default:
                        System.out.println("Unknown server argument: " + args[i]);
                        System.exit(1);
                }
            }

            System.out.printf("[Make-It-Reliable] server.Server : %s:%d%n", host, port);
            Server.startServer(host, port);

        } else if (mode.equals("get")) {
            // --- client.Client mode ---
            String host        = null;
            int    port        = -1;
            String filename    = null;
            int    segmentSize = -1;
            double timeout     = 5.0;
            int    maxTries    = 3;

            for (int i = 1; i < args.length; i++) {
                switch (args[i]) {
                    case "--host":         host        = args[++i]; break;
                    case "--port":         port        = Integer.parseInt(args[++i]); break;
                    case "--filename":     filename    = args[++i]; break;
                    case "--segment-size": segmentSize = Integer.parseInt(args[++i]); break;
                    case "--timeout":      timeout     = Double.parseDouble(args[++i]); break;
                    case "--max-tries":    maxTries    = Integer.parseInt(args[++i]); break;
                    default:
                        System.out.println("Unknown client argument: " + args[i]);
                        System.exit(1);
                }
            }

            if (host == null || port < 0 || filename == null || segmentSize < 0) {
                System.out.println("Missing required arguments for 'get' mode.");
                printUsage();
                System.exit(1);
            }

            System.out.printf("[Make-It-Reliable] server.Server       : %s:%d%n", host, port);
            System.out.printf("[Make-It-Reliable] File         : %s%n", filename);
            System.out.printf("[Make-It-Reliable] Segment Size : %d bytes%n", segmentSize);
            System.out.printf("[Make-It-Reliable] Timeout      : %.1f seconds%n", timeout);
            System.out.println();

            client.Client.startClient(host, port, filename, segmentSize, timeout, maxTries);

        } else {
            System.out.println("Unknown mode: " + mode);
            printUsage();
            System.exit(1);
        }
    }

    private static void printUsage() {
        System.out.println("Usage:");
        System.out.println("  server.Server: java -cp out Main serve [--host HOST] [--port PORT]");
        System.out.println("  client.Client: java -cp out Main get --host HOST --port PORT");
        System.out.println("                               --filename FILE --segment-size N");
        System.out.println("                               [--timeout SECS] [--max-tries N]");
    }
}
