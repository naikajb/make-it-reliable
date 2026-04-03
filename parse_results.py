# parses results.txt and generates a clean results_summary.txt

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
            current_scenario = {"name": line.strip(), "start": i, "end": len(lines)}
    
    if current_scenario is not None:
        current_scenario["end"] = len(lines)
        scenarios.append(current_scenario)

    # write the summary
    with open(output_file, "w") as f:
        f.write("PART 2: TEST RESULTS SUMMARY\n")
        f.write("=" * 40 + "\n\n")

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

            f.write(f"SCENARIO: {scenario['name']}\n")
            f.write("-" * 40 + "\n")
            f.write(f"Result: {'SUCCESS' if success else 'FAILURE'}\n")
            f.write(f"Chunks sent: {data_sent}\n")
            f.write(f"Chunks received: {data_received}\n")
            f.write(f"Retransmissions: {retransmits}\n")
            
            if success and file_saved:
                f.write(f"File saved: {file_saved}\n")
            if timed_out:
                f.write(f"Failure reason: {timed_out}\n")
            if exceeded:
                f.write(f"Failure reason: exceeded max retransmits\n")
            
            f.write("\n")

    print(f"Summary written to {output_file}")

parse_results()