#! /usr/bin/python

import os
import re
import sys
import string
import subprocess

def log_error(*args):
    msg = ' '.join([str(x) for x in args]) + '\n'
    sys.stderr.write(msg)


__plugin_version = (1,0)

def find_environment(spec):
    if not spec:
        return None
    if not spec.startswith('docker'):
        return None
    log_error('spec is ', spec)
    DockerEnvironment.spec = spec
    return DockerEnvironment

def defang(s):
    for c in s:
        if c not in string.digits + string.letters + '_':
            raise ValueError('Bad Value for env spec %s' % s)

class DockerEnvironment(object):
    spec = ''
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def run(self, test_fn, test_spec):

        env_spec = test_spec['env']
        _, container_name = env_spec.split('/')
        defang(container_name)

        # find the image we tagged
        cmd = 'docker ps -a|grep %s' % container_name
        p = subprocess.Popen(cmd, shell=True,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             )
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            log_error('No Docker container named "%s"!', container_name)
            return '',''


        cmd = test_fn()
        cmd = 'docker exec %s %s' % (container_name, cmd)
        log_error('')
        log_error('cmd', cmd)

        print '------ DOCKER THIS -----------'

        p = subprocess.Popen(cmd, shell=True,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             )

        stdout, stderr = p.communicate()
        log_error('stdout', stdout)
        log_error('stderr', stderr)

        return stdout, stderr
