import argparse
import ast
import datetime
import nagiosplugin
import boto3

cloudwatch = boto3.client('cloudwatch')


class Cloudwatch(nagiosplugin.Resource):

    def __init__(self, namespace, metric_name, dimensions, statistic, period):
        self.namespace = namespace
        self.metric_name = metric_name
        self.dimensions = ast.literal_eval(dimensions)
        self.statistic = statistic
        self.period = period

    def probe(self):
        dp = self.get_most_recent_data_point(self.namespace, self.metric_name, self.dimensions, self.statistic, self.period)

        return nagiosplugin.Metric(self.metric_name, dp)


    def parse_dimensions(self):
        ret = []
        for key, value in self.dimensions.items():
            ret.append({
                'Name': key,
                'Value': value
            })

        return ret

    def get_most_recent_data_point(self, namespace, metric_name, dimensions, statistic, period):
        most_recent_timestamp = datetime.datetime(1970, 1, 1)
        most_recent_reading = ''
        data_points = self.get_recent_data_points(namespace, metric_name, dimensions, statistic, period)

        for data_point in data_points:
            if (data_point['Timestamp'].replace(tzinfo=None) > most_recent_timestamp):
                most_recent_timestamp = data_point['Timestamp'].replace(tzinfo=None)
                most_recent_reading = data_point[statistic]

        return most_recent_reading

    def get_recent_data_points(self, namespace, metric_name, dimensions, statistic, period):
        dimensions = self.parse_dimensions()

        response = cloudwatch.get_metric_statistics(
            Namespace = self.namespace,
            MetricName = self.metric_name,
            Dimensions = dimensions,
            StartTime = datetime.datetime.utcnow() - datetime.timedelta(seconds=600),
            EndTime = datetime.datetime.utcnow(),
            Period = self.period,
            Statistics = [ self.statistic ]
        )

        return response['Datapoints']


@nagiosplugin.guarded
def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-n', '--namespace', metavar='NAMESPACE', default='AWS/EC2',
                      help='the namespace containing the metric')
    argp.add_argument('-m', '--metric', metavar='metric', default='', required=True,
                      help='the name of the metric to query')
    argp.add_argument('-d', '--dimension', metavar='{\'InstanceId\': \'i-123456790abcdef\'}', default='{}',
                      help='the dimension to query')
    argp.add_argument('-p', '--period', metavar='PERIOD', default=60, type=int,
                      help='the metric resolution in seconds')
    argp.add_argument('-s', '--statistic', metavar='Average/Minimum/etc', default='Average',
                      help='statistic to monitor')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='',
                      help='return critical if load is outside RANGE')
    argp.add_argument('-w', '--warning', metavar='RANGE', default='',
                      help='return warning if load is outside RANGE')
    args = argp.parse_args()

    # Perform the check
    check = nagiosplugin.Check(
        Cloudwatch(args.namespace, args.metric, args.dimension, args.statistic, args.period),
        nagiosplugin.ScalarContext(args.metric, args.warning, args.critical)
    )
    check.main()

if __name__ == '__main__':
    main()
