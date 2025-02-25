# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError, HTTPError, InvalidURL, Timeout
from simplejson import JSONDecodeError
from six import iteritems
from six.moves.urllib.parse import urljoin, urlparse, urlsplit, urlunsplit

from datadog_checks.base import AgentCheck, ConfigurationError, is_affirmative

# Identifier for cluster master address in `spark.yaml`
MASTER_ADDRESS = 'spark_url'
DEPRECATED_MASTER_ADDRESS = 'resourcemanager_uri'

# Switch that determines the mode Spark is running in. Can be either
# 'yarn' or 'standalone'
SPARK_CLUSTER_MODE = 'spark_cluster_mode'
SPARK_DRIVER_MODE = 'spark_driver_mode'
SPARK_YARN_MODE = 'spark_yarn_mode'
SPARK_STANDALONE_MODE = 'spark_standalone_mode'
SPARK_MESOS_MODE = 'spark_mesos_mode'

# option enabling compatibility mode for Spark ver < 2
SPARK_PRE_20_MODE = 'spark_pre_20_mode'

# Service Checks
SPARK_STANDALONE_SERVICE_CHECK = 'spark.standalone_master.can_connect'
SPARK_DRIVER_SERVICE_CHECK = 'spark.driver.can_connect'
YARN_SERVICE_CHECK = 'spark.resource_manager.can_connect'
SPARK_SERVICE_CHECK = 'spark.application_master.can_connect'
MESOS_SERVICE_CHECK = 'spark.mesos_master.can_connect'

# URL Paths
YARN_APPS_PATH = 'ws/v1/cluster/apps'
SPARK_APPS_PATH = 'api/v1/applications'
SPARK_MASTER_STATE_PATH = '/json/'
SPARK_MASTER_APP_PATH = '/app/'
MESOS_MASTER_APP_PATH = '/frameworks'

# Application type and states to collect
YARN_APPLICATION_TYPES = 'SPARK'
APPLICATION_STATES = 'RUNNING'

# Event types
JOB_EVENT = 'job'
STAGE_EVENT = 'stage'

# Alert types
ERROR_STATUS = 'FAILED'
SUCCESS_STATUS = ['SUCCEEDED', 'COMPLETE']

# Event source type
SOURCE_TYPE_NAME = 'spark'

# Metric types
GAUGE = 'gauge'
COUNT = 'count'
MONOTONIC_COUNT = 'monotonic_count'

# Metrics to collect
SPARK_JOB_METRICS = {
    'numTasks': ('spark.job.num_tasks', COUNT),
    'numActiveTasks': ('spark.job.num_active_tasks', COUNT),
    'numCompletedTasks': ('spark.job.num_completed_tasks', COUNT),
    'numSkippedTasks': ('spark.job.num_skipped_tasks', COUNT),
    'numFailedTasks': ('spark.job.num_failed_tasks', COUNT),
    'numActiveStages': ('spark.job.num_active_stages', COUNT),
    'numCompletedStages': ('spark.job.num_completed_stages', COUNT),
    'numSkippedStages': ('spark.job.num_skipped_stages', COUNT),
    'numFailedStages': ('spark.job.num_failed_stages', COUNT),
}

SPARK_STAGE_METRICS = {
    'numActiveTasks': ('spark.stage.num_active_tasks', COUNT),
    'numCompleteTasks': ('spark.stage.num_complete_tasks', COUNT),
    'numFailedTasks': ('spark.stage.num_failed_tasks', COUNT),
    'executorRunTime': ('spark.stage.executor_run_time', COUNT),
    'inputBytes': ('spark.stage.input_bytes', COUNT),
    'inputRecords': ('spark.stage.input_records', COUNT),
    'outputBytes': ('spark.stage.output_bytes', COUNT),
    'outputRecords': ('spark.stage.output_records', COUNT),
    'shuffleReadBytes': ('spark.stage.shuffle_read_bytes', COUNT),
    'shuffleReadRecords': ('spark.stage.shuffle_read_records', COUNT),
    'shuffleWriteBytes': ('spark.stage.shuffle_write_bytes', COUNT),
    'shuffleWriteRecords': ('spark.stage.shuffle_write_records', COUNT),
    'memoryBytesSpilled': ('spark.stage.memory_bytes_spilled', COUNT),
    'diskBytesSpilled': ('spark.stage.disk_bytes_spilled', COUNT),
}

