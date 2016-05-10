'''
Created on 10.05.2016

@author: lueschem
'''

import sys


def print_error_and_exit(*args, **kwargs):
    print('Error: ', end="", file=sys.stderr)
    print(*args, file=sys.stderr, **kwargs)
    sys.exit(1)
