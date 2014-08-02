#!/usr/bin/env perl

use warnings;
use strict;
use Getopt::Long;

my $r0  = 0;
my $r1  = 0;
my $D   = 0;
my $eps = 0;
my $t0  = 0;
my $t1  = 0;
my $help;
my ($fv, $a0, $a1);

usage() if (@ARGV < 6 or !GetOptions("eps=f", \$eps, "D=f", \$D, "r0=f", \$r0 , "r1=f", \$r1, "t0=i", \$t0, "t1=i", \$t1, "help|?", \$help) or (defined $help));

printf "Data input : EPS=%f, D=%f%%, r0=%f%%, r1=%f%%, t0=%dyrs, t1=%dyrs \n", $eps, $D, $r0, $r1, $t0, $t1;

$a0 = (1 + $r0/100)/(1 + $D/100);
$a1 = (1 + $r1/100)/(1 + $D/100);

$fv = $eps*((1 - $a0**$t0)/(1 - $a0) + ($a0**$t0)*(1 - $a1**$t1)/(1 - $a1));

printf "fair value = %f\n", $fv;

sub usage{
    print "Help :\n";
    print "--eps         = earning per share \n";
    print "--D           = discount rate \n";
    print "--r0          = rate0 \n";
    print "--r1          = rate1 \n";
    print "--t0          = t0 \n";
    print "--t1          = t1 \n";
    print "--help = help\n";
    exit 0;
}