SPARK_DRIVER_METRICS = {
    'rddBlocks': ('spark.driver.rdd_blocks', COUNT),
    'memoryUsed': ('spark.driver.memory_used', COUNT),
    'diskUsed': ('spark.driver.disk_used', COUNT),
    'activeTasks': ('spark.driver.active_tasks', COUNT),
    'failedTasks': ('spark.driver.failed_tasks', COUNT),
    'completedTasks': ('spark.driver.completed_tasks', COUNT),
    'totalTasks': ('spark.driver.total_tasks', COUNT),
    'totalDuration': ('spark.driver.total_duration', COUNT),
    'totalInputBytes': ('spark.driver.total_input_bytes', COUNT),
    'totalShuffleRead': ('spark.driver.total_shuffle_read', COUNT),
    'totalShuffleWrite': ('spark.driver.total_shuffle_write', COUNT),
    'maxMemory': ('spark.driver.max_memory', COUNT),
}

SPARK_EXECUTOR_METRICS = {
    'rddBlocks': ('spark.executor.rdd_blocks', COUNT),
    'memoryUsed': ('spark.executor.memory_used', COUNT),
    'diskUsed': ('spark.executor.disk_used', COUNT),
    'activeTasks': ('spark.executor.active_tasks', COUNT),
    'failedTasks': ('spark.executor.failed_tasks', COUNT),
    'completedTasks': ('spark.executor.completed_tasks', COUNT),
    'totalTasks': ('spark.executor.total_tasks', COUNT),
    'totalDuration': ('spark.executor.total_duration', COUNT),
    'totalInputBytes': ('spark.executor.total_input_bytes', COUNT),
    'totalShuffleRead': ('spark.executor.total_shuffle_read', COUNT),
    'totalShuffleWrite': ('spark.executor.total_shuffle_write', COUNT),
    'maxMemory': ('spark.executor.max_memory', COUNT),
}

SPARK_RDD_METRICS = {
    'numPartitions': ('spark.rdd.num_partitions', COUNT),
    'numCachedPartitions': ('spark.rdd.num_cached_partitions', COUNT),
    'memoryUsed': ('spark.rdd.memory_used', COUNT),
    'diskUsed': ('spark.rdd.disk_used', COUNT),
}

SPARK_STREAMING_STATISTICS_METRICS = {
    'avgInputRate': ('spark.streaming.statistics.avg_input_rate', GAUGE),
    'avgProcessingTime': ('spark.streaming.statistics.avg_processing_time', GAUGE),
    'avgSchedulingDelay': ('spark.streaming.statistics.avg_scheduling_delay', GAUGE),
    'avgTotalDelay': ('spark.streaming.statistics.avg_total_delay', GAUGE),
    'batchDuration': ('spark.streaming.statistics.batch_duration', GAUGE),
    'numActiveBatches': ('spark.streaming.statistics.num_active_batches', GAUGE),
    'numActiveReceivers': ('spark.streaming.statistics.num_active_receivers', GAUGE),
    'numInactiveReceivers': ('spark.streaming.statistics.num_inactive_receivers', GAUGE),
    'numProcessedRecords': ('spark.streaming.statistics.num_processed_records', MONOTONIC_COUNT),
    'numReceivedRecords': ('spark.streaming.statistics.num_received_records', MONOTONIC_COUNT),
    'numReceivers': ('spark.streaming.statistics.num_receivers', GAUGE),
    'numRetainedCompletedBatches': ('spark.streaming.statistics.num_retained_completed_batches', MONOTONIC_COUNT),
    'numTotalCompletedBatches': ('spark.streaming.statistics.num_total_completed_batches', MONOTONIC_COUNT),
}


