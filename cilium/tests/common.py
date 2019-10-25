# (C) Datadog, Inc. 2019
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

CHECK_NAME = 'cilium'
NAMESPACE = 'cilium.'


AGENT_METRICS = [
    'cilium.agent.api_process_time.seconds.count',
    'cilium.agent.api_process_time.seconds.sum',
    'cilium.agent.bootstrap.seconds.count',
    'cilium.agent.bootstrap.seconds.sum',
    'cilium.bpf.map_ops.total',
    'cilium.controllers.failing.count',
    'cilium.controllers.runs_duration.seconds.count',
    'cilium.controllers.runs_duration.seconds.sum',
    'cilium.controllers.runs.total',
    'cilium.datapath.conntrack_gc.duration.seconds.count',
    'cilium.datapath.conntrack_gc.duration.seconds.sum',
    'cilium.datapath.conntrack_gc.entries',
    'cilium.datapath.conntrack_gc.key_fallbacks.total',
    'cilium.datapath.conntrack_gc.runs.total',
    'cilium.datapath.errors.total',
    'cilium.drop_bytes.total',
    'cilium.drop_count.total',
    'cilium.endpoint.count',
    'cilium.endpoint.regeneration_time_stats.seconds.count',
    'cilium.endpoint.regeneration_time_stats.seconds.sum',
    'cilium.endpoint.regenerations.count',
    'cilium.endpoint.state',
    'cilium.errors_warning.total',
    'cilium.event_timestamp',
    'cilium.forward_bytes.total',
    'cilium.forward_count.total',
    'cilium.fqdn.gc_deletions.total',
    'cilium.identity.count',
    'cilium.ip_addresses.count',
    'cilium.ipam.events.total',
    'cilium.k8s_client.api_calls.count',
    'cilium.k8s_client.api_latency_time.seconds.count',
    'cilium.k8s_client.api_latency_time.seconds.sum',
    'cilium.kubernetes.events_received.total',
    'cilium.kubernetes.events.total',
    'cilium.nodes.all_datapath_validations.total',
    'cilium.nodes.all_events_received.total',
    'cilium.nodes.managed.total',
    'cilium.policy.count',
    'cilium.policy.endpoint_enforcement_status',
    'cilium.policy.import_errors.count', #continue here
    'cilium.policy.l7_denied.total',
    'cilium.policy.l7_forwarded.total',
    'cilium.policy.l7_parse_errors.total',
    'cilium.policy.l7_received.total',
    'cilium.policy.max_revision',
    'cilium.policy.regeneration_time_stats.seconds.count',
    'cilium.policy.regeneration_time_stats.seconds.sum',
    'cilium.policy.regeneration.total',
    'cilium.process.cpu.seconds.total',
    'cilium.process.max_fds',
    'cilium.process.open_fds',
    'cilium.process.resident_memory.bytes',
    'cilium.process.start_time.seconds',
    'cilium.process.virtual_memory.bytes',
    'cilium.process.virtual_memory.max.bytes',
    'cilium.subprocess.start.total',
    'cilium.triggers_policy.update_call_duration.seconds.count',
    'cilium.triggers_policy.update_call_duration.seconds.sum',
    'cilium.triggers_policy.update_folds',
    'cilium.triggers_policy.update.total',
    'cilium.unreachable.health_endpoints', #"Number of health endpoints that cannot be reached"
    'cilium.unreachable.nodes', #"Number of nodes that cannot be reached",
]

OPERATOR_METRICS = [
    'cilium.operator.process.cpu.seconds',
    'cilium.operator.process.max_fds',
    'cilium.operator.process.open_fds',
    'cilium.operator.process.resident_memory.bytes',
    'cilium.operator.process.start_time.seconds',
    'cilium.operator.process.virtual_memory.bytes',
    'cilium.operator.process.virtual_memory_max.bytes'
]
