#!/usr/bin/perl

use strict;
use warnings;
use LWP::UserAgent;
use Text::CSV_XS;
use JSON::XS;
use FindBin qw/$Bin/;
use Data::Dumper;

my $access_token = '2.00WsUooC2Qf7MD1e8da3b1d2tRA3UB';
mkdir("$Bin/data") unless -d "$Bin/data";

open(my $fh, '<', "$Bin/symbols.txt");
my @symbols = <$fh>;
close($fh);
chomp(@symbols);

# May 10: sz002086
# May 11: sh600105
# May 12: sh600815

my $ua = LWP::UserAgent->new(
    agent => 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/5.0)',,
);

my $csv = Text::CSV_XS->new({ binary => 1 }) or
    die "Cannot use CSV: " . Text::CSV_XS->error_diag();
open(my $out, '>', "$Bin/data.csv");
$csv->print($out, ['Symbol', 'UID', 'gender', 'followers_count', 'friends_count', 'statuses_count', 'favourites_count', 'created_at']);
print $out "\n";

foreach my $symbol (@symbols) {
    next if $symbol eq '990018';
    my $fd = substr($symbol, 0, 1);
    $symbol = 'sz' . $symbol if $fd < 6;
    $symbol = 'sh' . $symbol if $fd > 5;
    $symbol = 'jl000919' if $symbol eq 'sz000919';
    $symbol = 'hengdian002056' if $symbol eq 'sz002056';
    $symbol = 'sz0025700' if $symbol eq 'sz002570';
    $symbol = 'sz0025741' if $symbol eq 'sz002574';
    $symbol = 'hd601113'  if $symbol eq 'sh601113';
    $symbol = 'dckj601208' if $symbol eq 'sh601208';
    $symbol = 'tk601233' if $symbol eq 'sh601233';

    # get uid
    my $uid;
    my %map = (
        'sz002306' => 1984611295,
        'sz002569' => 2542995207,
        'sz300244' => 2231521293,
        'sh600287' => 1984560443,
        'sh601169' => 1984564857,
        'sh601258' => 2144146755,
        'sh601599' => 2166128291,
    );
    if (exists $map{$symbol}) {
        $uid = $map{$symbol};
    } elsif (-e "$Bin/data/$symbol.uid.txt") {
        open($fh, '<', "$Bin/data/$symbol.uid.txt");
        $uid = <$fh>; chomp($uid);
        close($fh);
        unlink("$Bin/data/$symbol.uid.txt") unless $uid;
    } else {
        my $url = "http://weibo.com/" . $symbol;
        my $resp = ua_get_with_retries($ua, $url);
        next unless $resp;

        # scope.redirect = "http%3A%2F%2Fweibo.com%2Fu%2F1984596951";
        ($uid) = ($resp->decoded_content =~ /\%2Fu\%2F(\d+)/);
        open($fh, '>', "$Bin/data/$symbol.uid.txt");
        print $fh $uid;
        close($fh);
    }

    die unless $uid;

    my $content;
    if (-e "$Bin/data/$symbol.data.txt") {
        open($fh, '<', "$Bin/data/$symbol.data.txt");
        $content = do {
            local $/;
            <$fh>;
        };
        close($fh);
    } else {
        # https://api.weibo.com/2/users/show.json?uid=1984596951&access_token=2.00WsUooC2Qf7MD1f029fa149wDtnnD
        my $url = "https://api.weibo.com/2/users/show.json?uid=$uid&access_token=$access_token";
        my $resp = ua_get_with_retries($ua, $url);

  #      sleep 15; # rate limit

        next unless $resp;

        open($fh, '>', "$Bin/data/$symbol.data.txt");
        print $fh $resp->decoded_content;
        close($fh);
        $content = $resp->decoded_content;
    }

    my $data = decode_json($content);

    $csv->print($out, [$symbol, $uid, $data->{'gender'}, $data->{'followers_count'}, $data->{'friends_count'}, $data->{'statuses_count'}, $data->{'favourites_count'}, $data->{'created_at'}]);
    print $out "\n";

#    last if $symbol eq 'sz000413';
}

close($out);

sub ua_get_with_retries {
    my ($ua, $url) = @_;

    print "# get $url\n";
    my $resp = $ua->get($url); sleep 2;
    my $max_tried_times = 10; my $tried_times = 0;
    while (1) {
        return $resp if $resp->is_success;
        warn "Failed to get $url: " . $resp->status_line . "\n";
        $tried_times++;
        last if $tried_times > $max_tried_times;
        sleep $tried_times * 10;
        $resp = $ua->get($url);
    }
    return; ## all failed
}