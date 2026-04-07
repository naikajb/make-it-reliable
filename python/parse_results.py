# parses results.txt and generates a clean results_summary.txt

SETUP = {
    "file"          : "COMP445_TA4_W26.pdf",
    "file_size"     : "2298799 bytes",
    "total_chunks"  : 4490,
    "segment_size"  : 512,
    "server_ns"     : "ns_server",
    "client_ns"     : "ns_client",
    "server_ip"     : "10.0.0.1",
    "client_ip"     : "10.0.0.2",
    "port"          : 5005,
}

NETEM_COMMANDS = {
    "DELAY 150ms + 20ms jitter" : "tc qdisc add dev veth_server root netem delay 150ms 20ms",
    "LOSS 3%"                   : "tc qdisc add dev veth_server root netem loss 3%",
    "LOSS 10%"                  : "tc qdisc add dev veth_server root netem loss 10%",
}

def parse_results(input_file="results.txt", output_file="results_summary.txt"):

    with open(input_file, "r") as f:
        lines = f.readlines()

    # find where each scenario starts and ends
    scenarios = []
    current_scenario = None

    for i, line in enumerate(lines):
        if line.startswith("---"):
            if current_scenario is not None:
                current_scenario["end"] = i
                scenarios.append(current_scenario)
            current_scenario = {"name": line.strip("- \n"), "start": i, "end": len(lines)}

    if current_scenario is not None:
        current_scenario["end"] = len(lines)
        scenarios.append(current_scenario)

    # write the summary
    with open(output_file, "w") as f:
        f.write("PART 2 - TEST RESULTS SUMMARY\n")
        f.write("=" * 40 + "\n\n")

        # write setup info
        f.write("EXPERIMENTAL SETUP\n")
        f.write("-" * 40 + "\n")
        f.write(f"File            : {SETUP['file']} ({SETUP['file_size']})\n")
        f.write(f"Total chunks    : {SETUP['total_chunks']}\n")
        f.write(f"Segment size    : {SETUP['segment_size']} bytes\n")
        f.write(f"Server          : {SETUP['server_ns']} @ {SETUP['server_ip']}:{SETUP['port']}\n")
        f.write(f"Client          : {SETUP['client_ns']} @ {SETUP['client_ip']}\n")
        f.write(f"Interface       : veth_server <-> veth_client\n\n")

        for scenario in scenarios:
            scenario_lines = lines[scenario["start"]:scenario["end"]]

            # extract key metrics
            data_sent       = sum(1 for l in scenario_lines if "DATA sent" in l)
            data_received   = sum(1 for l in scenario_lines if "DATA received" in l)
            retransmits     = sum(1 for l in scenario_lines if "Timeout" in l and "retransmitting" in l)
            success         = any("File saved" in l for l in scenario_lines)
            file_saved      = next((l.strip() for l in scenario_lines if "File saved" in l), None)
            timed_out       = next((l.strip() for l in scenario_lines if "Timed out" in l), None)
            exceeded        = any("exceeded max retransmits" in l for l in scenario_lines)
            netem_cmd       = NETEM_COMMANDS.get(scenario["name"], "unknown")

            f.write(f"SCENARIO: {scenario['name']}\n")
            f.write("-" * 40 + "\n")
            f.write(f"netem command   : {netem_cmd}\n")
            f.write(f"Result          : {'SUCCESS' if success else 'FAILURE'}\n")
            f.write(f"Chunks sent     : {data_sent}\n")
            f.write(f"Chunks received : {data_received}\n")
            f.write(f"Retransmissions : {retransmits}\n")

            if success and file_saved:
                f.write(f"File saved      : {file_saved}\n")
            if timed_out:
                f.write(f"Failure reason  : {timed_out}\n")
            if exceeded:
                f.write(f"Failure reason  : exceeded max retransmits\n")

            f.write("\n")

    print(f"Summary written to {output_file}")

parse_results()