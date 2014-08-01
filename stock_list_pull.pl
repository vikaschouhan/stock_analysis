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

my $yahoo_url_base   = "https://in.finance.yahoo.com/lookup/stocks?t=S&m=IN&r=";
my $yahoo_url        = "https://in.finance.yahoo.com/lookup/stocks?s=%3f&t=S&m=IN&r=&b=";

my $yahoo_url_s   = "s=";
my $yahoo_url_b   = "b=";

my @range_alpha   = ("A".."Z");
my $cmdline_base  = "wget --quiet --no-check-certificate -U \"Mozilla\"";
my $tmpfile       = "./tmp_f.txt";
my $genfile       = "stock_list.txt";
my $n_scrips      =3000;
#my $n_scrips      = 40;
my $jmp_gap       = 20;
my $exchange      = 0;     # 0 means NSE, 1 means BSE

my $gfh           = new IO::File;
my $cmdline       = "";
my $regex         = ($exchange == 0) ?
                    qr/>([\w\-]+)\.NS<\/a><\/td><td>([\w\s]*)<\/td>/ :
                    qr/>([\w\-]+)\.BO<\/a><\/td><td>([\w\s]*)<\/td>/ ;
my $ext           = ($exchange == 0) ? ".NS" : "BO";

die "Couldn't open $gfh\n" unless $gfh->open("> $genfile");

print "Scanning $yahoo_url\n";

for my $aindex (@range_alpha){
    my $cmdline_0 = $cmdline_base . " -O $tmpfile " . "\"" . $yahoo_url_base . "&" . $yahoo_url_s . $aindex;
    for (my $indx = 0; $indx < $n_scrips; $indx += $jmp_gap){
        $cmdline = $cmdline_0 . "&" . $yahoo_url_b . $indx . "\"";
        system($cmdline);
    
        open(my $pl, "$cmdline |"); # or die "Command failed\n";
    
        my $fh  = new IO::File;
        die "Couldn't open $tmpfile\n" unless $fh->open("< $tmpfile");
    
        while(<$fh>){
            while (/$regex/g) {
                my $full_name = "\"" . $2 . "\"";
                my $full_ticker = $1 . $ext;
                printf($gfh "%-20s %-100s\n", $full_ticker, $full_name); 
            }
        }
    
        system("rm $tmpfile");
    
        $fh->close();
        print "Scanned " . ($indx + $jmp_gap) . " scrips for " . $aindex . " ..................\n";
    }
}

$gfh->close();
