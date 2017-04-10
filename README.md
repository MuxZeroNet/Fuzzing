# Fuzzing
All about fuzz testing ZeroNet.

## What's this?
I conducted a very simple fuzz test for ZeroNet in order to check its robustness. This test has very little code coverage, but it discovered the inconsistency in ZeroNet's exception handling processes.

## Fuzz it yourself!
The script `zn_protocol.py` is a simple input sample generator. It produces one properly encoded or corrupted request at a time. Note that this simple script does not cover all of the commands defined in the ZeroNet [protocol](https://zeronet.readthedocs.io/en/latest/help_zeronet/network_protocol/) spec, but you can definitely [help us improve its code coverage!](zn_protocol.py)

I used [radamsa](https://github.com/aoh/radamsa) as the fuzzer. Other fuzzers are also applicable for fuzz testing ZeroNet. I ran the fuzz tests in a virtual machine with a clean ZeroNet package.

To generate 20 malformed requests and put them into ZeroNet's File Server port, simply run:

```bash
python ~/Documents/zn_protocol.py | ./radamsa --output 127.0.0.1:15441 --delay 10 -n 20
```

Please run this command multiple times so that the fuzzer can switch between different input samples.
