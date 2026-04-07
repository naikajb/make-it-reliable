# make-it-reliable
Implementation of a reliable  UDP protocol for file transfers. 


Struct library documentation: https://docs.python.org/3/library/struct.html
Datetime explanation: https://www.w3schools.com/python/python_datetime.asp 

---

## How to Test Part 1: File Transfer over UDP

Make sure the file you want to transfer is inside the `server_files/` folder.

**Terminal 1: start the server first:**
```bash
python main.py serve --port 5005
```
Wait until you see:
```
[SERVER]    Listening on 0.0.0.0:5005
[SERVER]    Waiting for requests...
```

**Terminal 2: run the client:**
```bash
python main.py get --host 127.0.0.1 --port 5005 --filename yourfile.pdf --segment-size 512 --timeout 5.0
```

The received file will be saved in `received_files/` as `Received_yourfile.pdf`.

**To test with a different segment size:**
```bash
python main.py get --host 127.0.0.1 --port 5005 --filename yourfile.pdf --segment-size 1024 --timeout 5.0
```


## Part 2: Network Emulation

### Setup
- Two network namespaces: `ns_server` (10.0.0.1) and `ns_client` (10.0.0.2)
- Connected via virtual ethernet pair (`veth_server` <-> `veth_client`)
- Segment size: 512 bytes
- File transferred: COMP445_TA4_W26.pdf (2298799 bytes, 4490 chunks)

### Scenarios
| Scenario | netem command | Result |
|---|---|---|
| Delay 150ms + 20ms jitter | `netem delay 150ms 20ms` | Success |
| Loss 3% | `netem loss 3%` | Failed |
| Loss 10% | `netem loss 10%` | Failed |

### How to reproduce (must be run on Linux)
```bash
sudo bash setup_network.sh          # set up virtual network
sudo bash run_tests.sh 2>&1 | tee results.txt   # run all scenarios
python3 parse_results.py            # generate clean summary
sudo bash teardown_network.sh       # clean up
```

### Notes
- Loss scenarios failed due to client timeout expiring before transfer completed
- Protocol handles delay well, but it struggles under packet loss
- See `results.txt` for full raw output and `results_summary.txt` for clean summary
