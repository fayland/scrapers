#!/usr/bin/perl

# Author: Fayland Lam (fayland@gmail.com)

use strict;
use warnings;
use WWW::Mechanize;
use Encode;
use FindBin qw/$Bin/;
use HTML::TreeBuilder;
use Data::Dumper;
use Text::CSV_XS;
use Digest::MD5 'md5_hex';
use URI::Escape qw/uri_escape/;
use JSON::XS;

$| = 1;

my $ua = WWW::Mechanize->new(
    agent => 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/5.0)',
    cookie_jar => {},
    timeout => 60,
    autocheck => 0,
    stack_depth => 1,
);
$ua->proxy('http', 'socks://127.0.0.1:9050');

my $html_dir = "$Bin/html";
mkdir($html_dir) unless -d $html_dir; # cache store to avoid duplicated requests

my $csv = Text::CSV_XS->new({ binary => 1 }) or
    die "Cannot use CSV: " . Text::CSV_XS->error_diag();
open(my $fh, '>', "$Bin/data.csv");
$csv->print($fh, ['Date Submitted/Updated', 'Location of Hay', 'Postal Code', 'Hay type', 'Bale Type', 'Quantity Available', 'Price', 'per UNIT', 'RFV', 'Comments', 'Contact Name', 'Telephone', 'Email']); print $fh  "\n";

# login
$ua->post('http://hayexchange.com/login/s_login.php', [
    userid  => 'fayland',
    password => 'fayland',
    login => 'Login'
]);
# print Dumper(\$ua->res);
sleep 2;

my $c = get_url($ua, 'http://hayexchange.com/index.php', 'index');
my $tree = HTML::TreeBuilder->new_from_content($c);
my $table = $tree->look_down(_tag => 'table', 'cellpadding' => '2', width => '100%');
my @links = $table->look_down(_tag => 'a');
@links = map { $_->attr('href') } @links;
$tree = $tree->delete;

foreach my $link (@links) {
    print "# $link \n";
    my ($f) = ($link =~ /([^\/]+)\.php/);
    die $link unless $f;
    $c = get_url($ua, 'http://hayexchange.com' . $link, $f);
    $tree = HTML::TreeBuilder->new_from_content($c);
    my @dlinks = $tree->look_down(_tag => 'a', href => qr'display_detail_hay.php');
    @dlinks = map { $_->attr('href') } @dlinks;
    $tree = $tree->delete;

    foreach my $dlink (@dlinks) {
        print "# $link $dlink\n";
        my ($id) = ($dlink =~ /id=(\d+)/);
        die $dlink unless $id;

        $c = get_url($ua, 'http://www.hayexchange.com/' . $dlink, $id);

        my %data;
        $tree = HTML::TreeBuilder->new_from_content($c);
        my $table = $tree->look_down(_tag => 'table', width => '40%');
        my @trs = $table->look_down(_tag => 'tr');
        foreach my $tr (@trs) {
            my @tds = $tr->look_down(_tag => 'td');
            @tds = map { $_->as_trimmed_text } @tds;
            @tds = map { s/\xA0/ /g; $_; } @tds;
            if (@tds == 2) {
                $data{$tds[0]} = $tds[1];
            } elsif (@tds == 1 and $tds[0] =~ /^Comments\:/) {
                $data{Comments} = $tds[0];
                $data{Comments} =~ s/^Comments\:\s*//;
            } else {
                print Dumper(\@tds);
            }
        }
        $tree = $tree->delete;

        my $postalcode = '';
        my $address = delete $data{'Origin or Current Location of Hay:'};
        if ($address) {
            my $gurl = "http://maps.googleapis.com/maps/api/geocode/json?address=%22" . uri_escape($address) . "%22&sensor=false";
            $c = get_url($ua, $gurl, md5_hex($address));
            my $data = decode_json($c);
            # print Dumper(\$data);
            if ($data->{results}->[0]) {
                my @address_components = @{ $data->{results}->[0]->{address_components} };
                foreach my $ac (@address_components) {
                    next unless grep { $_ eq 'postal_code' } @{$ac->{types}};
                    $postalcode = $ac->{short_name};
                }
                # $address = $data->{results}->[0]->{formatted_address};
            }
        }

        my $price = delete $data{'Price:'}; # 325.00 per Ton
        $price =~ s/per//;
        ($price, my $xxx) = ($price =~ /^([\d\.]+)\s+(\w+$)/);
        die unless $xxx;

        print Dumper(\%data);

        $csv->print($fh, [
            delete $data{'Date Submitted/Updated:'},
            $address, $postalcode,
            delete $data{'Hay type:'},
            delete $data{'Bale Type:'},
            delete $data{'Quantity Available:'},
            $price, $xxx,
            delete $data{'RFV:'},
            delete $data{'Comments'},
            delete $data{'Contact:'},
            delete $data{'Telephone:'},
            delete $data{'Send Email:'}
        ]); print $fh "\n";
    }
}

close($fh);

sub get_url {
    my ($ua, $url, $file) = @_;

    $file = "$Bin/html/$file.html";

    if (-e $file and -s $file and -M $file < 60) { # at most store 2 weeks?
        print "[$$] # open $file for $url\n";
        my $content = _read_file($file);
        if ($url =~ /maps.googleapis.com/) {
            return $content if $content =~ /^\{/;
        } else {
            return $content if index($content, '</HTML>') > -1;
        }

    }

    print "[$$] # get $url to $file\n";
    my $tried_times;
    while (1) {
        $tried_times++;
        return if $tried_times > 5; # most try 5 b/c it maybe remote server issue

        $ua->get($url);
        sleep 5;
        unless ($ua->success) {
            warn "[$$] # get $url err: " . $ua->res->status_line . "\n";
            next;
        }

        my $content = $ua->content;
        die 'login' if $content =~ '>Log in<';
        open(my $fh, '>', $file);
        print $fh $content;
        close($fh);

        return $content;
    }
}

sub _read_file {
    my ($file) = @_;

    open(my $fh, '<', $file);
    my $content = do {
        local $/;
        <$fh>;
    };
    close($fh);
    return $content;
}

1;