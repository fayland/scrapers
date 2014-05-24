#!/usr/bin/perl

use strict;
use warnings;
use FindBin qw/$Bin/;
use HTML::TreeBuilder;
use Text::CSV_XS;
use Digest::MD5 qw/md5_hex/;
use WWW::Mechanize::GZip;
use Encode qw/decode encode/;
use Data::Dumper;

my $csv = Text::CSV_XS->new({ binary => 1 }) or
    die "Cannot use CSV: " . Text::CSV_XS->error_diag();
open(my $csvfh, '>:utf8', "$Bin/data.csv");
$csv->print($csvfh, [ 'BARCODE', 'INGREDIENTS', 'PRODUCT NAME', 'IMAGE' ]);
print $csvfh "\n";

my $ua = WWW::Mechanize::GZip->new(
    agent => 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)',
    cookie_jar  => {},
    stack_depth => 1,
    timeout     => 15
);

mkdir("$Bin/uploads") unless -d "$Bin/uploads";
mkdir("$Bin/html") unless -d "$Bin/html";

my $file = shift @ARGV;
open(my $fh, '<', $file) or die "Can't open $file: $!\n";
while (my $barcode = <$fh>) {
    $barcode =~ s/^\s+|\s+$//g;
    next if $barcode eq 'Barcode';

    print "\n\n\n";

    my $url = "http://search.rakuten.co.jp/search/mall?sitem=" . $barcode . "&g=0&myButton.x=0&myButton.y=0&v=2&s=1&p=1&min=&max=&sf=0&st=A&nitem=&grp=product";
    my $c = get_url($ua, $url);
    my $tree = HTML::TreeBuilder->new_from_content($c);
    my @rsrSResultPhoto = $tree->look_down(_tag => 'div', class => 'rsrSResultPhoto');
    @rsrSResultPhoto = map { $_->look_down(_tag => 'a', href => qr'http') } @rsrSResultPhoto;
    @rsrSResultPhoto = map { $_->attr('href') } @rsrSResultPhoto;
    $tree = $tree->delete;

    unless (@rsrSResultPhoto) {
        print "## MISSING results for $barcode\n";
        next;
    }

    my ($name, $ingredients, $image, $matched_url);
    foreach my $in_url (@rsrSResultPhoto) {
        $matched_url = $in_url;
        $name = '';
        $ingredients = '';
        $image = '';

        $c = get_url($ua, $in_url);
        eval {
            $c = encode('utf8', decode('EUC-JP', $c));
        };
        # print encode('utf8', decode('EUC-JP', $c));
        $tree = HTML::TreeBuilder->new_from_content($c);
        my @trs = $tree->look_down(_tag => 'tr');
        while (1) {
            last unless @trs;
            my $tr = shift @trs;
            my @_tr = $tr->look_down(_tag => 'tr');
            next if @_tr > 1;

            my @tds = $tr->look_down(_tag => qr/^t[hd]$/);
            @tds = map { $_->as_trimmed_text } @tds;
            @tds = map { s/\xA0/ /g; s/^\s+|\s+$//g; $_ } @tds;
            @tds = grep { length($_) } @tds;
            next unless @tds;

            # print Dumper(\@tds);
            if ($tds[0] eq '商品名') {
                $name = $tds[1];
            } elsif ($tds[0] =~ /原材料/ or $tds[0] =~ /成分/) {
                $ingredients = $tds[1] unless $ingredients;
                if (@tds == 1) {
                    my $next_tr = (shift @trs)->as_trimmed_text;
                    $next_tr =~ s/\xA0/ /g; $next_tr =~ s/^\s+|\s+$//g;
                    $ingredients = $next_tr unless $ingredients;
                }
            }
        }

        if ($c =~ m{<B>原材料</B><BR>(.*?)<BR>}is) {
            $ingredients = $1;
        }
        if ($c =~ m{<p>【原材料名】<br>(.*?)</p>}) {
            $ingredients = $1;
        }

        unless ($name) {
            $name = $tree->look_down(_tag => 'span', class => 'content_title');
            $name = $name->as_trimmed_text if $name;
            $name =~ s/【\d+】// if $name;
        }

        my @images = $tree->look_down(_tag => 'a', class => qr/ImageMain/);
        @images = map { $_->attr('href') } @images;
        $image = $images[0] if @images;

        $tree = $tree->delete;

        last if $name and $ingredients and $image;
    }

    next unless $ingredients; # FIXME later

    die 'no image' unless $image;
    die 'no name' unless $name;
    die 'no ingredients' unless $ingredients;

    get_url($ua, $image, "$Bin/uploads/$barcode.jpg");

    eval {
        $ingredients = decode('utf8', $ingredients);
        $name = decode('utf8', $name);
    };
    $csv->print($csvfh, [ $barcode, $ingredients, $name, "uploads/$barcode.jpg", $matched_url ]);
    print $csvfh "\n";
}

close($csvfh);

sub get_url {
    my ($ua, $url, $image_file) = @_;

    my $file;
    if ($image_file) {
        $file = $image_file;
    } else {
        $file = md5_hex($url);
        $file = "$Bin/html/$file.html";
    }

    if (-e $file and -s $file and -M $file < 60) { # at most store 2 weeks?
        return if $image_file; # do not need content

        print "[$$] # open $file for $url\n";
        my $content = _read_file($file);
        return $content if index($content, '</html>') > -1; # avoid incomplete HTML
    }

    print "[$$] # get $url to $file\n";
    my $tried_times;
    while (1) {
        $tried_times++;
        return if $tried_times > 3; # most try 5 b/c it maybe remote server issue

#        my $proxy = $proxy[rand(scalar @proxy)];
#        $proxy = 'socks://127.0.0.1:9050';
#        $ua->proxy(['http', 'https'], $proxy);
        $ua->get($url);
        unless ($ua->success) {
            warn "[$$] # get $url err: " . $ua->res->status_line . "\n";
            next;
        }

        my $content = $ua->res->content;
        open(my $fh, '>', $file);
        binmode($fh) if $image_file;
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