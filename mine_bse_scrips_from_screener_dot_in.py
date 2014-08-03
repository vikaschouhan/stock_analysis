#!/usr/bin/env python

import argparse
import re

if __name__ == '__main__':
    regex_p          = re.compile(r'screener.in\/company\/\?q=(\d+)')
    scrip_list       = []

    parser           = argparse.ArgumentParser()
    parser.add_argument("input_files", help="Input HTML files downloaded from screener.in.",  type=str, nargs='+')
    parser.add_argument("--output",    help="minimum volume limit",                           type=str, required=True)

    args             = parser.parse_args()

    for ifile in args.input_files:
        f = open(ifile, "r")
        for line in f:
            res = regex_p.findall(line)
            if res != []:
                scrip_list += res
        f.close()

    # Remove duplicate entries & converts the number from string to integer
    scrip_list = map(int, list(set(scrip_list)))

    ofile = open(args.output, "w")
    for item in scrip_list:
        print >>ofile, "{}" . format(item)
    ofile.close()
