#!python

import argparse
import nagiosplugin
import boto3
import datetime


elbv2 = boto3.client('elbv2')
cloudwatch = boto3.client('cloudwatch')
ec2 = boto3.client('ec2')


# data acquisition

class TGInstanceMetric(nagiosplugin.Resource):

    def __init__(self, target_group_arn, metric_name, statistic, period, volume):
        self.target_group_arn = target_group_arn
        self.metric_name = metric_name
        self.period = period
        self.statistic = statistic
        self.volume = volume

    # Perform the service check
    # Returns a nagiosplugin.Metric for each instance in the Target Group
    def probe(self):
        instances = self.get_instances_in_target_group(self.target_group_arn)
        results = []

        if self.volume:
            volumes = self.get_volumes_for_instances(instances, self.volume)

            for volume_id in volumes:
                dps = self.get_volume_metric(volume_id, self.metric_name, self.statistic, self.period)
                dp = self.get_most_recent_data_point(dps, self.statistic)
                results.append(nagiosplugin.Metric(volume_id, dp, context=self.metric_name))

        else:

            for instance_id in instances:
                dps = self.get_instance_metric(instance_id, self.metric_name, self.statistic, self.period)
                dp = self.get_most_recent_data_point(dps, self.statistic)
                results.append(nagiosplugin.Metric(instance_id, dp, context=self.metric_name))

        return results

    # Returns a list of ids of instances in the supplied target group
    def get_instances_in_target_group(self, target_group_arn):
        response = elbv2.describe_target_health(
            TargetGroupArn = target_group_arn
        )
        instance_ids = []
        for target_health_description in response['TargetHealthDescriptions']:
            instance_ids.append(target_health_description['Target']['Id'])

        return instance_ids


    # Returns a list of volume_ids attached to the supplied instances with the supplied volume name
    def get_volumes_for_instances(self, instance_ids, volume_name):
        response = ec2.describe_instances(
            InstanceIds = instance_ids
        )

        volume_ids = []
        for instance in response['Reservations'][0]['Instances']:
            for volume in instance['BlockDeviceMappings']:
                print(volume['DeviceName'])
                if volume['DeviceName'] == volume_name:
                    volume_ids.append(volume['Ebs']['VolumeId'])

        return volume_ids


    # Returns trhe most recent data point from a list of data points
    def get_most_recent_data_point(self, data_points, statistic):
        most_recent_timestamp = datetime.datetime(1970, 1, 1)
        most_recent_reading = ''

        for data_point in data_points:
            if (data_point['Timestamp'].replace(tzinfo=None) > most_recent_timestamp):
                most_recent_timestamp = data_point['Timestamp'].replace(tzinfo=None)
                most_recent_reading = data_point[statistic]

        return most_recent_reading

    def get_instance_metric(self, instance_id, metric_name, statistic, period):
        response = cloudwatch.get_metric_statistics(
            Namespace = 'AWS/EC2',
            MetricName = metric_name,
            Dimensions = [
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                }
            ],
            StartTime = datetime.datetime.utcnow() - datetime.timedelta(seconds=600),
            EndTime = datetime.datetime.utcnow(),
            Period = period,
            Statistics = [ statistic ]
        )
        return response['Datapoints']

    def get_volume_metric(self, volume_id, metric_name, statistic, period):
        response = cloudwatch.get_metric_statistics(
            Namespace = 'AWS/EBS',
            MetricName = metric_name,
            Dimensions = [
                {
                    'Name': 'VolumeId',
                    'Value': volume_id
                }
            ],
            StartTime = datetime.datetime.utcnow() - datetime.timedelta(seconds=600),
            EndTime = datetime.datetime.utcnow(),
            Period = period,
            Statistics = [ statistic ]
        )
        return response['Datapoints']


class TGInstanceMetricSummary(nagiosplugin.Summary):

    def ok(self, results):
        return 'All instances are within the given thresholds '


@nagiosplugin.guarded
def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-t', '--targetgroup', metavar='target_group_arn', default='', required=True,
                      help='ARN of the target group to query')
    argp.add_argument('-m', '--metric', metavar='metric', default='', required=True,
                      help='Name of the metric to query')
    argp.add_argument('-w', '--warning', metavar='RANGE', default='',
                      help='return warning if load is outside RANGE')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='',
                      help='return critical if load is outside RANGE')
    argp.add_argument('-p', '--period', metavar='PERIOD', default=60, type=int,
                      help='metric resolution in seconds')
    argp.add_argument('-s', '--statistic', metavar='Average/Minimum/etc', default='Average',
                      help='statistic to monitor')
    argp.add_argument('-v', '--volume', metavar='Volume Name', default=None,
                      help='Volume to get metric of')
    args = argp.parse_args()

    # Perform the check
    check = nagiosplugin.Check(
        TGInstanceMetric(args.targetgroup, args.metric, args.statistic, args.period, args.volume),
        nagiosplugin.ScalarContext(args.metric, args.warning, args.critical),
        TGInstanceMetricSummary()
    )
    check.main()

if __name__ == '__main__':
    main()
