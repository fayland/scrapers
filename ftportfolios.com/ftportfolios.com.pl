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

open(my $fh, '<', "$Bin/FTLinks.csv");
my @urls = <$fh>;
close($fh);
chomp(@urls);


open($fh, '>:utf8', "$Bin/ftportfolio.csv");
my $csv = Text::CSV_XS->new({ binary => 1, sep_char => "\t" }) or
    die "Cannot use CSV: " . Text::CSV_XS->error_diag();
$csv->print($fh, ['Ticker', 'Investment Objective', 'Index Description']);
print $fh "\n";
foreach my $url (@urls) {
    # http://www.ftportfolios.com/Retail/etf/etfsummary.aspx?Ticker=FGD
    my ($ticker) = ($url =~ /Ticker=(\S+)$/);
#    next unless $ticker eq 'FEX';
    $ua->get($url);
    unless ($ua->success) {
        print "# get $url failed: " . $ua->res->status_line . "\n";
        next;
    }
    print "# get $url OK\n";
    my $tree = HTML::TreeBuilder->new_from_content( $ua->content );
    my $InvestmentStrategy = $tree->look_down(_tag => 'span', id => 'CEFControlPlaceHolder1_ctl00_lblInvestmentStrategy');
    $InvestmentStrategy = $InvestmentStrategy->as_trimmed_text;
    $InvestmentStrategy =~ s/\xA0/ /g;
    my $ul = $tree->look_down(_tag => 'ul', class => 'CEFPagesBody');
    unless ($ul) {
        $ul = $tree->look_down(_tag => 'td', class => 'CEFPagesBody', sub {
            $_[0]->look_down(_tag => 'ul')
        });
    }
    my @lis = $ul->look_down(_tag => 'li');
    @lis = map { $_->as_trimmed_text } @lis;
    $tree = $tree->delete;
    
    $csv->print($fh, [$ticker, "Investment Objective/Strategy - $InvestmentStrategy", join("\n", @lis)]);
    print $fh "\n";
    
    sleep 5; # so no blocking
}
close($fh);
$csv->eof or $csv->error_diag();

1;