#!/usr/bin/env python

import os
import sys
import re

def check(path):
    if os.path.splitext(path)[1] != '.md':
        return False
    with open(path) as f:
        head = f.readline()
        if head.strip() != '---':
            return False
        while True:
            text = f.readline().strip()
            if text == '---':
                break
            if re.match(r'^published:\strue$', text):
                return True
    return False


def check_and_print(path):
    if check(path):
        print(path)


def check_dir(dir):
    for f in os.listdir(dir):
        if f.startswith('.'):
            continue
        path = os.path.join(dir, f)
        if os.path.isdir(path):
            if f in ['articles', 'books']:
                check_dir(path)
        elif os.path.isfile(path):
            check_and_print(path)


def main():
    for path in sys.argv[1:]:
        if os.path.isdir(path):
            check_dir(path)
        elif os.path.isfile(path):
            check_and_print(path)

if __name__ == '__main__':
    main()