class SparkCheck(AgentCheck):
    HTTP_CONFIG_REMAPPER = {
        'ssl_verify': {'name': 'tls_verify'},
        'ssl_cert': {'name': 'tls_cert'},
        'ssl_key': {'name': 'tls_private_key'},
    }

    def check(self, instance):
        # Get additional tags from the conf file
        tags = instance.get('tags', [])
        if tags is None:
            tags = []
        else:
            tags = list(set(tags))

        cluster_name = instance.get('cluster_name')
        if not cluster_name:
            raise ConfigurationError('The cluster_name must be specified in the instance configuration')
        tags.append('cluster_name:%s' % cluster_name)

        spark_apps = self._get_running_apps(instance)

        # Get the job metrics
        self._spark_job_metrics(instance, spark_apps, tags)

        # Get the stage metrics
        self._spark_stage_metrics(instance, spark_apps, tags)

        # Get the executor metrics
        self._spark_executor_metrics(instance, spark_apps, tags)

        # Get the rdd metrics
        self._spark_rdd_metrics(instance, spark_apps, tags)

        # Get the streaming statistics metrics
        if is_affirmative(instance.get('streaming_metrics', True)):
            self._spark_streaming_statistics_metrics(instance, spark_apps, tags)

        # Report success after gathering all metrics from the ApplicationMaster
        if spark_apps:
            app_id, (app_name, tracking_url) = next(iteritems(spark_apps))
            base_url = self._get_request_url(instance, tracking_url)
            am_address = self._get_url_base(base_url)

            self.service_check(
                SPARK_SERVICE_CHECK,
                AgentCheck.OK,
                tags=['url:%s' % am_address] + tags,
                message='Connection to ApplicationMaster "%s" was successful' % am_address,
            )

    def _get_master_address(self, instance):
        """
        Get the master address from the instance configuration
        """

        master_address = instance.get(MASTER_ADDRESS)
        if master_address is None:
            master_address = instance.get(DEPRECATED_MASTER_ADDRESS)

            if master_address:
                self.log.warning(
                    'The use of `%s` is deprecated. Please use `%s` instead.'
                    % (DEPRECATED_MASTER_ADDRESS, MASTER_ADDRESS)
                )
            else:
                raise Exception('URL for `%s` must be specified in the instance configuration' % MASTER_ADDRESS)

        return master_address

    def _get_request_url(self, instance, url):
        """
        Get the request address, build with proxy if necessary
        """
        parsed = urlparse(url)

        _url = url
        if not (parsed.netloc and parsed.scheme) and is_affirmative(instance.get('spark_proxy_enabled', False)):
            master_address = self._get_master_address(instance)
            _url = urljoin(master_address, parsed.path)

        self.log.debug('Request URL returned: %s', _url)
        return _url

    def _get_running_apps(self, instance):
        """
        Determine what mode was specified
        """
        tags = instance.get('tags', [])
        if tags is None:
            tags = []
        master_address = self._get_master_address(instance)
        # Get the cluster name from the instance configuration
        cluster_name = instance.get('cluster_name')
        if cluster_name is None:
            raise Exception('The cluster_name must be specified in the instance configuration')
        tags.append('cluster_name:%s' % cluster_name)
        tags = list(set(tags))
        # Determine the cluster mode
        cluster_mode = instance.get(SPARK_CLUSTER_MODE)
        if cluster_mode is None:
            self.log.warning(
                'The value for `spark_cluster_mode` was not set in the configuration. '
                'Defaulting to "%s"' % SPARK_YARN_MODE
            )
            cluster_mode = SPARK_YARN_MODE

        if cluster_mode == SPARK_STANDALONE_MODE:
            # check for PRE-20
            pre20 = is_affirmative(instance.get(SPARK_PRE_20_MODE, False))
            return self._standalone_init(master_address, pre20, tags)

        elif cluster_mode == SPARK_MESOS_MODE:
            running_apps = self._mesos_init(instance, master_address, tags)
            return self._get_spark_app_ids(running_apps, tags)

        elif cluster_mode == SPARK_YARN_MODE:
            running_apps = self._yarn_init(master_address, tags)
            return self._get_spark_app_ids(running_apps, tags)

        elif cluster_mode == SPARK_DRIVER_MODE:
            return self._driver_init(master_address, tags)

        else:
            raise Exception('Invalid setting for %s. Received %s.' % (SPARK_CLUSTER_MODE, cluster_mode))

    def _driver_init(self, spark_driver_address, tags):
        """
        Return a dictionary of {app_id: (app_name, tracking_url)} for the running Spark applications
        """
        running_apps = {}
        metrics_json = self._rest_request_to_json(
            spark_driver_address, SPARK_APPS_PATH, SPARK_DRIVER_SERVICE_CHECK, tags
        )

        for app_json in metrics_json:
            app_id = app_json.get('id')
            app_name = app_json.get('name')
            running_apps[app_id] = (app_name, spark_driver_address)

        # Report success after gathering metrics from k8s spark driver
        self.service_check(
            SPARK_DRIVER_SERVICE_CHECK,
            AgentCheck.OK,
            tags=['url:%s' % spark_driver_address] + tags,
            message='Connection to k8s spark driver "%s" was successful' % spark_driver_address,
        )
        self.log.info("Returning running apps %s" % running_apps)
        return running_apps

    def _standalone_init(self, spark_master_address, pre_20_mode, tags):
        """
        Return a dictionary of {app_id: (app_name, tracking_url)} for the running Spark applications
        """
        metrics_json = self._rest_request_to_json(
            spark_master_address, SPARK_MASTER_STATE_PATH, SPARK_STANDALONE_SERVICE_CHECK, tags
        )

        running_apps = {}

        if metrics_json.get('activeapps'):
            for app in metrics_json['activeapps']:
                app_id = app.get('id')
                app_name = app.get('name')

                # Parse through the HTML to grab the application driver's link
                try:
                    app_url = self._get_standalone_app_url(app_id, spark_master_address, tags)

                    if app_id and app_name and app_url:
                        if pre_20_mode:
                            self.log.debug('Getting application list in pre-20 mode')
                            applist = self._rest_request_to_json(
                                app_url, SPARK_APPS_PATH, SPARK_STANDALONE_SERVICE_CHECK, tags
                            )
                            for appl in applist:
                                aid = appl.get('id')
                                aname = appl.get('name')
                                running_apps[aid] = (aname, app_url)
                        else:
                            running_apps[app_id] = (app_name, app_url)
                except Exception:
                    # it's possible for the requests to fail if the job
                    # completed since we got the list of apps.  Just continue
                    pass

        # Report success after gathering metrics from Spark master
        self.service_check(
            SPARK_STANDALONE_SERVICE_CHECK,
            AgentCheck.OK,
            tags=['url:%s' % spark_master_address] + tags,
            message='Connection to Spark master "%s" was successful' % spark_master_address,
        )
        self.log.info("Returning running apps %s" % running_apps)
        return running_apps

    def _mesos_init(self, instance, master_address, tags):
        """
        Return a dictionary of {app_id: (app_name, tracking_url)} for running Spark applications.
        """
        running_apps = {}

        metrics_json = self._rest_request_to_json(master_address, MESOS_MASTER_APP_PATH, MESOS_SERVICE_CHECK, tags)

        if metrics_json.get('frameworks'):
            for app_json in metrics_json.get('frameworks'):
                app_id = app_json.get('id')
                tracking_url = app_json.get('webui_url')
                app_name = app_json.get('name')

                if app_id and tracking_url and app_name:
                    spark_ports = instance.get('spark_ui_ports')
                    if spark_ports is None:
                        # No filtering by port, just return all the frameworks
                        running_apps[app_id] = (app_name, tracking_url)
                    else:
                        # Only return the frameworks running on the correct port
                        tracking_url_port = urlparse(tracking_url).port
                        if tracking_url_port in spark_ports:
                            running_apps[app_id] = (app_name, tracking_url)

        # Report success after gathering all metrics from ResourceManager
        self.service_check(
            MESOS_SERVICE_CHECK,
            AgentCheck.OK,
            tags=['url:%s' % master_address] + tags,
            message='Connection to ResourceManager "%s" was successful' % master_address,
        )

        return running_apps

    def _yarn_init(self, rm_address, tags):
        """
        Return a dictionary of {app_id: (app_name, tracking_url)} for running Spark applications.
        """
        running_apps = self._yarn_get_running_spark_apps(rm_address, tags)

        # Report success after gathering all metrics from ResourceManager
        self.service_check(
            YARN_SERVICE_CHECK,
            AgentCheck.OK,
            tags=['url:%s' % rm_address] + tags,
            message='Connection to ResourceManager "%s" was successful' % rm_address,
        )

        return running_apps

    def _get_standalone_app_url(self, app_id, spark_master_address, tags):
        """
        Return the application URL from the app info page on the Spark master.
        Due to a bug, we need to parse the HTML manually because we cannot
        fetch JSON data from HTTP interface.
        """
        app_page = self._rest_request(
            spark_master_address, SPARK_MASTER_APP_PATH, SPARK_STANDALONE_SERVICE_CHECK, tags, appId=app_id
        )

        dom = BeautifulSoup(app_page.text, 'html.parser')
        app_detail_ui_links = dom.find_all('a', string='Application Detail UI')

        if app_detail_ui_links and len(app_detail_ui_links) == 1:
            return app_detail_ui_links[0].attrs['href']

    def _yarn_get_running_spark_apps(self, rm_address, tags):
        """
        Return a dictionary of {app_id: (app_name, tracking_url)} for running Spark applications.

        The `app_id` returned is that of the YARN application. This will eventually be mapped into
        a Spark application ID.
        """
        metrics_json = self._rest_request_to_json(
            rm_address,
            YARN_APPS_PATH,
            YARN_SERVICE_CHECK,
            tags,
            states=APPLICATION_STATES,
            applicationTypes=YARN_APPLICATION_TYPES,
        )

        running_apps = {}

        if metrics_json.get('apps'):
            if metrics_json['apps'].get('app') is not None:

                for app_json in metrics_json['apps']['app']:
                    app_id = app_json.get('id')
                    tracking_url = app_json.get('trackingUrl')
                    app_name = app_json.get('name')

                    if app_id and tracking_url and app_name:
                        running_apps[app_id] = (app_name, tracking_url)

        return running_apps

    def _get_spark_app_ids(self, running_apps, tags):
        """
        Traverses the Spark application master in YARN to get a Spark application ID.

        Return a dictionary of {app_id: (app_name, tracking_url)} for Spark applications
        """
        spark_apps = {}
        for app_id, (app_name, tracking_url) in iteritems(running_apps):
            response = self._rest_request_to_json(tracking_url, SPARK_APPS_PATH, SPARK_SERVICE_CHECK, tags)

            for app in response:
                app_id = app.get('id')
                app_name = app.get('name')

                if app_id and app_name:
                    spark_apps[app_id] = (app_name, tracking_url)

        return spark_apps

    def _spark_job_metrics(self, instance, running_apps, addl_tags):
        """
        Get metrics for each Spark job.
        """
        for app_id, (app_name, tracking_url) in iteritems(running_apps):

            base_url = self._get_request_url(instance, tracking_url)
            response = self._rest_request_to_json(
                base_url, SPARK_APPS_PATH, SPARK_SERVICE_CHECK, addl_tags, app_id, 'jobs'
            )

            for job in response:

                status = job.get('status')

                tags = ['app_name:%s' % str(app_name)]
                tags.extend(addl_tags)
                tags.append('status:%s' % str(status).lower())

                self._set_metrics_from_json(tags, job, SPARK_JOB_METRICS)
                self._set_metric('spark.job.count', COUNT, 1, tags)

    def _spark_stage_metrics(self, instance, running_apps, addl_tags):
        """
        Get metrics for each Spark stage.
        """
        for app_id, (app_name, tracking_url) in iteritems(running_apps):

            base_url = self._get_request_url(instance, tracking_url)
            response = self._rest_request_to_json(
                base_url, SPARK_APPS_PATH, SPARK_SERVICE_CHECK, addl_tags, app_id, 'stages'
            )

            for stage in response:

                status = stage.get('status')

                tags = ['app_name:%s' % str(app_name)]
                tags.extend(addl_tags)
                tags.append('status:%s' % str(status).lower())

                self._set_metrics_from_json(tags, stage, SPARK_STAGE_METRICS)
                self._set_metric('spark.stage.count', COUNT, 1, tags)

    def _spark_executor_metrics(self, instance, running_apps, addl_tags):
        """
        Get metrics for each Spark executor.
        """
        for app_id, (app_name, tracking_url) in iteritems(running_apps):

            base_url = self._get_request_url(instance, tracking_url)
            response = self._rest_request_to_json(
                base_url, SPARK_APPS_PATH, SPARK_SERVICE_CHECK, addl_tags, app_id, 'executors'
            )

            tags = ['app_name:%s' % str(app_name)]
            tags.extend(addl_tags)

            for executor in response:
                if executor.get('id') == 'driver':
                    self._set_metrics_from_json(tags, executor, SPARK_DRIVER_METRICS)
                else:
                    self._set_metrics_from_json(tags, executor, SPARK_EXECUTOR_METRICS)

            if len(response):
                self._set_metric('spark.executor.count', COUNT, len(response), tags)

    def _spark_rdd_metrics(self, instance, running_apps, addl_tags):
        """
        Get metrics for each Spark RDD.
        """
        for app_id, (app_name, tracking_url) in iteritems(running_apps):

            base_url = self._get_request_url(instance, tracking_url)
            response = self._rest_request_to_json(
                base_url, SPARK_APPS_PATH, SPARK_SERVICE_CHECK, addl_tags, app_id, 'storage/rdd'
            )

            tags = ['app_name:%s' % str(app_name)]
            tags.extend(addl_tags)

            for rdd in response:
                self._set_metrics_from_json(tags, rdd, SPARK_RDD_METRICS)

            if len(response):
                self._set_metric('spark.rdd.count', COUNT, len(response), tags)

    def _spark_streaming_statistics_metrics(self, instance, running_apps, addl_tags):
        """
        Get metrics for each application streaming statistics.
        """
        for app_id, (app_name, tracking_url) in iteritems(running_apps):
            try:
                base_url = self._get_request_url(instance, tracking_url)
                response = self._rest_request_to_json(
                    base_url, SPARK_APPS_PATH, SPARK_SERVICE_CHECK, addl_tags, app_id, 'streaming/statistics'
                )
                self.log.debug('streaming/statistics: %s', response)
                tags = ['app_name:%s' % str(app_name)]
                tags.extend(addl_tags)

                # NOTE: response is a dict
                self._set_metrics_from_json(tags, response, SPARK_STREAMING_STATISTICS_METRICS)
            except HTTPError as e:
                # NOTE: If api call returns response 404
                # then it means that the application is not a streaming application, we should skip metric submission
                if e.response.status_code != 404:
                    raise

    def _set_metrics_from_json(self, tags, metrics_json, metrics):
        """
        Parse the JSON response and set the metrics
        """
        if metrics_json is None:
            return

        for status, (metric_name, metric_type) in iteritems(metrics):
            metric_status = metrics_json.get(status)

            if metric_status is not None:
                self._set_metric(metric_name, metric_type, metric_status, tags)

    def _set_metric(self, metric_name, metric_type, value, tags=None):
        """
        Set a metric
        """
        if tags is None:
            tags = []
        if metric_type == GAUGE:
            self.gauge(metric_name, value, tags=tags)
        elif metric_type == COUNT:
            self.count(metric_name, value, tags=tags)
        elif metric_type == MONOTONIC_COUNT:
            self.monotonic_count(metric_name, value, tags=tags)
        else:
            self.log.error('Metric type "{}" unknown'.format(metric_type))

    def _rest_request(self, url, object_path, service_name, tags, *args, **kwargs):
        """
        Query the given URL and return the response
        """
        service_check_tags = ['url:%s' % self._get_url_base(url)] + tags

        if object_path:
            url = self._join_url_dir(url, object_path)

        # Add args to the url
        if args:
            for directory in args:
                url = self._join_url_dir(url, directory)

        # Add kwargs as arguments
        if kwargs:
            query = '&'.join(['{0}={1}'.format(key, value) for key, value in iteritems(kwargs)])
            url = urljoin(url, '?' + query)

        try:
            self.log.debug('Spark check URL: %s' % url)
            response = self.http.get(url)

            response.raise_for_status()

        except Timeout as e:
            self.service_check(
                service_name,
                AgentCheck.CRITICAL,
                tags=service_check_tags,
                message='Request timeout: {0}, {1}'.format(url, e),
            )
            raise

        except (HTTPError, InvalidURL, ConnectionError) as e:
            self.service_check(
                service_name,
                AgentCheck.CRITICAL,
                tags=service_check_tags,
                message='Request failed: {0}, {1}'.format(url, e),
            )
            raise

        except ValueError as e:
            self.service_check(service_name, AgentCheck.CRITICAL, tags=service_check_tags, message=str(e))
            raise

        else:
            return response

    def _rest_request_to_json(self, address, object_path, service_name, tags, *args, **kwargs):
        """
        Query the given URL and return the JSON response
        """
        response = self._rest_request(address, object_path, service_name, tags, *args, **kwargs)

        try:
            response_json = response.json()

        except JSONDecodeError as e:
            self.service_check(
                service_name,
                AgentCheck.CRITICAL,
                tags=['url:%s' % self._get_url_base(address)] + tags,
                message='JSON Parse failed: {0}'.format(e),
            )
            raise

        return response_json

    @classmethod
    def _join_url_dir(cls, url, *args):
        """
        Join a URL with multiple directories
        """
        for path in args:
            url = url.rstrip('/') + '/'
            url = urljoin(url, path.lstrip('/'))

        return url

    @classmethod
    def _get_url_base(cls, url):
        """
        Return the base of a URL
        """
        s = urlsplit(url)
        return urlunsplit([s.scheme, s.netloc, '', '', ''])
