#!/usr/bin/perl

# Author: Fayland Lam (fayland@gmail.com)

use strict;
use warnings;
use LWP::UserAgent;
use Encode;
use FindBin qw/$Bin/;
use HTML::TreeBuilder;
use Data::Dumper;
use DBI;

$| = 1;

my $ua = LWP::UserAgent->new(
    agent => 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/5.0)',
    timeout => 60,
);
# $ua->proxy('http', 'socks://127.0.0.1:9050');

my $dbh = DBI->connect('DBI:mysql:fayland', 'root', $ENV{MYSQL_ROOT_PASS}, { PrintError => 1, RaiseError => 1, AutoCommit => 1 })
    or die "Can't connect mysql.\n";

my $url = 'http://www.jqball.com/result.htm';
my $res = $ua->get($url);
die $res->status_line unless $res->is_success;

my $tree = HTML::TreeBuilder->new_from_content( decode('gb2312', $res->content) );
my @links = $tree->look_down(_tag => 'a', target => 'result_in');
@links = map { $_->attr('href') } @links;
@links = grep { /2013/ } @links;
$tree = $tree->delete;

my $insert_sth = $dbh->prepare("INSERT IGNORE INTO corners (`date`, event, host_team, guest_team, host_corners, guest_corners) VALUES (?, ?, ?, ?, ?, ?)");

foreach my $link (@links) {
    print "# on $link\n";
    $res = $ua->get('http://www.jqball.com/' . $link);
    die $res->status_line unless $res->is_success;

    $tree = HTML::TreeBuilder->new_from_content( decode('gb2312', $res->content) );
    my @trs = $tree->look_down(_tag => 'table')->look_down(_tag => 'tr');
    shift @trs; shift @trs;
    foreach my $tr (@trs) {
        my @tds = $tr->look_down(_tag => 'td');
        @tds = map { $_->as_trimmed_text } @tds;
        next unless @tds == 7;
        print Dumper(\@tds);
        my ($h, $g) = split(/\s*\-\s*/, $tds[2]);
        die unless $g;
        next if $tds[5] eq "\x{53d6}\x{6d88}"; # Cancelled
        my ($hc, $gc) = split(/\s*\-\s*/, $tds[5]);
        die unless defined $gc;
        $tds[1] =~ s/^\[|\]$//g;
        $insert_sth->execute("2013-" . $tds[0], $tds[1], $h, $g, $hc, $gc) or die $dbh->errstr;
    }
    $tree = $tree->delete;

    sleep 5;
}

1;