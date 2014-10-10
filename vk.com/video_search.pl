#!/usr/bin/env perl

use strict;
use warnings;
use WWW::Mechanize::GZip;
use JSON;
use Data::Dumper;

my $DEBUG = 1;

# config
my $client_id = $ENV{VK_CLIENTID};
my $username  = $ENV{VK_USERNAME};
my $password  = $ENV{VK_PASSWORD};
my $phone_verify = $ENV{VK_PHONE};
my $search_term = shift @ARGV or die;

my $ua = WWW::Mechanize::GZip->new();
$ua->agent('Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16');
$ua->default_header('Accept' => 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8');
$ua->default_header('Accept-Language' => 'en-us,en;q=0.5');
$ua->cookie_jar({ file => "/tmp/cookies.vk_com.txt" });

my $access_token = '';
if (open(my $fh, '<', '/tmp/access_token.vk_com.txt')) {
    $access_token = <$fh>; chomp($access_token);
    close($fh);
}

if ($access_token) {
    my $st = __do_api_request($ua, $access_token, $search_term);
    exit if $st; # all done
}

# http://vk.com/dev/auth_mobile
my $url = "https://oauth.vk.com/authorize?client_id=$client_id&scope=video&redirect_uri=http://api.vk.com/blank.html&response_type=token&v=5.25";
my $res = $ua->get($url);
print "# get $url\n" if $DEBUG;

if ($ua->content =~ /email/ and $ua->content =~ /pass/) {
    print "# Login...\n" if $DEBUG;
    $res = $ua->submit_form(
        with_fields => {
            email => $username,
            pass  => $password
        }
    );
    if ($ua->content =~ /In order to confirm ownership of the page/) {
        print "# fix phone verify\n" if $DEBUG;
        $res = $ua->submit_form(
            with_fields => {
                code => $phone_verify
            }
        );
    }
}

# http://api.vk.com/blank.html#access_token=...&expires_in=86400&user_id=...
my $redirect_uri = $ua->base->as_string;
($access_token) = ($redirect_uri =~ m{access_token=(\w+)});
die "[FIXME] Can't get the token\n" unless $access_token;

print "# get token as $access_token\n" if $DEBUG;
open(my $fh, '>', '/tmp/access_token.vk_com.txt');
print $fh $access_token;
close($fh);

my $st = __do_api_request($ua, $access_token, $search_term);

sub __do_api_request {
    my ($ua, $access_token, $search_term) = @_;

    # http://vk.com/dev/video.search
    my $url = "https://api.vk.com/method/video.search?q=" . uri_escape($search_term) . "&sort=1&filters=long&count=200&access_token=$access_token";
    print "## get $url\n" if $DEBUG;
    my $res = $ua->get($url);
    my $data = decode_json($res->content);
    return if $data->{error}; # token expired maybe

    my @videos;
    foreach my $item (@{$data->{response}}) {
        push @videos, join('_', $item->{owner_id}, $item->{id});
    }

    $url = "https://api.vk.com/method/video.get?videos=" . join(',', @videos) . "&access_token=$access_token";
    print "## get $url\n" if $DEBUG;
    $res = $ua->get($url);
    $data = decode_json($res->content);
    return if $data->{error};

    foreach my $item (@{$data->{response}}) {
        next if $item =~ /^\d+$/; # first element is a number

        print Dumper(\$item);
    }

    return 1;
}