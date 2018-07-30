#!/usr/bin/env python

import argparse, nagiosplugin
import json
import urllib.request

api_key = 'AIzaSyBBFYqrJpq1Kp0pi_LR9pC5pnTvT1k-Jxo'

class GooglePageSpeedMetric(nagiosplugin.Resource):
    def __init__(self, url, strategy):
        self.url = url
        self.strategy = strategy

    # Perform the service check
    # Returns a nagiosplugin.Metric for each instance in the Target Group
    def probe(self):
        pagespeed_url = 'https://www.googleapis.com/pagespeedonline/v1/runPagespeed?key=' + api_key + '&url=' + self.url + '&strategy=' + self.strategy

        request = urllib.request.Request(pagespeed_url)
        result = urllib.request.urlopen(request)
        body = result.read().decode("utf-8")
        results = json.loads(body)
        print(results)

        return [
            nagiosplugin.Metric('score', results['score'], min=0, max=100),
            nagiosplugin.Metric('numberResources', results['pageStats']['numberResources'], min=0, context='default'),
            nagiosplugin.Metric('totalRequestBytes', int(results['pageStats']['totalRequestBytes']), min=0, context='default'),
            nagiosplugin.Metric('numberStaticResources', results['pageStats']['numberStaticResources'], min=0, context='default'),
            nagiosplugin.Metric('htmlResponseBytes', int(results['pageStats']['htmlResponseBytes']), min=0, context='default'),
            #nagiosplugin.Metric('textResponseBytes', int(results['pageStats']['textResponseBytes']), min=0, context='default'),
            nagiosplugin.Metric('cssResponseBytes', int(results['pageStats']['cssResponseBytes']), min=0, context='default'),
            nagiosplugin.Metric('imageResponseBytes', int(results['pageStats']['imageResponseBytes']), min=0, context='default'),
            nagiosplugin.Metric('javascriptResponseBytes', int(results['pageStats']['javascriptResponseBytes']), min=0, context='default'),
            nagiosplugin.Metric('otherResponseBytes', int(results['pageStats']['otherResponseBytes']), min=0, context='default'),
            nagiosplugin.Metric('numberJsResources', results['pageStats']['numberJsResources'], min=0, context='default'),
            nagiosplugin.Metric('numberCssResources', results['pageStats']['numberCssResources'], min=0, context='default')
        ]



class GooglePageSpeedMetricSummary(nagiosplugin.Summary):

    def ok(self, results):
        dump(results)
        return 'All instances are within the given thresholds '

@nagiosplugin.guarded
def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-u', '--url', default='', required=True,
                      help='URL to query (including protocol)')
    argp.add_argument('-s', '--strategy', default='desktop', required=True,
                      help='Strategy to use (desktop/mobile)')
    argp.add_argument('-w', '--warning', metavar='RANGE', default='',
                      help='return warning if load is outside RANGE')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='',
                      help='return critical if load is outside RANGE')
    args = argp.parse_args()

    # Perform the check
    check = nagiosplugin.Check(
        GooglePageSpeedMetric(args.url, args.strategy),
        nagiosplugin.ScalarContext('score', args.warning, args.critical),
    )
    check.main()

if __name__ == '__main__':
    main()
