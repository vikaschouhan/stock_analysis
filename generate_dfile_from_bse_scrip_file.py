#!/usr/bin/env python

import argparse
import re
import csv

if __name__ == '__main__':
    """bsefile is the actual csv file which we get from bseindia.com"""

    bse_scrip_list   = []
    local_scrip_list = []
    regex_i          = re.compile(r'(\d+)')

    parser           = argparse.ArgumentParser()
    parser.add_argument("--output",    help="Output description file",     type=str, required=True)
    parser.add_argument("--sfile",     help="scrip file",                  type=str, required=True)
    parser.add_argument("--bsefile",   help="bse scrip database file",     type=str, required=True)

    args             = parser.parse_args()

    ofile            = open(args.output, "w")
    sfile            = open(args.sfile,  "r")
    bsefile          = open(args.bsefile, "r")

    bsefile_data     = csv.reader(bsefile)

    # Populate scrip information from bse database
    for item in bsefile_data:
        bse_scrip_list.append(item)

    #  Populate scrip ids from scrip file
    for line in sfile:
        res = regex_i.search(line)
        if res:
            local_scrip_list.append(res.groups()[0])

    #print bse_scrip_list
    #print local_scrip_list

    # search for each scrip in bse database.
    for iscrip in local_scrip_list:
        for bsescrip in bse_scrip_list:
            if iscrip == bsescrip[0]:
                print >>ofile, "{}  \"{}\"  {}" . format(bsescrip[1] + ".BO", bsescrip[2], bsescrip[0])

    ofile.close()
    sfile.close()
    bsefile.close()

