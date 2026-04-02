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