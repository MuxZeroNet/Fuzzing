## About the Results
ZeroNet logged exceptions immediately after malformed request were put in. Below are some error messages particularly interesting to look at.

### Long call stack
The log shows a very long call stack found in `fallback.py`, a file in the `msgpack-python` package. In a stack trace, the keyword `fallback.py` appears 23 times, which indicates that `msgpack-python` does not handle deeply nested MessagePack data well, or the corresponding protection is not enabled by the implementer or the client.

```
[22:43:11] FileServer Conn#94 127.0.0.1    [?] > Incoming connection...
[22:43:11] FileServer Conn#94 127.0.0.1    [v2] > Socket error: TypeError:
unhashable type: 'dict' in Connection.py line 158 > fallback.py line 557 >
fallback.py line 538 > fallback.py line 537 > fallback.py line 537 > fallback.py
line 537 > fallback.py line 537 > fallback.py line 537 > fallback.py line 537 >
fallback.py line 537 > fallback.py line 537 > fallback.py line 537 > fallback.py
line 537 > fallback.py line 537 > fallback.py line 537 > fallback.py line 537 >
fallback.py line 537 > fallback.py line 537 > fallback.py line 537 > fallback.py
line 537 > fallback.py line 537 > fallback.py line 537 > fallback.py line 537 >
fallback.py line 538
[22:43:11] FileServer Conn#94 127.0.0.1    [v2] > Closing connection:
MessageLoop ended, waiting_requests: 0, sites: 0, buff: 2...
[22:43:11] FileServer Conn#95 127.0.0.1    [?] > Incoming connection...
[22:43:11] FileServer Conn#95 127.0.0.1    [v2] > Socket error: KeyError: 'site'
in Connection.py line 163 > Connection.py line 270 > FileServer.py line 43 >
FileRequest.py line 82 > FileRequest.py line 260
[22:43:11] FileServer Conn#95 127.0.0.1    [v2] > Closing connection:
MessageLoop ended, waiting_requests: 0, sites: 0, buff: 0...
[22:43:11] FileServer Conn#113 127.0.0.1    [?] > Incoming connection...
[22:43:11] FileServer Conn#113 127.0.0.1    [v2] > Socket error: TypeError:
unhashable type: 'dict' in Connection.py line 158 > fallback.py line 557 >
fallback.py line 538 > fallback.py line 538
[22:43:11] FileServer Conn#113 127.0.0.1    [v2] > Closing connection:
MessageLoop ended, waiting_requests: 0, sites: 0, buff: 1...
```

### Type error
ZeroNet's FileServer implementation runs on the assumption that values must be in the expected types. The request handler terminates when trying to call a bound method that does not exist in an instance of an unexpected type. However, the request handler **should** validate data types before processing incoming data, and **should** report detected errors immediately after they are detected. It **should not** throw any unexpected exception when errors can be detected.

In `Connection.py`, the values of the `to` keys are used directly as list indices. The code does not check for data types and does not check for negative values. In `FileRequest.py`, similar issues are found and shown in the stack trace.

