#! /usr/bin/python
'''
Looks for comment lines like this:
    autotest: unittest.testfile : xxxxxxx
or:
    autotest: unittest
'''

# autotest: doctest
# autotest: unittest.testfile:tests/test_python_unittest.py

import os
import re
import sys
from ideemon.autotest_comment_parser import parse


__plugin_version = (1,0)


def log_error(*args):
    msg = ' unittest ' + ' '.join([str(x) for x in args]) + '\n'
    sys.stderr.write(msg)

tb_begin_pattern = 'Traceback (most recent call last):'
unittest_error_pattern = re.compile('File .*/([^/]+\.py)", line (\d+)')


def testfileFn(srcPath, testPath, **kwargs):
    srcDirname = os.path.dirname(srcPath)

    cmd = 'python %s' % testPath
    return cmd


def make_report(output, errput):
    '''
    "errput" is usually something like this:

     E
     ======================================================================
     ERROR: test_foo (__main__.SomeTestClass)
     ----------------------------------------------------------------------
     Traceback (most recent call last):
       File "/python/dist-packages/tornado/testing.py", line 120, in __call__
         result = self.orig_method(*args, **kwargs)
       File "/python/dist-packages/mock.py", line 1190, in patched
         return func(*args, **keywargs)
       File "/home/user/project/tests/foo.py", line 74, in test_foo
         ret = handler.foo(bazbar).result()
       File "/python/dist-packages/tornado/concurrent.py", line 209, in result
         raise_exc_info(self._exc_info)
       File "/python/dist-packages/tornado/gen.py", line 212, in wrapper
         yielded = next(result)
       File "/home/user/project/foo.py", line 160, in foo
         l = [a for (a,b) in some_pairs]
     ValueError: too many values to unpack
     
     ----------------------------------------------------------------------
     Ran 1 test in 0.143s


    If there are no errors, return []
    If there are errors, return a list of (filepath, lineNumber, errorSummary)
    '''
    errors = []
    lines = errput.splitlines()
    stack = []

    #print 'lines:\n', '\n'.join(errput.splitlines())

    tb_begun = False
    for i, line in enumerate(lines):
        if not tb_begun and line.strip() != tb_begin_pattern:
            #print 'S ', line
            continue
        tb_begun = True
        #print line

        m = unittest_error_pattern.search(line)
        if m:
            testFileName = m.group(1)
            lineNum = m.group(2)
            detail = lines[i+1].strip()
            detail += '\n' + lines[i+2].strip()
            errors.append((testFileName, lineNum, detail))

    #print 'E', errors
    # We want the LAST line that matches
    return errors[-1:]


def find_tests_for(fpath):
    '''Find tests for python files. Returns a unittest test if the
    file has a comment line that looks like "# autotest: unittest"

    >>> find_tests_for('/dev/null')
    []
    '''
    try:
        fileSize = os.path.getsize(fpath)
    except OSError, ex:
        log_error('could not get file size', fpath, ex)
        return []
    if fileSize > 100*1024: #bigger than 100KiB
        log_error('file too big', fpath)
        return []
    try:
        fp = file(fpath)
    except Exception, ex:
        log_error('could not open', fpath, ex)
        return []
    contents = fp.read()
    fp.close()
    lines = contents.splitlines()
    if not lines:
        log_error('empty file', fpath)
        return []

    firstline = lines[0]

    if not (fpath.endswith('.py')
        or (firstline.startswith('#!') and 'python' in firstline)):
        return []

    tests = findTestfileTestsFor(fpath, lines)
    return tests


def findTestfileTestsFor(fpath, lines):
    '''Returns a unittest test file if the inspected file has a comment line 
    that looks like "# autotest: unittest.testfile:tests/test_modname.py"

    >>> findTestfileTestsFor('/dev/null', [])
    []
    '''
    test_specs = []

    for line in lines:
        found_autotest = parse(line)
        if not found_autotest:
            continue
        args, kwargs = found_autotest

        if 'unittest' in args:
            # the unit test is assumed to be in the "standard" place
            fname = os.path.split(fpath)[-1]
            relativeTestPath = 'tests/test_' + fname
        else:
            relativeTestPath = kwargs.get('unittest.testfile')

        if relativeTestPath:
            srcDirname = os.path.dirname(fpath)
            testPath = os.path.join(srcDirname, relativeTestPath)

            #print 'found testfile pattern', line
            test_specs.append({
                'make_cmd_fn': testfileFn,
                'args': (fpath, testPath),
                'kwargs': {},
                'report_fn': make_report,
                'env': kwargs.get('env'),
            })
            break

    return test_specs


def main():
    thismodule_py = __file__.replace('pyc', 'py')
    print thismodule_py
    for t in find_tests_for(thismodule_py):
        print t

if __name__ == '__main__':
    main()
