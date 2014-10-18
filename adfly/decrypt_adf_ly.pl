#!/usr/bin/perl

use strict;
use warnings;
use LWP::UserAgent;
use MIME::Base64;

our $DEBUG = 1;

my $url = shift @ARGV or die "url is required.";
my $ua = LWP::UserAgent->new();

$url = convert_adfly($ua, $url);
print $url . "\n";

sub convert_adfly {
    my ($ua, $url) = @_;

    print "## get $url\n" if $DEBUG;
    my $resp = $ua->get($url);
    unless ($resp->is_success) {
        print STDERR "## get $url error: " . $resp->status_line . "\n";
        return;
    }

    # var ysmm = 'ZpDwBWobd0HhRmwLOlix8Wvadm39dS3MNyjcADuMe0mYljwNc3H8lizdavG0F2ybZjS5';
    my ($ysmm) = ($resp->decoded_content =~ /ysmm\s*\=\s*[\'\"]([^\'\"]+)[\'\"]/);
    unless ($ysmm) {
        print STDERR "FIXME...";
        return;
    }

    my ($C, $h) = ('', '');
    my @ysmm = split(//, $ysmm);
    foreach my $s (0 .. $#ysmm) {
        if ($s % 2 == 0) {
            $C .= $ysmm[$s];
        } else {
            $h = $ysmm[$s] . $h;
        }
    }

    my $sec = decode_base64($C . $h);
    $sec = substr($sec, 2);

    return $sec;
}