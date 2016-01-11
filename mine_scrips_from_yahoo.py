#!/usr/bin/env python
#
# Author : Vikas Chouhan
# email  : presentisgood@gmail.com
#
# This is an automated script for mining down the list of all scrips available on
# https://in.finance.yahoo.com
# NOTE : This script uses selenium python module to function properly.

from   selenium import webdriver
from   selenium.webdriver.common.keys import Keys
from   selenium.webdriver.common.proxy import *
from   selenium.common.exceptions import *
import os
import sys
import argparse

###################################################

def assertm(cond, msg):
    if not cond:
        print msg
        sys.exit(-1)
    # endif
# enddef

def main_thread(fout):
    yahoo_base_url    = "https://in.finance.yahoo.com/lookup/stocks?s=%3f&t=S&m=IN&r="
    next_xpath_first_page = '//*[@id="pagination"]/a[3]'
    next_xpath_other_page = '//*[@id="pagination"]/a[3]'
    next_csspath_first_page = '#pagination > a:nth-child(1)'
    next_csspath_other_page = '#pagination > a:nth-child(3)'
    driver            = webdriver.PhantomJS()
    scrip_dict        = {}
    page_num          = 1
 
    # Load starting page
    driver.get(yahoo_base_url)

    while True:
        if True:
            # Check if "Next Button" exists
            if page_num == 1:
                # If next button doesn't exists, just break out of the loop !!
                try:
                    next_button = driver.find_element_by_css_selector(next_csspath_first_page)
                except NoSuchElementException:
                    break
                except:
                    continue
                # endtry
            else:
                # If next button dnoesn't exist, just break out of the loop !!
                try:
                    next_button = driver.find_element_by_css_selector(next_csspath_other_page)
                except NoSuchElementException:
                    break
                except:
                    continue
                # endtry
            # endif

            # Get list of all rows
            odd_list  = driver.find_elements_by_class_name("yui-dt-odd")
            even_list = driver.find_elements_by_class_name("yui-dt-even")
            # Collect all information for odd rows
            for item_this in odd_list:
                column_list = item_this.find_elements_by_tag_name("td")
                scrip_id    = column_list[0].text.encode('ascii', 'ignore')
                name        = column_list[1].text.encode('ascii', 'ignore')
                scrip_type  = column_list[3].text.encode('ascii', 'ignore')
                exchange    = column_list[4].text.encode('ascii', 'ignore')
                scrip_dict[scrip_id] = {
                                           "id"    : scrip_id,
                                           "name"  : name,
                                           "type"  : scrip_type,
                                           "exch"  : exchange,
                                       }
                # Write to target file
                fout.write("{},{},{},{}\n".format(scrip_id, name, scrip_type, exchange))
            # endfor
            # Collect all information for even rows
            for item_this in even_list:
                column_list = item_this.find_elements_by_tag_name("td")
                scrip_id    = column_list[0].text.encode('ascii', 'ignore')
                name        = column_list[1].text.encode('ascii', 'ignore')
                scrip_type  = column_list[3].text.encode('ascii', 'ignore')
                exchange    = column_list[4].text.encode('ascii', 'ignore')
                scrip_dict[scrip_id] = {
                                           "id"    : scrip_id,
                                           "name"  : name,
                                           "type"  : scrip_type,
                                           "exch"  : exchange,
                                       }
                # Write to target file
                fout.write("{},{},{},{}\n".format(scrip_id, name, scrip_type, exchange))
            # endfor

            # Print
            sys.stdout.write("{}-{}..".format(len(even_list) + len(odd_list), page_num))
            sys.stdout.flush()

            # Click "Next Button"
            next_button.click()

            # Increment page number count
            page_num = page_num + 1
    # endwhile
    
    # Close driver
    driver.close()

    return scrip_dict
# enddef


# Main
if __name__ == "__main__":
    parser  = argparse.ArgumentParser()
    parser.add_argument("--outfile", help="output file for downloaded data", type=str, default=None)
    args    = parser.parse_args()

    if not args.__dict__["outfile"]:
        print "--outfile is required !!"
        sys.exit(-1)
    # endif
    outfile = args.__dict__["outfile"]
    fout    = open(outfile, "w")
    # Start collecting all values
    sdict   = main_thread(fout)
    # endfor
    fout.close()
# endif
