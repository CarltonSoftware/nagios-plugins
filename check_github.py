#!/usr/bin/env python

import argparse, nagiosplugin
import json
import urllib.request


class GithubMetric(nagiosplugin.Resource):

    # Perform the service check
    # Returns a nagiosplugin.Metric for each instance in the Target Group
    def probe(self):
        status_url = 'https://status.github.com/api/status.json'

        request = urllib.request.Request(status_url)
        result = urllib.request.urlopen(request)
        body = result.read().decode("utf-8")
        status = json.loads(body)

        yield nagiosplugin.Metric('status', status, context='status')


class GithubContext(nagiosplugin.Context):

    def evaluate(self, metric, resource):
        status = metric.value['status']

        if status == 'good':
            return nagiosplugin.result.Result(nagiosplugin.state.Ok, 'Github is running OK', metric)
        elif status == 'minor':
            return nagiosplugin.result.Result(nagiosplugin.state.Warn, 'Github are reporting minor problems', metric)
        elif status == 'major':
            return nagiosplugin.result.Result(nagiosplugin.state.Critical, 'Github are reporting major problems', metric)

        return nagiosplugin.result.Result(nagiosplugin.state.Unknown, '', metric)

@nagiosplugin.guarded
def main():
    # Perform the check
    check = nagiosplugin.Check(
        GithubMetric(),
        GithubContext('status')
    )
    check.main()

if __name__ == '__main__':
    main()
