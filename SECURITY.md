# Security reporting and scope

Vector-64 processes local UCI input, positions, networks and datasets. The native
visualizer is an unauthenticated loopback developer tool with file-loading and
file-writing controls. It is not a public hosted-service boundary. A server
adapter must isolate engine processes and bound requests, output and time.

## Reporting

Use the repository's **Security** tab to check whether private vulnerability
reporting is available. If it is unavailable, open an issue requesting a private
reporting channel without publishing exploit details or sensitive data. This
repository does not currently publish a dedicated security mailbox or a response
SLA; this page does not invent one.

Include the affected revision/platform, input type, impact, minimal reproduction,
and whether the issue is reachable through UCI, a network file, training data,
or the local visualizer. Share full exploit details only through the agreed
private channel.

## Boundaries

- Train/export only from trusted PyTorch checkpoints; current loaders allow
  pickle deserialization.
- Keep visualization bound to loopback; do not expose it through an unrestricted
  reverse proxy.
- Validate and isolate externally supplied positions, files and process runs.
- Do not continue using a worker after a failed network replacement; see
  [the known loader defect](LIMITATIONS.md#network-replacement).

Current CI includes sanitizers and protocol checks, but that is not a security
certification. No maintained backport/support window is declared here; reports
should identify the exact release and whether current source is affected.
