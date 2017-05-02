## Test ZeroNet with any fuzzer

ZeroNet has no official support for fuzz testing, so you have to modify the source code of ZeroNet before you use a fuzzer. You need to disable the UiServer and make the FileServer read `sys.stdin` as data input. Most importantly, ZeroNet must clearly report its states in a way that the fuzzer understands. Exception handlers must be modified to kill the program when an unexpected exception is caught.

### Disable UiServer and spawn FileServer only

Find the `main` method in `src/main.py`

```python
# Default action: Start serving UiServer and FileServer
def main(self):
```

Comment out the code used to spawn the FileServer.

```python
gevent.joinall([gevent.spawn(ui_server.start), gevent.spawn(file_server.start)])
```

In the `main` method, you should start the FileServer directly. Note that you do not need to use `gevent`

```python
file_server.start()
```

### Don't use `gevent` methods

We do not need multithreading at this moment. We have to make bootstrapping as fast as possible. Open the file `src/File/FileServer.py` and find the `start` method.

```python
# Bind and start serving sites
def start(self, check_sites=True):
```

You should comment out every line that uses `gevent`

```python
if check_sites:  # Open port, Update sites, Check files integrity
    gevent.spawn(self.checkSites)

thread_announce_sites = gevent.spawn(self.announceSites)
thread_cleanup_sites = gevent.spawn(self.cleanupSites)
thread_wakeup_watcher = gevent.spawn(self.wakeupWatcher)
```

We see this method call `ConnectionServer.start(self)`. Now find the constructor in `src/Connection/ConnectionServer.py`

```python
class ConnectionServer:
    def __init__(self, ip=None, port=None, request_handler=None):
```

The constructor spawns a site checker thread. You may need to comment this out for performance.

```python
# self.thread_checker = gevent.spawn(self.checkConnections)
self.thread_checker = None
```

### Read `sys.stdin`
A majority of fuzzers write output to `stdin`, so ZeroNet must read `sys.stdin` and process what it gets. Find the `start` method in `src/Connection/ConnectionServer.py`

```python
def start(self):
```

We see this method constructs a gevent StreamServer. We do not need this in fuzz testing.

```python
try:
    self.stream_server.serve_forever()  # Start normal connection server
except Exception, err:
    self.log.info("StreamServer bind error, must be running already: %s" % err)
```

However, this section should be changed to initialize the fuzzer and read `sys.stdin`

```python
try:
    import afl  # python-afl
    afl.init()

    s = sys.stdin.read()
    self.handleFuzzTest(s)
except Exception, err:
    self.log.error("Uncaught Exception %s" % err)
    killProcess()  # will explain later
```

Find the `handleIncomingConnection` method in the same file. We see this handler constructs a new `Connection` instance. After that, it calls `connection.handleIncomingConnection(sock)`

```python
def handleIncomingConnection(self, sock, addr):
    ip, port = addr

    # Connection flood protection
    # ......

    connection = Connection(self, ip, port, sock)
    self.connections.append(connection)
    self.ips[ip] = connection
    connection.handleIncomingConnection(sock)
```

Following the call graph, we now open `src/Connection/Connection.py` and see what's inside. We see the method `Connection.handleIncomingConnection` calls the method `messageLoop`, which calls the method `handleMessage`

```python
class Connection(object):

    def handleIncomingConnection(self, sock):
        self.log("Incoming connection...")
        self.type = "in"

        # TLS unwrapping
        # ......

        self.messageLoop()

    def messageLoop(self):
        if not self.sock:
            self.log("Socket error: No socket found")
            return False
        # Lots of attribute reassignment
        # ......

        self.unpacker = msgpack.Unpacker()
        try:
            while not self.closed:
                # Receive data from socket and unpack
                # ......

                for message in self.unpacker:
                    self.incomplete_buff_recv = 0
                    if "stream_bytes" in message:
                        self.handleStream(message)
                    else:
                        self.handleMessage(message)

                message = None
        except Exception, err:
            if not self.closed:
                self.log("Socket error: %s" % Debug.formatException(err))
        self.close("MessageLoop ended")  # MessageLoop ended, close connection
```

Therefore, the `messageLoop` method is the "real" handler. It reads data from a socket and unpacks it. We want it to accept a binary string. Now copy the body of this method, make a new method, and paste the code. Instead of a socket, we put a binary string into the unpacker.

```python
def _messageLoop(self, binary_string):
    self.log("Processing binary string...")
    self.protocol = "v2"
    self.updateName()
    self.connected = True
    buff_len = 0

    self.unpacker = msgpack.Unpacker()
    try:
        while not self.closed:
            buff = binary_string  # note the change
            self.closed = True  # note the change

            if not buff:
                break  # Connection closed
            buff_len = len(buff)

            # Remove Statistics stuff

            if not self.unpacker:
                self.unpacker = msgpack.Unpacker()
            self.unpacker.feed(buff)
            buff = None
            for message in self.unpacker:
                self.incomplete_buff_recv = 0
                if "stream_bytes" in message:
                    self.handleStream(message)
                else:
                    self.handleMessage(message)

            message = None
    except Exception, err:
        # note the change
        self.log("Socket error: %s" % Debug.formatException(err))
        killProcess()
    self.close("MessageLoop ended")  # MessageLoop ended, close connection
```

Save this file. Now go back to `src/Connection/ConnectionServer.py` and find the `handleIncomingConnection` method again. Write a new method below it. Our new method should use the binary string capable `_messageLoop`

```python
def handleFuzzTest(self, binary_string):
    connection = Connection(self, "127.0.0.1", 56789, sock=None)
    self.connections.append(connection)
    self.ips["127.0.0.1"] = connection  # note the change
    connection._messageLoop(binary_string)  # note the change
```

#### Call graph
```
main -> FileServer -> ConnectionServer -> Connection -> FileServer -> FileRequest
```

### Exception handlers
ZeroNet suppresses exceptions and will never crash. Even when ZeroNet exits after an uncaught exception, AFL does not recognize this as a crash.

If the process which AFL spawns is killed, AFL recognizes this signal as a crash. Exception handlers should be modified to first print out a stack trace and then deliberately kill the process.

```python
def killProcess():
    os.kill(os.getpid(), 9)
```

Exception handlers should look like this.

```python
try:
    # do something awful
    req_id = max(0, message["req_id"])
    req_list[req_id] = "..."
except Exception, err:
    self.log.error("Awful! %s" % err.message)
    killProcess()  # kill the process
```

### Test your changes
```bash
# should not throw any exception
python2 -c "import sys; sys.stdout.write('\x82\xa3cmd\xa4ping\xa6req_id\x02')" | python2 zeronet.py --tor disable --debug
# should throw an exception
echo "Malformed msg" | python2 zeronet.py --tor disable --debug
```

### Use a RAM disk
```bash
sudo mkdir /mnt/ramdisk
sudo mount -t tmpfs -o size=200m tmpfs /mnt/ramdisk
mount | grep 'tmpfs'
```

### Get the stack trace
```bash
cat /path/to/testcase | python2 zeronet.py --tor disable --debug
```
