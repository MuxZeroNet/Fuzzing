#!/usr/bin/env python2

import sys
import os
import random
import msgpack # requires msgpack-python

samples = [
    -1,
    15441,
    99999999999,
    "43110",
    192168,
    ['aaaaaaa', 'bbbbbbb', os.urandom(30), 12345678, 11111111111, {123: "4567890"}],
    "[sjfdkjsdalfksjdlfsafl]",
    "",
    0,
    1,
    ["this", 123, "is", {"not": "gonna"}, [["work", "!"]]],

    {"cmd": "getFile", "req_id": 1, "params": {"site": "1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D", "inner_path": "content.json", "location": 0}},
    {"cmd": "getFile", "req_id": 12345, "params": {"site": "1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D", "inner_path": "../sites.json", "location": -1230}},
    {"cmd": "ping", "req_id": 34323683, "params": {}},
    {"cmd": "ping", "req_id": False, "params": False},
    {"cmd": "pex", "req_id": 3123683, "params": ["sdfasfdsf", "vvvvvvv", 12388712937812]},
    {"cmd": "pex", "req_id": "fake", "params": {"site": "1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D", "peers": "AAAABBBBCCCCDDDD", "need": 50}},
    {"cmd": "pex", "req_id": "fake", "params:": {"site": "1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D", "peers": 0xABCDABCD, "need": -100}},
    {"cmd": "pex", "req_id": 50, "params:": {"site": "1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D", "peers": os.urandom(32), "need": "x"}},
    {"cmd": "pex", "req_id": 5, "params": {"site": "1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D", "peers": ["aaaa", "bbbb", "cccc", "dddd"], "need": [100]}},
    {"cmd": "getFile", "req_id": os.urandom(64), "params": {"site": "1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D", "inner_path": os.urandom(64), "location": 0}},
    {"cmd": "getFile", "req_id": 25519, "params": {"site": "1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D", "inner_path": ["./", "./", "./..", "sites.json"], "location": -1}},
    {"cmd": "", "req_id": None, "params": {"site": "1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D", "inner_path": os.urandom(64), "location": 0xAAAA}},
    {"cmd": [[[[[["getWhat?"]]]]]], "req_id": -300, "params": {"site": "1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D", "inner_path": ["./", "./", "./../", "/sites.json"], "location": 65537}},
    {"cmd": "update", "req_id": 123, "params": {"site": os.urandom(32)}},
    {os.urandom(8): "update", os.urandom(8): 123, "params": {"site": os.urandom(32), "inner_path": "././././././content.json"}},
]


item = random.SystemRandom().choice(samples)
sys.stdout.write(msgpack.packb(item))
