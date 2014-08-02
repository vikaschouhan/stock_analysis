#!/usr/bin/env perl

use warnings;
use strict;
use Getopt::Long;
use IO::File;
use Data::Dumper;

my $fin;
my $finh = IO::File->new();

my $help;
my @columns;
my @columns_n;
my $data;

usage() if (@ARGV < 1 or !GetOptions("file=s", \$fin, "help|?", \$help) or (defined $help));
die "Couldn't open $fin\n" unless $finh->open("< $fin");

while(<$finh>){
    if(m/TICKER/){
        @columns_n = split ' ';
        print join("..", @columns_n), "\n";
    }
    #@columns = split ' ';
    #next if $columns[0] =~ /#/;
    #push @$data, $_;
}

#foreach my $entry (@$data){
#    print "NAME=>", $entry->{"ticker"}, " ", "dcf_eps=>", dcf_eps($entry), "\n";
#}


$finh->close();

#print Data::Dumper->Dump($data);

sub dcf_eps {
    my $params = shift;
    die "Invalid parameter in dcf_eps\n" if !defined($params);

    my $a0  = (1 + $params->{"r0"}/100)/(1 + $params->{"d"}/100);
    my $a1  = (1 + $params->{"r1"}/100)/(1 + $params->{"d"}/100);
    my $t0  = $params->{"t0"};
    my $t1  = $params->{"t1"};
    my $eps = $params->{"eps"};

    return $eps*((1 - $a0**$t0)/(1 - $a0) + ($a0**$t0)*(1 - $a1**$t1)/(1 - $a1));
}

sub usage{
    print "Help :\n";
    print "--file = input file name\n";
    print "--help = help\n";
    exit 0;
}

