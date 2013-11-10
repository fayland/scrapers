#!/usr/bin/perl

use strict;
use warnings;
use WWW::Mechanize;
use HTML::TreeBuilder;
use Text::CSV_XS;
use Data::Dumper;
use FindBin qw/$Bin/;
use Encode;

# ua
my $ua = WWW::Mechanize->new(
    stack_depth => 1,
    agent => 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/5.0)',
    cookie_jar => {},
    autocheck => 0,
);

$ua->get('http://www.wisdomtree.com/etfs/');
die $ua->res->status_line unless $ua->success;

my %urls; my @urls;
my $tree = HTML::TreeBuilder->new_from_content( $ua->content );
my @us = $tree->look_down(_tag => 'a', href => qr'fund-details');
foreach my $u (@us) {
    next if exists $urls{$u->attr('href')};
    push @urls, $u->attr('href');
    $urls{$u->attr('href')} = $u->as_trimmed_text;
}
$tree = $tree->delete;

open(my $fh, '>:utf8', "$Bin/wisdomtree.csv");
my $csv = Text::CSV_XS->new({ binary => 1, sep_char => "\t" }) or
    die "Cannot use CSV: " . Text::CSV_XS->error_diag();
$csv->print($fh, ['ETF Ticker', 'ETF Description', 'Index Description']);
print $fh "\n";
foreach my $url (@urls) {
    $ua->get($url);
    unless ($ua->success) {
        print "# get $url failed: " . $ua->res->status_line . "\n";
        next;
    }
    print "# get $url OK\n";
    $tree = HTML::TreeBuilder->new_from_content( $ua->content );
    my $content = $tree->look_down(_tag => 'div', id => 'content');
    my $h1 = $content->look_down(_tag => 'h1');
    my $h2 = $content->look_down(_tag => 'h2');
    my $desc1; my $durl; my $tag = $h1 || $h2;
    while ($tag = $tag->right()) {
        last if defined $tag->{_tag} and ($tag->{_tag} eq 'script' or $tag->{_tag} eq 'div');
        $durl = $tag->look_down(_tag => 'a', href => qr'index-details') unless $durl;
        my $text = $tag->as_trimmed_text; $text =~ s/^\s+|\s+$//g;
        $desc1 .=  $text . "\n";
    }
    my $desc2;
    if ($durl) {
        $durl = $durl->attr('href');
        $ua->get($durl);
        unless ($ua->success) {
            print "# get $durl failed: " . $ua->res->status_line . "\n";
            next;
        }
        print "# get $durl OK\n";
        my $tree2 = HTML::TreeBuilder->new_from_content( $ua->content );
        $content = $tree2->look_down(_tag => 'div', id => 'content');

        $h2 = $content->look_down(_tag => 'h2');
        $tag = $h2;
        while ($tag = $tag->right()) {
            last if defined $tag->{_tag} and ($tag->{_tag} eq 'ul' or $tag->{_tag} eq 'table' or $tag->{_tag} eq 'div' or $tag->{_tag} eq 'script');
            my $text = $tag->as_trimmed_text; $text =~ s/^\s+|\s+$//g;
            $desc2 .=  $text . "\n";
        }

        $tree2 = $tree2->delete;
        $desc2 =~ s/\xA0/ /g;
        $desc2 =~ s/^\s+|\s+$//g;
    }
    $desc1 =~ s/\xA0/ /g;
    $desc1 =~ s/^\s+|\s+$//g;
    $tree = $tree->delete;

    $csv->print($fh, [$urls{$url}, $desc1, $desc2]);
    print $fh "\n";

    sleep 5; # so no blocking
}
close($fh);
$csv->eof or $csv->error_diag();

1;