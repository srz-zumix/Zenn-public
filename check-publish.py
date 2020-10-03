#!/usr/bin/env python

import os
import sys
import re

def check(path):
    if os.path.splitext(path)[1] != '.md':
        return False
    with open(path) as f:
        head = f.readline()
        if head != '---':
            return False
        while True:
            text = f.readline()
            if text == '---':
                break
            if re.match("^published:\strue$", text):
                return True
    return True

def check_and_print(path):
    if check(path):
        print(path)

def main():
    for path in sys.argv[1:]:
        if os.path.isdir(path):
            for f in os.listdir(path):
                check_and_print(f)
        elif os.path.isfile(path):
            check_and_print(path)

if __name__ == '__main__':
    main()