```
[22:43:11] FileServer Conn#93 127.0.0.1    [?] > Incoming connection...
[22:43:11] FileServer Conn#93 127.0.0.1    [v2] > Socket error: AttributeError:
'str' object has no attribute 'get' in Connection.py line 163 > Connection.py
line 238
[22:43:11] FileServer Conn#93 127.0.0.1    [v2] > Closing connection:
MessageLoop ended, waiting_requests: 0, sites: 0, buff: 0...

[22:49:20] FileServer Conn#1183 127.0.0.1    [v2] > Socket error: TypeError:
argument of type 'int' is not iterable in Connection.py line 160
[22:49:20] FileServer Conn#1183 127.0.0.1    [v2] > Closing connection:
MessageLoop ended, waiting_requests: 0, sites: 0, buff: 0...

[22:57:36] FileServer Conn#1353 127.0.0.1    [?] > Incoming connection...
[22:57:36] FileServer Conn#1353 127.0.0.1    [v2] > Socket error: TypeError:
list indices must be integers, not str in Connection.py line 163 > Connection.py
line 270 > FileServer.py line 43 > FileRequest.py line 82 > FileRequest.py
line 260
[22:57:36] FileServer Conn#1353 127.0.0.1    [v2] > Closing connection:
MessageLoop ended, waiting_requests: 0, sites: 0, buff: 0...
[22:57:36] FileServer Conn#1354 127.0.0.1    [?] > Incoming connection...
[22:57:36] FileServer Conn#1354 127.0.0.1    [v2] > Socket error: TypeError:
list indices must be integers, not str in Connection.py line 163 > Connection.py
line 270 > FileServer.py line 43 > FileRequest.py line 82 > FileRequest.py
line 260
[22:57:36] FileServer Conn#1354 127.0.0.1    [v2] > Closing connection:
MessageLoop ended, waiting_requests: 0, sites: 0, buff: 0...
[22:57:36] FileServer Conn#1355 127.0.0.1    [?] > Incoming connection...
```

### Key error
ZeroNet's implementation expects some JSON keys to always be there. "The error messaging was unclear." said [Mish Ochu](https://github.com/HelloZeroNet/ZeroNet/issues/877), an issue reporter. There are benefits of not relying on uncaught exceptions. Making ZeroNet distinguish between detected errors and unexpected errors reduces logging noise, and more important error messages can be seen easier.

```
[22:57:35] FileServer Conn#1335 127.0.0.1    [?] > Incoming connection...
[22:57:35] FileServer Conn#1335 127.0.0.1    [v2] > Socket error: KeyError:
'site' in Connection.py line 163 > Connection.py line 270 > FileServer.py
line 43 > FileRequest.py line 82 > OptionalManagerPlugin.py line 79 >
FileRequest.py line 174
[22:57:35] FileServer Conn#1335 127.0.0.1    [v2] > Closing connection:
MessageLoop ended, waiting_requests: 0, sites: 0, buff: 0...
[22:57:35] FileServer Conn#1336 127.0.0.1    [?] > Incoming connection...
[22:57:35] FileServer Conn#1336 127.0.0.1    [v2] > Socket error: KeyError:
'inner_path' in Connection.py line 163 > Connection.py line 270 > FileServer.py
line 43 > FileRequest.py line 82 > OptionalManagerPlugin.py line 80
```

### ASCII decoding error
Though ZeroNet only allows a subset of ASCII characters to be used as file names, the request handler does not "crash well" when invalid characters are present. Since byte strings and unicode strings are used interchangeably in the source code, I **strongly recommend** the implementer decode byte strings as early as possible before any string comparison takes place. The Python interpreter will **not** throw an exception when it is comparing a unicode string with a malformed byte string. Instead, it will treat the two strings as unequal, which may lead to unexpected behaviors.

```python
>>> request_norm = 'Tamás Kocsis/data/'
>>> forbidden_folder = u'Tamás Kocsis/data/'
>>> request_norm, forbidden_folder
('Tam\xc3\xa1s Kocsis/data/', u'Tam\xe1s Kocsis/data/')
>>> request_norm == forbidden_folder
__main__:1: UnicodeWarning: Unicode equal comparison failed to convert both
arguments to Unicode - interpreting them as being unequal
False
>>>
```

```
[22:49:20] FileServer GetFile read error: UnicodeDecodeError: 'ascii' codec
can't decode byte 0xa1 in position 4: ordinal not in range(128) in
FileRequest.py line 179 > SiteStorage.py line 292
[22:49:20] FileServer Conn#1182 127.0.0.1    [v2] > Closing connection:
MessageLoop ended, waiting_requests: 0, sites: 0, buff: 0...
[22:49:20] FileServer Conn#1183 127.0.0.1    [?] > Incoming connection...
[22:49:20] FileServer GetFile read error: UnicodeDecodeError: 'ascii' codec
can't decode byte 0xa1 in position 4: ordinal not in range(128) in
FileRequest.py line 179 > SiteStorage.py line 292
```
