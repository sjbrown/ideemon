#! /usr/bin/python
'''
The parser that turns the comment
    autotest: unittest.testfile: foo_test.py
Into an args,kwargs tuple:
    ( (), {'unittest.testfile': 'foo_test.py'} )
'''

# autotest: doctest

import os
import re
import sys

__plugin_version = (1,0)

prefix = r'^\s*#\s*autotest\s*:\s*(.*)'
prefix_and_tail = re.compile(prefix, re.IGNORECASE)

def parse(s):
    '''Parse an #autotest string into args and kwargs

    >>> parse('') # returns None
    >>> parse('#autotest:')
    ((), {})
    >>> parse('#autotest: unittest')
    (('unittest',), {})
    >>> parse('#autotest: unittest.testfile:foo_test.py')
    ((), {'unittest.testfile': 'foo_test.py'})
    >>> parse('#autotest: env:docker unittest.testfile:foo_test.py')
    ((), {'env': 'docker', 'unittest.testfile': 'foo_test.py'})
    >>> parse('#autotest: some.thing : A B   other.thing:1 2')
    ((), {'other.thing': '1 2', 'some.thing': 'A B'})

    '''
    match = prefix_and_tail.match(s)
    if not match:
        return None
    tail = match.group(1)

    args = []
    kwargs = {}

    def recurse_tail(tail):
        # Go backwards, because the keys cannot contain whitespace and thus are
        # easier to split by.
        if not tail:
            return
        try:
            tail, value = tail.rsplit(':', 1)
        except ValueError:
            # It's all just 'asdf qewr zxcv' remaining
            [args.append(x) for x in tail.split()]
            return

        tail, value = tail.strip(), value.strip()
        try:
            tail, key = tail.rsplit(None, 1)
        except ValueError:
            key = tail
            tail = ''
        kwargs[key.strip()] = value

        recurse_tail(tail)

    recurse_tail(tail)
    return tuple(args), kwargs

