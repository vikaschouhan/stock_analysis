#!/usr/bin/env perl
##################################################################################
# This script scans yahoo server for all scrips belonging to NSE or BSE
# and stores the ticker symbols along with the ticker names in a file called
# stock_list.txt.
#
# Copyright 2014 : Vikas Chouhan (presentisgood@gmail.com)
#
# This file is distributed under the terms of GNU General Public License v2 under
# the provision that the above copyright notice shouldn't be removed from the modified
# file.
##################################################################################

use warnings;
use strict;
use Getopt::Long;
use IO::File;
use Data::Dumper;

my $yahoo_url     = "https://in.finance.yahoo.com/lookup/stocks?s=%3f&t=S&m=IN&r=&b=";
my $cmdline_base  = "wget --quiet --no-check-certificate -U \"Mozilla\"";
my $tmpfile       = "./tmp_f.txt";
my $genfile       = "stock_list.txt";
#my $n_scrips      = 8810;
my $n_scrips      = 40;
my $jmp_gap       = 20;
my $exchange      = 0;     # 0 means NSE, 1 means BSE

my $gfh           = new IO::File;
my $cmdline       = "";
my $regex         = ($exchange == 0) ?
                    qr/>(\w+)\.NS<\/a><\/td><td>([\w\s]*)<\/td>/ :
                    qr/>(\w+)\.NS<\/a><\/td><td>([\w\s]*)<\/td>/;

die "Couldn't open $gfh\n" unless $gfh->open("> $genfile");

print "Scanning $yahoo_url\n";

for (my $indx = 0; $indx < $n_scrips; $indx += $jmp_gap){
    $cmdline = $cmdline_base . " -O $tmpfile " . "\"" . $yahoo_url . $indx . "\"";
    system($cmdline);

    open(my $pl, "$cmdline |"); # or die "Command failed\n";

    my $fh  = new IO::File;
    die "Couldn't open $tmpfile\n" unless $fh->open("< $tmpfile");

    while(<$fh>){
        while (/$regex/g) {
            printf($gfh "%-20s %-100s\n", $1, $2); 
        }
    }

    system("rm $tmpfile");

    $fh->close();
    print "Scanned " . ($indx + $jmp_gap) . " scrips.............\n";
}

$gfh->close();
