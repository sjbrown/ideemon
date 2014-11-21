#! /usr/bin/python

import os
import re
import sys
import subprocess

def log_error(*args):
    msg = ' '.join([str(x) for x in args]) + '\n'
    sys.stderr.write(msg)


pluginVersion = (1,0)

def find_environment(spec):
    if spec != 'subprocess':
        return None
    return SubprocessEnvironment

class SubprocessEnvironment(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def run(self, test_fn, *args, **kwargs):
        cmd = test_fn(*args, **kwargs)
        log_error('')
        log_error('cmd', cmd)

        p = subprocess.Popen(cmd, shell=True,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             )

        stdout, stderr = p.communicate()
        log_error('stdout', stdout)
        log_error('stderr', stderr)

        return stdout, stderr
