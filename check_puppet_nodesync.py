#!/usr/bin/env python3
# coding=utf-8

import argparse
import datetime
import logging
import nagiosplugin
import pypuppetdb
import re

_log = logging.getLogger('nagiosplugin')


class ListContext(nagiosplugin.Context):
	def __init__(self, name, text, state=nagiosplugin.state.Critical, result_cls=nagiosplugin.result.Result):  # pylint: disable=too-many-arguments
		self.text = text
		self.state = state
		fmt_metric = ''
		super(ListContext, self).__init__(name, fmt_metric, result_cls)

	def evaluate(self, metric, resource):
		if len(metric.value) == 0:
			return self.result_cls(nagiosplugin.state.Ok, "No hosts %s" % self.text, metric)
		else:
			d = ",".join(metric.value)
			return self.result_cls(self.state, "Hosts: %s %s" % (d, self.text), metric)


class PuppetNodeSync(nagiosplugin.Resource):
	def __init__(self, args):
		self.args = args

		self.now = datetime.datetime.now(datetime.timezone.utc)

	def check_in_sync(self, time, max_diff=60):
		dt = (self.now - time) / datetime.timedelta(minutes=1)

		if dt > max_diff:
			return False
		else:
			return True

	def probe(self):
		_log.debug("Connecting to PuppetDB on %s:%s", self.args.db, self.args.port)
		pdb = pypuppetdb.connect(host=self.args.db, port=self.args.port, timeout=self.args.timeout)

		nodes = pdb.nodes()

		node_status = dict(total=[], ignored=[], in_sync=[], no_sync=[], no_report=[], unchanged=[], failed=[], changed=[])

		r_exc = None

		if self.args.exclude is not None:
			r_exc = re.compile(self.args.exclude)

		for node in nodes:
			nodename = str(node)
			_log.debug("Processing node %s", nodename)
			node_status["total"].append(nodename)

			if r_exc is not None and r_exc.match(nodename):
				node_status["ignored"].append(nodename)
				continue

			_log.debug("Querying PuppetDB reports for node %s", nodename)
			d = pdb._query(endpoint="reports", query='["and",["=","certname","%s"],["=","latest_report?",true]]' % str(node))
			if len(d) != 1:
				_log.debug("Found no report for hostname %s", nodename)
				node_status["no_report"].append(nodename)
				continue
			else:
				status = d[0]["status"]
				_log.debug("Found report for hostname %s with status: %s", nodename, status)
				if status == "unchanged":
					node_status["unchanged"].append(nodename)
				elif status == "failed":
					node_status["failed"].append(nodename)
					# print(str(node), node.report_timestamp, status, "FAILED")
				elif status == "changed":
					node_status["changed"].append(nodename)
				else:
					raise RuntimeError("Unknown status %s" % status)

				if self.check_in_sync(node.report_timestamp, self.args.sync_time):
					node_status["in_sync"].append(nodename)
					_log.debug("Hostname %s is in sync", nodename)
				else:
					node_status["no_sync"].append(nodename)
					_log.debug("Hostname %s is out of sync", nodename)

		yield nagiosplugin.Metric('nodes_total', len(node_status["total"]))
		yield nagiosplugin.Metric('nodes_ignored', len(node_status["ignored"]))
		yield nagiosplugin.Metric('nodes_changed', len(node_status["changed"]))
		yield nagiosplugin.Metric('nodes_unchanged', len(node_status["unchanged"]))
		yield nagiosplugin.Metric('nodes_failed', len(node_status["failed"]))
		yield nagiosplugin.Metric('nodes_in_sync', len(node_status["in_sync"]))
		yield nagiosplugin.Metric('nodes_no_sync', len(node_status["no_sync"]))

		yield nagiosplugin.Metric('failed', node_status["failed"])
		yield nagiosplugin.Metric('no_sync', node_status["no_sync"])


@nagiosplugin.guarded
def main():
	argp = argparse.ArgumentParser()
	argp.add_argument("-d", "--db", help="PuppetDB Server name", default="localhost")
	argp.add_argument("-p", "--port", help="PuppetDB Server port", type=int, default=8080)
	argp.add_argument("-t", "--timeout", help="PuppetDB Server timeout", type=int, default=60)
	argp.add_argument("-v", "--verbose", help="Verbosity on checks", action='count', default=0)
	argp.add_argument("-e", "--exclude", help="Regular expression to exclude nodes", default=None)
	argp.add_argument("-s", "--sync-time", help="Time in minutes for nodes to be considered in sync", type=int, default=60)

	args = argp.parse_args()

	check = nagiosplugin.Check(PuppetNodeSync(args))
	check.add(nagiosplugin.ScalarContext('nodes_total'))
	check.add(nagiosplugin.ScalarContext('nodes_ignored'))
	check.add(nagiosplugin.ScalarContext('nodes_changed'))
	check.add(nagiosplugin.ScalarContext('nodes_unchanged'))
	check.add(nagiosplugin.ScalarContext('nodes_failed'))
	check.add(nagiosplugin.ScalarContext('nodes_in_sync'))
	check.add(nagiosplugin.ScalarContext('nodes_no_sync'))

	check.add(ListContext('failed', "failed", state=nagiosplugin.state.Critical))
	check.add(ListContext('no_sync', "out of sync", state=nagiosplugin.state.Warn))

	check.main(args.verbose, timeout=args.timeout)


if __name__ == '__main__':
	main()
