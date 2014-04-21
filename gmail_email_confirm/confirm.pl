#!/usr/bin/perl

use strict;
use warnings;
use FindBin qw/$Bin/;
use Mail::IMAPClient;
use IO::Socket::SSL;
use Email::MIME;
use LWP::UserAgent;
use URI::Find;

# Connect to IMAP server
my $imap = Mail::IMAPClient->new(
  Server   => 'imap.gmail.com',
  User     => $ENV{GMAIL_USER},
  Password => $ENV{GMAIL_PASS},
  Port     => 993,
  Ssl      => 1,
  Peek     => 1,
  Ignoresizeerrors => 1,
) or die "Cannot connect through IMAPClient: $!";

my $ua = LWP::UserAgent->new(
    agent => 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13',
    cookie_jar  => {},
    timeout     => 60,
);

my %done;
my $finder = URI::Find->new(sub {
    my ($uri, $ori_uri) = @_;
    return $ori_uri if $done{$uri};
    $done{$uri} = 1;
    if ($uri =~ /^http/) { # start with http
        return if $uri =~ /\.(gif|jpg|png|dtd)$/i;
        print "Get URL $uri\n";
        $ua->get($uri);
    }
} );

$imap->select("INBOX");
my @unseen = $imap->unseen or print "No unseen messages in inbox\n";
foreach my $msg_id (@unseen) {

    my $str = $imap->message_string($msg_id)
        or die "$0: message_string: $@";

    my $parsed = Email::MIME->new($str);
    my $subject = $parsed->header("Subject");

    print "Checking $subject\n";

    my @body  = ($parsed->body);
    my @parts = $parsed->parts;
    foreach (@parts) { push @body, $_->body }

    foreach my $body (@body) {
        $finder->find(\$body);
    }

    $imap->see($msg_id);
}

# Say so long
$imap->logout();

1;
