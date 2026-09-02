# abrege

![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.1.0](https://img.shields.io/badge/AppVersion-0.1.0-informational?style=flat-square)

A Helm chart to deploy abrege.

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://cloudnative-pg.github.io/charts | cnpg(cluster) | 0.8.1 |
| oci://registry-1.docker.io/cloudpirates | postgres(postgres) | 0.19.6 |
| oci://registry-1.docker.io/cloudpirates | redis(redis) | 0.27.9 |
| oci://registry-1.docker.io/cloudpirates | rustfs(rustfs) | 0.10.0 |

## Values

### General

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| commonLabels | object | `{}` | Add labels to all the deployed resources |
| cronjobs | object | `{}` | Map of CronJobs to create. Each key is used as the cronjob name and as its `app.kubernetes.io/component` label. Empty by default. |
| enabled | bool | `true` | Master switch for the whole chart. When `false`, every template renders nothing (no api/frontend/worker/jobs/cronjobs/redis/postgres/cnpg/extraObjects at all) - use this to keep a release/namespace registered with a deployment system (e.g. an ArgoCD Application that always gets generated for every app/env combination) without actually deploying any resource into it. |
| extraObjects | object | `{}` | Map of extra specs to dynamically add to this chart. Each key is a unique, arbitrary name for the object (only used so `-f` values files/overrides can add, override or remove a single entry by key instead of the whole list - lists don't merge across values files in Helm). Each entry must be written as a YAML literal block scalar string (see the commented `my-configmap`/`my-vault-secret` examples below for the exact syntax), not a nested map: only the string form is passed through `tpl` as raw text, so multi-line substitutions (`nindent`, `include "helper.labels"`, ...) render correctly; a nested map form only round-trips safely for single-scalar substitutions like `{{ .Values.fullnameOverride }}`. |
| fullnameOverride | string | `""` | String to fully override the default application name. |
| nameOverride | string | `""` | Provide a name in place of the default application name. |

### Global

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| global.env | object | `{}` | Map or array of environment variables to inject into all containers (`valueFrom` supported). Since this chart injects `global.env`/`global.envCm`/`global.envSecret` into EVERY component (including `frontend`), only put values here that truly ALL components need. Anything backend-specific (redis, celery, S3/AWS, etc.) belongs on the specific component's own `env`/`envCm`/`envSecret` instead (see `api.env`/`worker.env`), so it isn't needlessly exposed to components that don't use it (e.g. the static `frontend`). |
| global.envCm | object | `{}` | Map of environment variables to inject into a configmap loaded by all containers (`valueFrom` not supported). |
| global.envFrom | list | `[]` | List or map of `configMapRef`/`secretRef` entries to load into every container's `envFrom` (merged with each component's own `envFrom`, global entries first). Same scope caveat as `env` below: only put entries here that truly ALL components need. |
| global.envSecret | object | `{}` | Map of environment variables to inject into a secret loaded by all containers (`valueFrom` not supported). |
| global.httpRoute | object | `{}` | Globally shared httproute configuration. |
| global.imagePullSecrets | list | `[]` | Image credentials applied to every component in addition to any component-specific `imagePullSecrets`. |
| global.imageRegistry | string | `""` | Global Docker image registry. |
| global.ingress | object | `{}` | Globally shared ingress configuration. |

### Api

#### General

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.affinity | object | `{}` | Affinity used for app pod. |
| api.args | list | `[]` | Api container command args. |
| api.command | list | `[]` | Api container command. |
| api.containerPort | int | `5000` | Api container port number. |
| api.containerPortName | string | `"http"` | Api container port name. |
| api.deploymentType | string | `"Deployment"` | Workload kind to deploy the app as. One of "Deployment" or "StatefulSet". |
| api.env | object | `{"AWS_ACCESS_KEY_ID":"rustfsadmin","AWS_BUCKET_NAME":"abrege","AWS_DEFAULT_REGION":"us-east-1","AWS_ENDPOINT_URL":"http://abrege-rustfs:9000","AWS_SECRET_ACCESS_KEY":{"valueFrom":{"secretKeyRef":{"key":"secret-key","name":"abrege-rustfs"}}},"CELERY_APP_NAME":"abrege","DATABASE_URL":{"valueFrom":{"secretKeyRef":{"key":"uri","name":"abrege-postgres"}}},"REDIS_HOST":"abrege-redis-master"}` | Map or array of environment variables to inject into the app container (`valueFrom` supported). |
| api.envCm | object | `{}` | Map of environment variables to inject into a configmap loaded by the app container (`valueFrom` not supported). |
| api.envFrom | list | `[]` | Api container env variables loaded from configmap or secret reference. List or map (merged with `global.envFrom` above, global entries first); see `global.envFrom` for both forms. |
| api.envSecret | object | `{}` | Map of environment variables to inject into a secret loaded by the app container (`valueFrom` not supported). |
| api.extraContainers | list | `[]` | Extra containers to add to the app pod as sidecars. |
| api.extraPorts | list | `[]` | Api extra container ports. |
| api.extraVolumeClaims | list | `[]` | Additional volumeClaims to add, concatenated with `volumeClaims` above at render time. |
| api.extraVolumeMounts | list | `[]` | Additional volumeMounts to add, concatenated with `volumeMounts` above at render time. |
| api.extraVolumes | list | `[]` | Additional volumes to add, concatenated with `volumes` above at render time. |
| api.hostAliases | list | `[]` | Host aliases that will be injected at pod-level into /etc/hosts. |
| api.imagePullSecrets | list | `[]` | Image credentials configuration. |
| api.initContainers | list | `[]` | Init containers to add to the app pod. |
| api.nodeSelector | object | `{}` | Default node selector for app. |
| api.podAnnotations | object | `{}` | Annotations for the app deployed pods. |
| api.podLabels | object | `{}` | Labels for the app deployed pods. |
| api.podSecurityContext | object | `{"fsGroup":10001,"runAsNonRoot":true,"seccompProfile":{"type":"RuntimeDefault"}}` | Pod-level security context. Rendered via `toYaml`, so any other `PodSecurityContext` field (e.g. `runAsGroup`, `sysctls`, `supplementalGroups`) can be added here too, even though not pre-populated below. |
| api.replicaCount | int | `1` | The number of application controller pods to run. Kept at `1` by default so the chart deploys plug-and-play with minimal resources; bump this (and/or enable `api.autoscaling`) for production. |
| api.revisionHistoryLimit | int | `10` | Revision history limit for the app. |
| api.securityContext | object | `{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]},"readOnlyRootFilesystem":true,"runAsNonRoot":true,"runAsUser":10001,"seccompProfile":{"type":"RuntimeDefault"}}` | Container-level security context. Rendered via `toYaml`, so any other `SecurityContext` field (e.g. `runAsGroup`, `procMount`) can be added here too, even though not pre-populated below. |
| api.tolerations | list | `[]` | Default tolerations for app. |
| api.volumeClaims | list | `[]` | List of volumeClaims to add. |
| api.volumeMounts | list | `[{"mountPath":"/app/.cache/","name":"cache"},{"mountPath":"/app/.tmp/","name":"tmp"},{"mountPath":"/tmp/","name":"run-tmp"}]` | List of mounts to add (normally used with `volumes` or `volumeClaims`). |
| api.volumes | list | `[{"emptyDir":{},"name":"cache"},{"emptyDir":{},"name":"tmp"},{"emptyDir":{},"name":"run-tmp"}]` | List of volumes to add. |

#### Autoscaling

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.autoscaling.enabled | bool | `false` | Enable Horizontal Pod Autoscaler for the app. |
| api.autoscaling.maxReplicas | int | `3` | Maximum number of replicas for the app. |
| api.autoscaling.minReplicas | int | `1` | Minimum number of replicas for the app. |
| api.autoscaling.targetCPUUtilizationPercentage | int | `80` | Average CPU utilization percentage for the app. |
| api.autoscaling.targetMemoryUtilizationPercentage | int | `80` | Average memory utilization percentage for the app. |

#### GrpcRoute

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.grpcRoute.annotations | object | `{}` | Additional GRPCRoute annotations. |
| api.grpcRoute.enabled | bool | `false` | Enable a GRPCRoute resource for this service. |
| api.grpcRoute.hostnames | list | `[]` | Hostnames for the GRPCRoute to match. |
| api.grpcRoute.labels | object | `{}` | Additional GRPCRoute labels. |
| api.grpcRoute.parentRefs | list | `[]` | Parent references (Gateways) to attach the GRPCRoute to. |
| api.grpcRoute.rules | list | `[]` | Routing rules for the GRPCRoute. |

#### HttpRoute

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.httpRoute.annotations | object | `{}` | Additional HTTPRoute annotations. |
| api.httpRoute.enabled | bool | `false` | Enable an HTTPRoute resource for this service. |
| api.httpRoute.hostnames | list | `[]` | Hostnames for the HTTPRoute to match. |
| api.httpRoute.labels | object | `{}` | Additional HTTPRoute labels. |
| api.httpRoute.parentRefs | list | `[]` | Parent references (Gateways) to attach the HTTPRoute to. |
| api.httpRoute.rules | list | `[]` | Routing rules for the HTTPRoute. |

#### Image

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.image.pullPolicy | string | `"IfNotPresent"` | Image pull policy for the app. |
| api.image.registry | string | `"ghcr.io"` | Registry to use for the app. |
| api.image.repository | string | `"ia-generative/abrege/api"` | Repository to use for the app. |
| api.image.tag | string | `""` | Tag to use for the app. Overrides the image tag whose default is the chart appVersion. |

#### Ingress

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.ingress.annotations | object | `{}` | Additional ingress annotations. |
| api.ingress.className | string | `""` | Defines which ingress controller will implement the resource. |
| api.ingress.enabled | bool | `false` | Whether or not ingress should be enabled. |
| api.ingress.hosts[0].name | string | `"domain.local"` | Name of the host record. |
| api.ingress.hosts[0].paths[0].backend.portNumber | string | `nil` | Port used by the backend service linked to the path (leave null to use the app service port). |
| api.ingress.hosts[0].paths[0].backend.serviceName | string | `""` | Name of the backend service linked to the path (leave empty to use the app service). |
| api.ingress.hosts[0].paths[0].path | string | `"/"` | Path of the host record to manage routing. |
| api.ingress.hosts[0].paths[0].pathType | string | `"Prefix"` | Path type of the host record. |
| api.ingress.labels | object | `{}` | Additional ingress labels. |
| api.ingress.tls | list | `[]` | Enable TLS configuration. |

#### Metrics

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.metrics.enabled | bool | `false` | Deploy metrics service. |
| api.metrics.service.annotations | object | `{}` | Metrics service annotations. |
| api.metrics.service.labels | object | `{}` | Metrics service labels. |
| api.metrics.service.port | int | `9000` | Metrics service port. |
| api.metrics.service.portName | string | `"metrics"` | Metrics service port name. |
| api.metrics.service.targetPort | int | `9000` | Metrics service target port. |
| api.metrics.serviceMonitor.annotations | object | `{}` | Prometheus ServiceMonitor annotations. |
| api.metrics.serviceMonitor.enabled | bool | `false` | Enable a prometheus ServiceMonitor. |
| api.metrics.serviceMonitor.endpoints[0].basicAuth.password | string | `""` | The secret in the service monitor namespace that contains the password for authentication. |
| api.metrics.serviceMonitor.endpoints[0].basicAuth.username | string | `""` | The secret in the service monitor namespace that contains the username for authentication. |
| api.metrics.serviceMonitor.endpoints[0].bearerTokenSecret.key | string | `""` | Secret key to mount to read bearer token for scraping targets. The secret needs to be in the same namespace as the service monitor and accessible by the Prometheus Operator. |
| api.metrics.serviceMonitor.endpoints[0].bearerTokenSecret.name | string | `""` | Secret name to mount to read bearer token for scraping targets. The secret needs to be in the same namespace as the service monitor and accessible by the Prometheus Operator. |
| api.metrics.serviceMonitor.endpoints[0].honorLabels | bool | `false` | When true, honorLabels preserves the metric’s labels when they collide with the target’s labels. |
| api.metrics.serviceMonitor.endpoints[0].interval | string | `"30s"` | Prometheus ServiceMonitor interval. |
| api.metrics.serviceMonitor.endpoints[0].metricRelabelings | list | `[]` | Prometheus MetricRelabelConfigs to apply to samples before ingestion. |
| api.metrics.serviceMonitor.endpoints[0].path | string | `"/metrics"` | Path used by the Prometheus ServiceMonitor to scrape metrics. |
| api.metrics.serviceMonitor.endpoints[0].relabelings | list | `[]` | Prometheus RelabelConfigs to apply to samples before scraping. |
| api.metrics.serviceMonitor.endpoints[0].scheme | string | `""` | Prometheus ServiceMonitor scheme. |
| api.metrics.serviceMonitor.endpoints[0].scrapeTimeout | string | `"10s"` | Prometheus ServiceMonitor scrapeTimeout. If empty, Prometheus uses the global scrape timeout unless it is less than the target's scrape interval value in which the latter is used. |
| api.metrics.serviceMonitor.endpoints[0].selector | object | `{}` | Prometheus ServiceMonitor selector. |
| api.metrics.serviceMonitor.endpoints[0].tlsConfig | object | `{}` | Prometheus ServiceMonitor tlsConfig. |
| api.metrics.serviceMonitor.labels | object | `{}` | Prometheus ServiceMonitor labels. |

#### NetworkPolicy

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.networkPolicy.create | bool | `false` | Create NetworkPolicy object for the app. |
| api.networkPolicy.egress | list | `[]` | Egress rules for the NetworkPolicy object. |
| api.networkPolicy.ingress | list | `[]` | Ingress rules for the NetworkPolicy object. |
| api.networkPolicy.policyTypes | list | `["Ingress"]` | Policy types used in the NetworkPolicy object. |

#### Pdb

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.pdb.annotations | object | `{}` | Annotations to be added to app pdb. |
| api.pdb.enabled | bool | `false` | Deploy a PodDisruptionBudget for the app |
| api.pdb.labels | object | `{}` | Labels to be added to app pdb. |
| api.pdb.maxUnavailable | string | `""` | Number of pods that are unavailable after eviction as number or percentage (eg.: 50%). Has higher precedence over `api.pdb.minAvailable`. |
| api.pdb.minAvailable | string | `""` (defaults to 0 if not specified) | Number of pods that are available after eviction as number or percentage (eg.: 50%). |

#### Probes

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.probes.livenessProbe.failureThreshold | int | `3` | Minimum consecutive failures for the probe to be considered failed after having succeeded. |
| api.probes.livenessProbe.httpGet.path | string | `"/api/health"` | Api container healthcheck endpoint (livenessProbe is defined using `toYaml` so it is possible to override it completely). |
| api.probes.livenessProbe.httpGet.port | int | `5000` | Port to use for healthcheck (defaults to container port). |
| api.probes.livenessProbe.initialDelaySeconds | int | `15` | Number of seconds after the container has started before probe is initiated. |
| api.probes.livenessProbe.periodSeconds | int | `15` | How often (in seconds) to perform the probe. |
| api.probes.livenessProbe.successThreshold | int | `1` | Minimum consecutive successes for the probe to be considered successful after having failed. |
| api.probes.livenessProbe.timeoutSeconds | int | `1` | Number of seconds after which the probe times out. |
| api.probes.readinessProbe.failureThreshold | int | `3` | Minimum consecutive failures for the probe to be considered failed after having succeeded. |
| api.probes.readinessProbe.httpGet.path | string | `"/api/health"` | Api container healthcheck endpoint (readinessProbe is defined using `toYaml` so it is possible to override it completely). |
| api.probes.readinessProbe.httpGet.port | int | `5000` | Port to use for healthcheck (defaults to container port). |
| api.probes.readinessProbe.initialDelaySeconds | int | `15` | Number of seconds after the container has started before probe is initiated. |
| api.probes.readinessProbe.periodSeconds | int | `15` | How often (in seconds) to perform the probe. |
| api.probes.readinessProbe.successThreshold | int | `1` | Minimum consecutive successes for the probe to be considered successful after having failed. |
| api.probes.readinessProbe.timeoutSeconds | int | `1` | Number of seconds after which the probe times out. |
| api.probes.startupProbe.failureThreshold | int | `60` | Minimum consecutive failures for the probe to be considered failed after having succeeded. |
| api.probes.startupProbe.httpGet.path | string | `"/api/health"` | Api container healthcheck endpoint (startupProbe is defined using `toYaml` so it is possible to override it completely). |
| api.probes.startupProbe.httpGet.port | int | `5000` | Port to use for healthcheck (defaults to container port). |
| api.probes.startupProbe.initialDelaySeconds | int | `15` | Number of seconds after the container has started before probe is initiated. |
| api.probes.startupProbe.periodSeconds | int | `5` | How often (in seconds) to perform the probe. |
| api.probes.startupProbe.successThreshold | int | `1` | Minimum consecutive successes for the probe to be considered successful after having failed. |
| api.probes.startupProbe.timeoutSeconds | int | `1` | Number of seconds after which the probe times out. |

#### Resources

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.resources.limits.cpu | string | `"500m"` | CPU limit for the app. |
| api.resources.limits.memory | string | `"2Gi"` | Memory limit for the app. |
| api.resources.requests.cpu | string | `"125m"` | CPU request for the app. |
| api.resources.requests.memory | string | `"1Gi"` | Memory request for the app. |

#### Service

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.service.enabled | bool | `true` | Whether or not to create a Service for the app. Set to `false` for components that don't accept traffic (e.g. a queue consumer with no `containerPort`). |
| api.service.extraPorts | list | `[]` | Extra service ports. |
| api.service.nodePort | int | `31000` | Port used when type is `NodePort` to expose the service on the given node port. |
| api.service.port | int | `80` | Port used by the service. |
| api.service.portName | string | `"http"` | Port name used by the service. |
| api.service.protocol | string | `"TCP"` | Protocol used by the service. |
| api.service.type | string | `"ClusterIP"` | Type of service to create for the app. |

#### ServiceAccount

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.serviceAccount.annotations | object | `{}` | Annotations applied to created service account. |
| api.serviceAccount.automountServiceAccountToken | bool | `false` | Should the service account access token be automount in the pod. |
| api.serviceAccount.clusterRole.create | bool | `false` | Should the clusterRole be created. |
| api.serviceAccount.clusterRole.rules | list | `[]` | ClusterRole rules associated with the service account. |
| api.serviceAccount.create | bool | `false` | Create a service account. |
| api.serviceAccount.enabled | bool | `false` | Enable the service account. |
| api.serviceAccount.name | string | `""` | Service account name. |
| api.serviceAccount.role.create | bool | `false` | Should the role be created. |
| api.serviceAccount.role.rules | list | `[]` | Role rules associated with the service account. |

#### Strategy

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api.strategy.rollingUpdate.maxSurge | int | `1` | The maximum number of pods that can be scheduled above the desired number of pods. |
| api.strategy.rollingUpdate.maxUnavailable | int | `1` | The maximum number of pods that can be unavailable during the update process. |
| api.strategy.type | string | `"RollingUpdate"` | Strategy type used to replace old Pods by new ones, can be `Recreate` or `RollingUpdate`. |

### Cnpg

#### General

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| cnpg.enabled | bool | `false` | Enable the bundled CNPG PostgreSQL cluster (requires the CloudNativePG operator to be installed in the cluster). This is the production-grade database path (HA, backups) - mutually exclusive with `postgres` above: when enabling this, set `postgres.enabled: false` and repoint (or unset) `DATABASE_URL` at CNPG's own credentials/secret instead. |

### Frontend

#### General

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.affinity | object | `{}` | Affinity used for app pod. |
| frontend.args | list | `[]` | Frontend container command args. |
| frontend.command | list | `[]` | Frontend container command. |
| frontend.containerPort | int | `8080` | Frontend container port number. |
| frontend.containerPortName | string | `"http"` | Frontend container port name. |
| frontend.deploymentType | string | `"Deployment"` | Workload kind to deploy the app as. One of "Deployment" or "StatefulSet". |
| frontend.env | object | `{}` | Map or array of environment variables to inject into the app container (`valueFrom` supported). |
| frontend.envCm | object | `{}` | Map of environment variables to inject into a configmap loaded by the app container (`valueFrom` not supported). |
| frontend.envFrom | list | `[]` | Frontend container env variables loaded from configmap or secret reference. List or map (merged with `global.envFrom` above, global entries first); see `global.envFrom` for both forms. |
| frontend.envSecret | object | `{}` | Map of environment variables to inject into a secret loaded by the app container (`valueFrom` not supported). |
| frontend.extraContainers | list | `[]` | Extra containers to add to the app pod as sidecars. |
| frontend.extraPorts | list | `[]` | Frontend extra container ports. |
| frontend.extraVolumeClaims | list | `[]` | Additional volumeClaims to add, concatenated with `volumeClaims` above at render time. |
| frontend.extraVolumeMounts | list | `[]` | Additional volumeMounts to add, concatenated with `volumeMounts` above at render time. |
| frontend.extraVolumes | list | `[]` | Additional volumes to add, concatenated with `volumes` above at render time. |
| frontend.hostAliases | list | `[]` | Host aliases that will be injected at pod-level into /etc/hosts. |
| frontend.imagePullSecrets | list | `[]` | Image credentials configuration. |
| frontend.initContainers | list | `[]` | Init containers to add to the app pod. |
| frontend.nodeSelector | object | `{}` | Default node selector for app. |
| frontend.podAnnotations | object | `{}` | Annotations for the app deployed pods. |
| frontend.podLabels | object | `{}` | Labels for the app deployed pods. |
| frontend.podSecurityContext | object | `{"fsGroup":10001,"runAsNonRoot":true,"seccompProfile":{"type":"RuntimeDefault"}}` | Pod-level security context. Rendered via `toYaml`, so any other `PodSecurityContext` field (e.g. `runAsGroup`, `sysctls`, `supplementalGroups`) can be added here too, even though not pre-populated below. |
| frontend.replicaCount | int | `1` | The number of application controller pods to run. |
| frontend.revisionHistoryLimit | int | `10` | Revision history limit for the app. |
| frontend.securityContext | object | `{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]},"readOnlyRootFilesystem":false,"runAsNonRoot":true,"runAsUser":10001,"seccompProfile":{"type":"RuntimeDefault"}}` | Container-level security context. Rendered via `toYaml`, so any other `SecurityContext` field (e.g. `runAsGroup`, `procMount`) can be added here too, even though not pre-populated below. |
| frontend.tolerations | list | `[]` | Default tolerations for app. |
| frontend.viteEnv | object | `{}` | Frontend runtime config, rendered as `window.KEY = value` assignments into the `templates/frontend/vite-config.yaml` ConfigMap (mounted as `config.js` - see `volumes`/`volumeMounts` on this component). Since the built frontend bundle is static (Vite env vars are compile-time), this is how truly runtime-configurable values (API URLs, feature flags, ...) reach it without a rebuild. |
| frontend.volumeClaims | list | `[]` | List of volumeClaims to add. |
| frontend.volumeMounts | list | `[]` | List of mounts to add (normally used with `volumes` or `volumeClaims`). |
| frontend.volumes | list | `[]` | List of volumes to add. |

#### Autoscaling

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.autoscaling.enabled | bool | `false` | Enable Horizontal Pod Autoscaler for the app. |
| frontend.autoscaling.maxReplicas | int | `3` | Maximum number of replicas for the app. |
| frontend.autoscaling.minReplicas | int | `1` | Minimum number of replicas for the app. |
| frontend.autoscaling.targetCPUUtilizationPercentage | int | `80` | Average CPU utilization percentage for the app. |
| frontend.autoscaling.targetMemoryUtilizationPercentage | int | `80` | Average memory utilization percentage for the app. |

#### GrpcRoute

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.grpcRoute.annotations | object | `{}` | Additional GRPCRoute annotations. |
| frontend.grpcRoute.enabled | bool | `false` | Enable a GRPCRoute resource for this service. |
| frontend.grpcRoute.hostnames | list | `[]` | Hostnames for the GRPCRoute to match. |
| frontend.grpcRoute.labels | object | `{}` | Additional GRPCRoute labels. |
| frontend.grpcRoute.parentRefs | list | `[]` | Parent references (Gateways) to attach the GRPCRoute to. |
| frontend.grpcRoute.rules | list | `[]` | Routing rules for the GRPCRoute. |

#### HttpRoute

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.httpRoute.annotations | object | `{}` | Additional HTTPRoute annotations. |
| frontend.httpRoute.enabled | bool | `false` | Enable an HTTPRoute resource for this service. |
| frontend.httpRoute.hostnames | list | `[]` | Hostnames for the HTTPRoute to match. |
| frontend.httpRoute.labels | object | `{}` | Additional HTTPRoute labels. |
| frontend.httpRoute.parentRefs | list | `[]` | Parent references (Gateways) to attach the HTTPRoute to. |
| frontend.httpRoute.rules | list | `[]` | Routing rules for the HTTPRoute. |

#### Image

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.image.pullPolicy | string | `"IfNotPresent"` | Image pull policy for the app. |
| frontend.image.registry | string | `"ghcr.io"` | Registry to use for the app. |
| frontend.image.repository | string | `"ia-generative/abrege/frontend"` | Repository to use for the app. |
| frontend.image.tag | string | `""` | Tag to use for the app. Overrides the image tag whose default is the chart appVersion. |

#### Ingress

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.ingress.annotations | object | `{}` | Additional ingress annotations. |
| frontend.ingress.className | string | `""` | Defines which ingress controller will implement the resource. |
| frontend.ingress.enabled | bool | `false` | Whether or not ingress should be enabled. |
| frontend.ingress.hosts[0].name | string | `"domain.local"` | Name of the host record. |
| frontend.ingress.hosts[0].paths[0].backend.portNumber | string | `nil` | Port used by the backend service linked to the path (leave null to use the app service port). |
| frontend.ingress.hosts[0].paths[0].backend.serviceName | string | `""` | Name of the backend service linked to the path (leave empty to use the app service). |
| frontend.ingress.hosts[0].paths[0].path | string | `"/"` | Path of the host record to manage routing. |
| frontend.ingress.hosts[0].paths[0].pathType | string | `"Prefix"` | Path type of the host record. |
| frontend.ingress.labels | object | `{}` | Additional ingress labels. |
| frontend.ingress.tls | list | `[]` | Enable TLS configuration. |

#### Metrics

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.metrics.enabled | bool | `false` | Deploy metrics service. |
| frontend.metrics.service.annotations | object | `{}` | Metrics service annotations. |
| frontend.metrics.service.labels | object | `{}` | Metrics service labels. |
| frontend.metrics.service.port | int | `9000` | Metrics service port. |
| frontend.metrics.service.portName | string | `"metrics"` | Metrics service port name. |
| frontend.metrics.service.targetPort | int | `9000` | Metrics service target port. |
| frontend.metrics.serviceMonitor.annotations | object | `{}` | Prometheus ServiceMonitor annotations. |
| frontend.metrics.serviceMonitor.enabled | bool | `false` | Enable a prometheus ServiceMonitor. |
| frontend.metrics.serviceMonitor.endpoints[0].basicAuth.password | string | `""` | The secret in the service monitor namespace that contains the password for authentication. |
| frontend.metrics.serviceMonitor.endpoints[0].basicAuth.username | string | `""` | The secret in the service monitor namespace that contains the username for authentication. |
| frontend.metrics.serviceMonitor.endpoints[0].bearerTokenSecret.key | string | `""` | Secret key to mount to read bearer token for scraping targets. The secret needs to be in the same namespace as the service monitor and accessible by the Prometheus Operator. |
| frontend.metrics.serviceMonitor.endpoints[0].bearerTokenSecret.name | string | `""` | Secret name to mount to read bearer token for scraping targets. The secret needs to be in the same namespace as the service monitor and accessible by the Prometheus Operator. |
| frontend.metrics.serviceMonitor.endpoints[0].honorLabels | bool | `false` | When true, honorLabels preserves the metric’s labels when they collide with the target’s labels. |
| frontend.metrics.serviceMonitor.endpoints[0].interval | string | `"30s"` | Prometheus ServiceMonitor interval. |
| frontend.metrics.serviceMonitor.endpoints[0].metricRelabelings | list | `[]` | Prometheus MetricRelabelConfigs to apply to samples before ingestion. |
| frontend.metrics.serviceMonitor.endpoints[0].path | string | `"/metrics"` | Path used by the Prometheus ServiceMonitor to scrape metrics. |
| frontend.metrics.serviceMonitor.endpoints[0].relabelings | list | `[]` | Prometheus RelabelConfigs to apply to samples before scraping. |
| frontend.metrics.serviceMonitor.endpoints[0].scheme | string | `""` | Prometheus ServiceMonitor scheme. |
| frontend.metrics.serviceMonitor.endpoints[0].scrapeTimeout | string | `"10s"` | Prometheus ServiceMonitor scrapeTimeout. If empty, Prometheus uses the global scrape timeout unless it is less than the target's scrape interval value in which the latter is used. |
| frontend.metrics.serviceMonitor.endpoints[0].selector | object | `{}` | Prometheus ServiceMonitor selector. |
| frontend.metrics.serviceMonitor.endpoints[0].tlsConfig | object | `{}` | Prometheus ServiceMonitor tlsConfig. |
| frontend.metrics.serviceMonitor.labels | object | `{}` | Prometheus ServiceMonitor labels. |

#### NetworkPolicy

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.networkPolicy.create | bool | `false` | Create NetworkPolicy object for the app. |
| frontend.networkPolicy.egress | list | `[]` | Egress rules for the NetworkPolicy object. |
| frontend.networkPolicy.ingress | list | `[]` | Ingress rules for the NetworkPolicy object. |
| frontend.networkPolicy.policyTypes | list | `["Ingress"]` | Policy types used in the NetworkPolicy object. |

#### Pdb

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.pdb.annotations | object | `{}` | Annotations to be added to app pdb. |
| frontend.pdb.enabled | bool | `false` | Deploy a PodDisruptionBudget for the app |
| frontend.pdb.labels | object | `{}` | Labels to be added to app pdb. |
| frontend.pdb.maxUnavailable | string | `""` | Number of pods that are unavailable after eviction as number or percentage (eg.: 50%). Has higher precedence over `frontend.pdb.minAvailable`. |
| frontend.pdb.minAvailable | string | `""` (defaults to 0 if not specified) | Number of pods that are available after eviction as number or percentage (eg.: 50%). |

#### Probes

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.probes.livenessProbe.failureThreshold | int | `3` | Minimum consecutive failures for the probe to be considered failed after having succeeded. |
| frontend.probes.livenessProbe.httpGet.path | string | `"/"` | Frontend container healthcheck endpoint (livenessProbe is defined using `toYaml` so it is possible to override it completely). |
| frontend.probes.livenessProbe.httpGet.port | int | `8080` | Port to use for healthcheck (defaults to container port). |
| frontend.probes.livenessProbe.initialDelaySeconds | int | `30` | Number of seconds after the container has started before probe is initiated. |
| frontend.probes.livenessProbe.periodSeconds | int | `30` | How often (in seconds) to perform the probe. |
| frontend.probes.livenessProbe.successThreshold | int | `1` | Minimum consecutive successes for the probe to be considered successful after having failed. |
| frontend.probes.livenessProbe.timeoutSeconds | int | `5` | Number of seconds after which the probe times out. |
| frontend.probes.readinessProbe.failureThreshold | int | `2` | Minimum consecutive failures for the probe to be considered failed after having succeeded. |
| frontend.probes.readinessProbe.httpGet.path | string | `"/"` | Frontend container healthcheck endpoint (readinessProbe is defined using `toYaml` so it is possible to override it completely). |
| frontend.probes.readinessProbe.httpGet.port | int | `8080` | Port to use for healthcheck (defaults to container port). |
| frontend.probes.readinessProbe.initialDelaySeconds | int | `10` | Number of seconds after the container has started before probe is initiated. |
| frontend.probes.readinessProbe.periodSeconds | int | `10` | How often (in seconds) to perform the probe. |
| frontend.probes.readinessProbe.successThreshold | int | `2` | Minimum consecutive successes for the probe to be considered successful after having failed. |
| frontend.probes.readinessProbe.timeoutSeconds | int | `5` | Number of seconds after which the probe times out. |
| frontend.probes.startupProbe.failureThreshold | int | `10` | Minimum consecutive failures for the probe to be considered failed after having succeeded. |
| frontend.probes.startupProbe.httpGet.path | string | `"/"` | Frontend container healthcheck endpoint (startupProbe is defined using `toYaml` so it is possible to override it completely). |
| frontend.probes.startupProbe.httpGet.port | int | `8080` | Port to use for healthcheck (defaults to container port). |
| frontend.probes.startupProbe.initialDelaySeconds | int | `0` | Number of seconds after the container has started before probe is initiated. |
| frontend.probes.startupProbe.periodSeconds | int | `10` | How often (in seconds) to perform the probe. |
| frontend.probes.startupProbe.successThreshold | int | `1` | Minimum consecutive successes for the probe to be considered successful after having failed. |
| frontend.probes.startupProbe.timeoutSeconds | int | `5` | Number of seconds after which the probe times out. |

#### Resources

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.resources.limits.cpu | string | `"500m"` | CPU limit for the app. |
| frontend.resources.limits.memory | string | `"2Gi"` | Memory limit for the app. |
| frontend.resources.requests.cpu | string | `"100m"` | CPU request for the app. |
| frontend.resources.requests.memory | string | `"256Mi"` | Memory request for the app. |

#### Service

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.service.enabled | bool | `true` | Whether or not to create a Service for the app. Set to `false` for components that don't accept traffic (e.g. a queue consumer with no `containerPort`). |
| frontend.service.extraPorts | list | `[]` | Extra service ports. |
| frontend.service.nodePort | int | `31000` | Port used when type is `NodePort` to expose the service on the given node port. |
| frontend.service.port | int | `80` | Port used by the service. |
| frontend.service.portName | string | `"http"` | Port name used by the service. |
| frontend.service.protocol | string | `"TCP"` | Protocol used by the service. |
| frontend.service.type | string | `"ClusterIP"` | Type of service to create for the app. |

#### ServiceAccount

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.serviceAccount.annotations | object | `{}` | Annotations applied to created service account. |
| frontend.serviceAccount.automountServiceAccountToken | bool | `false` | Should the service account access token be automount in the pod. |
| frontend.serviceAccount.clusterRole.create | bool | `false` | Should the clusterRole be created. |
| frontend.serviceAccount.clusterRole.rules | list | `[]` | ClusterRole rules associated with the service account. |
| frontend.serviceAccount.create | bool | `false` | Create a service account. |
| frontend.serviceAccount.enabled | bool | `false` | Enable the service account. |
| frontend.serviceAccount.name | string | `""` | Service account name. |
| frontend.serviceAccount.role.create | bool | `false` | Should the role be created. |
| frontend.serviceAccount.role.rules | list | `[]` | Role rules associated with the service account. |

#### Strategy

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.strategy.rollingUpdate.maxSurge | int | `1` | The maximum number of pods that can be scheduled above the desired number of pods. |
| frontend.strategy.rollingUpdate.maxUnavailable | int | `1` | The maximum number of pods that can be unavailable during the update process. |
| frontend.strategy.type | string | `"RollingUpdate"` | Strategy type used to replace old Pods by new ones, can be `Recreate` or `RollingUpdate`. |

### Gateway

#### General

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| gateway.addresses | list | `[]` | Gateway addresses configuration. |
| gateway.annotations | object | `{}` | Additional gateway annotations. |
| gateway.className | string | `""` | GatewayClass name. Required when creating a Gateway. |
| gateway.create | bool | `false` | Create a Gateway resource. Usually, you reference an existing Gateway managed by the infrastructure team. |
| gateway.labels | object | `{}` | Additional gateway labels. |
| gateway.listeners | list | `[]` | Gateway listeners configuration. |
| gateway.name | string | `""` | Name of the Gateway resource. If not set, uses the release fullname. |

### Jobs

#### Migration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| jobs.migration.activeDeadlineSeconds | string | `nil` | Active deadline (in seconds) for the Job. If specified, the job will be terminated if it runs longer than this duration. |
| jobs.migration.affinity | object | `{}` | Default affinity for the migration job. |
| jobs.migration.args | list | `["alembic upgrade head"]` | Migration container command args. Defaults to running Alembic migrations up to the latest revision; override to run a different Alembic command (e.g. stamp then upgrade). |
| jobs.migration.backoffLimit | int | `10` | Number of retries before considering the Job as failed. |
| jobs.migration.command | list | `["/bin/sh","-c"]` | Migration container command. |
| jobs.migration.completions | string | `nil` | Number of successful completions required for the Job to be considered complete. If specified, the job will be considered complete when this many successful completions are reached. |
| jobs.migration.env | object | `{"DATABASE_URL":{"valueFrom":{"secretKeyRef":{"key":"uri","name":"abrege-postgres"}}}}` | Points at the top-level `postgres` values (the bundled, default database backend). Switching to `cnpg.enabled: true` for production requires overriding (or unsetting, e.g. `null`) this to point at CNPG's own credentials/secret instead - see `postgres`/`cnpg`. |
| jobs.migration.envCm | object | `{}` |  |
| jobs.migration.envFrom | list | `[]` | Migration container env variables loaded from configmap or secret reference. List or map (merged with `global.envFrom` above, global entries first); see `global.envFrom` for both forms. |
| jobs.migration.envSecret | object | `{}` | Map of environment variables to inject into a secret loaded by the migration container (`valueFrom` not supported). |
| jobs.migration.extraContainers | list | `[]` | Additional containers to run with the migration container. |
| jobs.migration.extraVolumeMounts | list | `[]` | List of extra volume mounts to add to the migration job. |
| jobs.migration.extraVolumes | list | `[]` | List of extra volumes to add to the migration job. |
| jobs.migration.hook.deletePolicy | string | `"before-hook-creation,hook-succeeded"` | Hook delete policy to control when the job is deleted. `before-hook-creation` and `hook-succeeded` are common choices. |
| jobs.migration.hook.enabled | bool | `true` | Enable the Helm hook for this job. |
| jobs.migration.hook.types | list | `["post-install","post-upgrade"]` | Hook events to trigger this job. `post-install` and `post-upgrade` are the most common. |
| jobs.migration.hook.weight | int | `1` | Hook weight to control the order of execution when multiple hooks are defined. Lower weights execute first. |
| jobs.migration.hostAliases | list | `[]` | List of host aliases to add to the migration job. |
| jobs.migration.image.pullPolicy | string | `"IfNotPresent"` | Image pull policy for the migration job. |
| jobs.migration.image.registry | string | `"ghcr.io"` | Registry to use for the migration job. |
| jobs.migration.image.repository | string | `"ia-generative/abrege/api"` | Repository to use for the migration job. |
| jobs.migration.image.tag | string | `""` | Tag to use for the migration job. Overrides the image tag whose default is the chart appVersion. |
| jobs.migration.imagePullSecrets | list | `[]` | Image credentials configuration. |
| jobs.migration.initContainers[0].command | list | `["sh","-c","until nc -z abrege-postgres 5432; do echo 'Waiting for PostgreSQL...'; sleep 2; done"]` | Init container command to wait for the bundled `postgres` (default database backend) to accept connections. Update/remove this (e.g. to target CNPG's own service instead) when switching `cnpg.enabled: true` for production. |
| jobs.migration.initContainers[0].image | string | `"docker.io/busybox:1.37"` | Init container image to use for the wait-for-postgres init container. |
| jobs.migration.initContainers[0].imagePullPolicy | string | `"IfNotPresent"` | Init container image pull policy for the wait-for-postgres init container. |
| jobs.migration.initContainers[0].name | string | `"wait-for-postgres"` | Init container to wait for the bundled `postgres` (default database backend) to accept connections. Update/remove this (e.g. to target CNPG's own service instead) when switching `cnpg.enabled: true` for production. |
| jobs.migration.initContainers[0].resources.limits.cpu | string | `"50m"` | CPU limit for the wait-for-postgres init container. |
| jobs.migration.initContainers[0].resources.limits.memory | string | `"32Mi"` | Memory limit for the wait-for-postgres init container. |
| jobs.migration.initContainers[0].resources.requests.cpu | string | `"10m"` | CPU request for the wait-for-postgres init container. |
| jobs.migration.initContainers[0].resources.requests.memory | string | `"16Mi"` | Memory request for the wait-for-postgres init container. |
| jobs.migration.initContainers[0].securityContext | object | `{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]},"readOnlyRootFilesystem":true,"runAsNonRoot":true,"runAsUser":10001,"seccompProfile":{"type":"RuntimeDefault"}}` | Init container-level security context for the wait-for-postgres init container. Rendered via `toYaml`, so any other `SecurityContext` field (e.g. `runAsGroup`, `procMount`) can be added here too, even though not pre-populated below. |
| jobs.migration.nodeSelector | object | `{}` | Default node selector for the migration job. |
| jobs.migration.parallelism | int | `1` | Number of pods to run in parallel for the Job. If specified, the job will run this many pods in parallel. |
| jobs.migration.podAnnotations | object | `{}` |  |
| jobs.migration.podLabels | object | `{}` |  |
| jobs.migration.podSecurityContext | object | `{"fsGroup":10001,"runAsNonRoot":true,"seccompProfile":{"type":"RuntimeDefault"}}` | Pod-level security context. Rendered via `toYaml`, so any other `PodSecurityContext` field (e.g. `runAsGroup`, `sysctls`, `supplementalGroups`) can be added here too, even though not pre-populated below. |
| jobs.migration.resources.limits.cpu | string | `"20m"` | CPU limit for the migration job. |
| jobs.migration.resources.limits.memory | string | `"128Mi"` | Memory limit for the migration job. |
| jobs.migration.resources.requests.cpu | string | `"10m"` | CPU request for the migration job. |
| jobs.migration.resources.requests.memory | string | `"64Mi"` | Memory request for the migration job. |
| jobs.migration.restartPolicy | string | `"Never"` | Restart policy for the Job's pods. Can be `Always`, `OnFailure`, or `Never`. |
| jobs.migration.securityContext | object | `{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]},"readOnlyRootFilesystem":true,"runAsNonRoot":true,"runAsUser":10001,"seccompProfile":{"type":"RuntimeDefault"}}` | Container-level security context. Rendered via `toYaml`, so any other `SecurityContext` field (e.g. `runAsGroup`, `procMount`) can be added here too, even though not pre-populated below. |
| jobs.migration.serviceAccount.annotations | object | `{}` |  |
| jobs.migration.serviceAccount.automountServiceAccountToken | bool | `false` |  |
| jobs.migration.serviceAccount.create | bool | `false` |  |
| jobs.migration.serviceAccount.enabled | bool | `false` |  |
| jobs.migration.serviceAccount.name | string | `""` |  |
| jobs.migration.tolerations | list | `[]` | Default tolerations for the migration job. |
| jobs.migration.ttlSecondsAfterFinished | int | `300` | Time to live (in seconds) after the Job finishes before it is garbage collected. |
| jobs.migration.volumeMounts | list | `[]` | List of volume mounts to add to the migration job. |
| jobs.migration.volumes | list | `[]` | List of volumes to add to the migration job. |

### Postgres

#### General

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| postgres.enabled | bool | `true` | Deploy the bundled postgres subchart. |
| postgres.fullnameOverride | string | `"abrege-postgres"` | Override the name used for postgres resources. |

#### Auth

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| postgres.auth.existingSecret | string | `""` | Name of a pre-existing secret to use instead of the one above (e.g. Vault-managed). Must be named identically to `fullnameOverride` above and already contain the keys the chart would otherwise generate (`uri`, `postgres-password`, `host`, `port`, `username`, `database`) - when set, the chart generates no Secret of its own (same pattern as `redis.auth.existingSecret` below). |
| postgres.auth.password | string | `""` | Password for the auto-created postgres superuser. Leave empty (default) to auto-generate a random password on first install (plug-and-play) - the chart-generated "<fullnameOverride>" Secret's `uri` key (consumed by `api.env.DATABASE_URL`/`worker.env.DATABASE_URL` below) is built from it either way. |

#### ContainerSecurityContext

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| postgres.containerSecurityContext.allowPrivilegeEscalation | bool | `false` |  |
| postgres.containerSecurityContext.capabilities.drop[0] | string | `"ALL"` |  |
| postgres.containerSecurityContext.runAsNonRoot | bool | `true` |  |
| postgres.containerSecurityContext.runAsUser | int | `10001` |  |
| postgres.containerSecurityContext.seccompProfile.type | string | `"RuntimeDefault"` |  |

#### Persistence

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| postgres.persistence.size | string | `"5Gi"` | Size of the PersistentVolumeClaim for PostgreSQL data. |

#### PodSecurityContext

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| postgres.podSecurityContext.fsGroup | int | `10001` |  |
| postgres.podSecurityContext.runAsNonRoot | bool | `true` |  |
| postgres.podSecurityContext.seccompProfile.type | string | `"RuntimeDefault"` |  |

#### Resources

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| postgres.resources.limits.cpu | string | `"250m"` | CPU limit for the PostgreSQL container. |
| postgres.resources.limits.memory | string | `"512Mi"` | Memory limit for the PostgreSQL container. |
| postgres.resources.requests.cpu | string | `"50m"` | CPU request for the PostgreSQL container. |
| postgres.resources.requests.memory | string | `"128Mi"` | Memory request for the PostgreSQL container. |

### Redis

#### General

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| redis.architecture | string | `"replication"` | Redis architecture (`standalone` or `replication`). Kept as `replication` even with a single replica/no Sentinel below, purely so the exposed Service name/address stays identical whether or not Sentinel/extra replicas are later enabled for production (see note above). |
| redis.enabled | bool | `true` | Deploy the bundled redis subchart. |
| redis.fullnameOverride | string | `"abrege-redis"` | Override the name used for redis resources. |
| redis.replicaCount | int | `1` | Number of Redis instances to deploy (1 master + N-1 replicas when `architecture` is `replication`). Kept at `1` (master only, no replicas) by default for a plug-and-play install; raise this for production HA. |

#### Auth

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| redis.auth.enabled | bool | `true` | Enable Redis password authentication (secure by default). |
| redis.auth.existingSecret | string | `""` | Name of a pre-existing secret to use instead of the one above (e.g. Vault-managed). Must be named identically to `fullnameOverride` above and already contain the key named by `existingSecretPasswordKey` below - when set, the chart generates no Secret of its own (same pattern as `postgres.auth.existingSecret` above). |
| redis.auth.existingSecretPasswordKey | string | `"redis-password"` | Key inside `existingSecret` (or the chart-generated secret) holding the Redis password. |
| redis.auth.password | string | `""` | Redis password. Leave empty (default) to auto-generate a random password on first install (plug-and-play) - the chart-generated "<fullnameOverride>" Secret's `redis-password` key (see `existingSecretPasswordKey` below) is set from it either way. |
| redis.auth.sentinel | bool | `true` | Enable Sentinel authentication (only relevant when `sentinel.enabled` below is `true`). In this chart's non-ACL auth mode there is only one real password - when enabled, the Sentinel process's own `requirepass` is set from this same `password`/`existingSecret` too (there is no separate value/key for a distinct Sentinel-only password). |

#### ContainerSecurityContext

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| redis.containerSecurityContext.allowPrivilegeEscalation | bool | `false` |  |
| redis.containerSecurityContext.capabilities.drop[0] | string | `"ALL"` |  |
| redis.containerSecurityContext.runAsNonRoot | bool | `true` |  |
| redis.containerSecurityContext.runAsUser | int | `10001` |  |
| redis.containerSecurityContext.seccompProfile.type | string | `"RuntimeDefault"` |  |

#### InitContainer

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| redis.initContainer.resources.limits.cpu | string | `"25m"` | CPU limit for the volume-permissions init container. |
| redis.initContainer.resources.limits.memory | string | `"64Mi"` | Memory limit for the volume-permissions init container. |
| redis.initContainer.resources.requests.cpu | string | `"25m"` | CPU request for the volume-permissions init container. |
| redis.initContainer.resources.requests.memory | string | `"64Mi"` | Memory request for the volume-permissions init container. |

#### Persistence

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| redis.persistence.enabled | bool | `true` | Enable a PersistentVolumeClaim for Redis data. |
| redis.persistence.size | string | `"5Gi"` | Size of the PersistentVolumeClaim for Redis data. |

#### PodSecurityContext

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| redis.podSecurityContext.fsGroup | int | `10001` |  |
| redis.podSecurityContext.runAsNonRoot | bool | `true` |  |
| redis.podSecurityContext.seccompProfile.type | string | `"RuntimeDefault"` |  |

#### Resources

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| redis.resources.limits.cpu | string | `"100m"` | CPU limit for the Redis container. |
| redis.resources.limits.memory | string | `"256Mi"` | Memory limit for the Redis container. |
| redis.resources.requests.cpu | string | `"50m"` | CPU request for the Redis container. |
| redis.resources.requests.memory | string | `"128Mi"` | Memory request for the Redis container. |

#### Sentinel

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| redis.sentinel.downAfterMilliseconds | int | `5000` | Milliseconds after which the master is considered down if unreachable. |
| redis.sentinel.enabled | bool | `false` | Enable Sentinel for automatic master failover. Disabled by default (single replica, see `replicaCount` above); turn on together with a higher `replicaCount` for production HA. The KEDA ScaledObject trigger (`worker.kedaAutoscaler.redis.address`) only supports a single plain address, not native sentinel discovery - `masterService.enabled` below keeps exposing a stable "<fullnameOverride>-master" Service either way, so flipping this doesn't require any other change. |
| redis.sentinel.failoverTimeout | int | `60000` | Milliseconds to wait before considering a failover attempt failed. |
| redis.sentinel.masterName | string | `"abrege-redis"` | Name Sentinel uses to identify the monitored master group. |
| redis.sentinel.masterService.checkInterval | int | `30` | Interval (in seconds) at which the master-service discovery Deployment checks Sentinel for the current master. |
| redis.sentinel.masterService.enabled | bool | `false` | When Sentinel is enabled, keep exposing a stable "<fullnameOverride>-master" Service (same name/behavior as without Sentinel) via a small chart-managed discovery Deployment that dynamically repoints it at whichever pod Sentinel currently elected as master. |
| redis.sentinel.parallelSyncs | int | `1` | Number of replicas Sentinel resyncs from the new master simultaneously during a failover. |
| redis.sentinel.quorum | int | `2` | Minimum number of Sentinels that must agree the master is down before triggering failover. |
| redis.sentinel.resources.limits.cpu | string | `"100m"` | CPU limit for the Sentinel container. |
| redis.sentinel.resources.limits.memory | string | `"256Mi"` | Memory limit for the Sentinel container. |
| redis.sentinel.resources.requests.cpu | string | `"50m"` | CPU request for the Sentinel container. |
| redis.sentinel.resources.requests.memory | string | `"128Mi"` | Memory request for the Sentinel container. |

### Rustfs

#### General

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| rustfs.enabled | bool | `true` | Deploy the bundled RustFS subchart. |
| rustfs.fullnameOverride | string | `"abrege-rustfs"` | Override the name used for RustFS resources. |

#### Auth

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| rustfs.auth.accessKey | string | `"rustfsadmin"` | RustFS access key (not secret-backed - unlike `secretKey` below, this is a plain value). |
| rustfs.auth.existingSecret | string | `""` | Name of a pre-existing secret to use instead of the one above (e.g. Vault-managed). Must be named identically to `fullnameOverride` above and already contain the keys named by `existingSecretAccessKeyKey`/`existingSecretSecretKeyKey` below - when set, the chart generates no Secret of its own (same pattern as `redis.auth.existingSecret` above). Unlike postgres/redis (single password), RustFS needs an access/secret key *pair* - both keys live in the same secret. |
| rustfs.auth.existingSecretAccessKeyKey | string | `"access-key"` | Key inside `existingSecret` (or the chart-generated secret) holding the access key. |
| rustfs.auth.existingSecretSecretKeyKey | string | `"secret-key"` | Key inside `existingSecret` (or the chart-generated secret) holding the secret key. |
| rustfs.auth.secretKey | string | `""` | RustFS secret key. Leave empty (default) to auto-generate a random one on first install (plug-and-play) - the chart-generated "<fullnameOverride>" Secret's `secret-key` key (see `existingSecretSecretKeyKey` below) is set from it either way. |

#### ContainerSecurityContext

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| rustfs.containerSecurityContext.allowPrivilegeEscalation | bool | `false` |  |
| rustfs.containerSecurityContext.capabilities.drop[0] | string | `"ALL"` |  |
| rustfs.containerSecurityContext.runAsNonRoot | bool | `true` |  |
| rustfs.containerSecurityContext.runAsUser | int | `10001` |  |
| rustfs.containerSecurityContext.seccompProfile.type | string | `"RuntimeDefault"` |  |

#### DataPersistence

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| rustfs.dataPersistence.size | string | `"5Gi"` | Size of the PersistentVolumeClaim for RustFS data. |

#### PodSecurityContext

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| rustfs.podSecurityContext.fsGroup | int | `10001` |  |
| rustfs.podSecurityContext.runAsNonRoot | bool | `true` |  |
| rustfs.podSecurityContext.seccompProfile.type | string | `"RuntimeDefault"` |  |

#### Resources

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| rustfs.resources.limits.cpu | string | `"250m"` | CPU limit for the RustFS container. |
| rustfs.resources.limits.memory | string | `"512Mi"` | Memory limit for the RustFS container. |
| rustfs.resources.requests.cpu | string | `"50m"` | CPU request for the RustFS container. |
| rustfs.resources.requests.memory | string | `"128Mi"` | Memory request for the RustFS container. |

### Worker

#### General

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.affinity | object | `{}` | Affinity used for app pod. |
| worker.args | list | `[]` | Worker container command args. |
| worker.celeryConfig | string | `"worker_concurrency = 1\nworker_pool = \"prefork\"\ntimezone = \"Europe/Paris\"\nbroker_connection_retry_on_startup = True\ntask_acks_late = True\nworker_prefetch_multiplier = 1\nworker_cancel_long_running_tasks_on_connection_loss = True\nworker_hijack_root_logger = False\n"` | Celery configuration for the worker container, rendered as-is into the `templates/worker/celeryconfig.yaml` ConfigMap (mounted as `celeryconfig.py`, see `volumes`/`volumeMounts` below) and genuinely loaded: `command` below passes `--config celeryconfig` to the `celery` CLI, which reads this module (verified against Celery 5.6.3's own CLI reference - `--config` is still a valid global option, positioned before the `worker` subcommand per Celery 5.x's CLI convention). The equivalent `api.celeryConfig` was removed: the api container never invokes the `celery` CLI (its entrypoint is a plain uvicorn server) and nothing in the app reads `CELERY_CONFIG_MODULE` either, so that ConfigMap/mount were pure dead weight there. |
| worker.command | list | `["celery","--config","celeryconfig","-A","abrege_service.main","worker","-E"]` | Worker container command. |
| worker.containerPort | string | `nil` | Worker container port number. Set to `null` since this component only consumes a Celery queue and never accepts traffic (see `service.enabled` below). |
| worker.containerPortName | string | `"http"` | Worker container port name. |
| worker.deploymentType | string | `"Deployment"` | Workload kind to deploy the app as. One of "Deployment" or "StatefulSet". |
| worker.env | object | `{"AWS_ACCESS_KEY_ID":"rustfsadmin","AWS_BUCKET_NAME":"abrege","AWS_DEFAULT_REGION":"us-east-1","AWS_ENDPOINT_URL":"http://abrege-rustfs:9000","AWS_SECRET_ACCESS_KEY":{"valueFrom":{"secretKeyRef":{"key":"secret-key","name":"abrege-rustfs"}}},"CELERY_APP_NAME":"abrege","DATABASE_URL":{"valueFrom":{"secretKeyRef":{"key":"uri","name":"abrege-postgres"}}},"REDIS_HOST":"abrege-redis-master","UV_CACHE_DIR":"/app/.cache/"}` | Map or array of environment variables to inject into the app container (`valueFrom` supported). |
| worker.envCm | object | `{}` | Map of environment variables to inject into a configmap loaded by the app container (`valueFrom` not supported). |
| worker.envFrom | list | `[]` | Worker container env variables loaded from configmap or secret reference. List or map (merged with `global.envFrom` above, global entries first); see `global.envFrom` for both forms. |
| worker.envSecret | object | `{}` | Map of environment variables to inject into a secret loaded by the app container (`valueFrom` not supported). |
| worker.extraContainers | list | `[]` | Extra containers to add to the app pod as sidecars. |
| worker.extraPorts | list | `[]` | Worker extra container ports. |
| worker.extraVolumeClaims | list | `[]` | Additional volumeClaims to add, concatenated with `volumeClaims` above at render time. |
| worker.extraVolumeMounts | list | `[]` | Additional volumeMounts to add, concatenated with `volumeMounts` above at render time. |
| worker.extraVolumes | list | `[]` | Additional volumes to add, concatenated with `volumes` above at render time. |
| worker.hostAliases | list | `[]` | Host aliases that will be injected at pod-level into /etc/hosts. |
| worker.imagePullSecrets | list | `[]` | Image credentials configuration. |
| worker.initContainers | list | `[]` | Init containers to add to the app pod. |
| worker.nodeSelector | object | `{}` | Default node selector for app. |
| worker.podAnnotations | object | `{}` | Annotations for the app deployed pods. |
| worker.podLabels | object | `{}` | Labels for the app deployed pods. |
| worker.podSecurityContext | object | `{"fsGroup":10001,"runAsNonRoot":true,"runAsUser":10001,"seccompProfile":{"type":"RuntimeDefault"}}` | Pod-level security context. Rendered via `toYaml`, so any other `PodSecurityContext` field (e.g. `runAsGroup`, `sysctls`, `supplementalGroups`) can be added here too, even though not pre-populated below. |
| worker.replicaCount | int | `1` | The number of application controller pods to run. Kept at `1` by default so the chart deploys plug-and-play with minimal resources; bump this (and/or enable `worker.kedaAutoscaler`) for production. |
| worker.revisionHistoryLimit | int | `10` | Revision history limit for the app. |
| worker.securityContext | object | `{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]},"readOnlyRootFilesystem":true,"runAsNonRoot":true,"runAsUser":10001,"seccompProfile":{"type":"RuntimeDefault"}}` | Container-level security context. Rendered via `toYaml`, so any other `SecurityContext` field (e.g. `runAsGroup`, `procMount`) can be added here too, even though not pre-populated below. |
| worker.terminationGracePeriodSeconds | int | `600` | Grace period k8s gives the worker to shut down before SIGKILL. Worker tasks (LLM calls, audio/video transcription) run for minutes, so the 30s k8s default would SIGKILL the pod mid-task on every rollout / KEDA scale-down. Raised so Celery's warm shutdown can finish the in-flight task first; anything still running past this window is caught by `task_acks_late` (see `celeryConfig`) and redelivered/resumed. Keep it below the KEDA `cooldownPeriod` horizon and rollout expectations so a stuck worker cannot block scale-down forever. |
| worker.tolerations | list | `[]` | Default tolerations for app. |
| worker.volumeClaims | list | `[]` | List of volumeClaims to add. |
| worker.volumeMounts | list | `[{"mountPath":"/app/celeryconfig.py","name":"celeryconfig","subPath":"celeryconfig.py"},{"mountPath":"/app/.cache/","name":"cache"},{"mountPath":"/app/.tmp/","name":"tmp"},{"mountPath":"/tmp/","name":"run-tmp"}]` | List of mounts to add (normally used with `volumes` or `volumeClaims`). |
| worker.volumes | list | `[{"configMap":{"name":"{{ printf \"%s-%s\" (include \"helper.fullname\" .) \"worker-celery\" }}"},"name":"celeryconfig"},{"emptyDir":{},"name":"cache"},{"emptyDir":{},"name":"tmp"},{"emptyDir":{},"name":"run-tmp"}]` | List of volumes to add. |

#### Autoscaling

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.autoscaling.enabled | bool | `false` | Enable Horizontal Pod Autoscaler for the app. |
| worker.autoscaling.maxReplicas | int | `3` | Maximum number of replicas for the app. |
| worker.autoscaling.minReplicas | int | `1` | Minimum number of replicas for the app. |
| worker.autoscaling.targetCPUUtilizationPercentage | int | `80` | Average CPU utilization percentage for the app. |
| worker.autoscaling.targetMemoryUtilizationPercentage | int | `80` | Average memory utilization percentage for the app. |

#### GrpcRoute

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.grpcRoute.annotations | object | `{}` | Additional GRPCRoute annotations. |
| worker.grpcRoute.enabled | bool | `false` | Enable a GRPCRoute resource for this service. |
| worker.grpcRoute.hostnames | list | `[]` | Hostnames for the GRPCRoute to match. |
| worker.grpcRoute.labels | object | `{}` | Additional GRPCRoute labels. |
| worker.grpcRoute.parentRefs | list | `[]` | Parent references (Gateways) to attach the GRPCRoute to. |
| worker.grpcRoute.rules | list | `[]` | Routing rules for the GRPCRoute. |

#### HttpRoute

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.httpRoute.annotations | object | `{}` | Additional HTTPRoute annotations. |
| worker.httpRoute.enabled | bool | `false` | Enable an HTTPRoute resource for this service. |
| worker.httpRoute.hostnames | list | `[]` | Hostnames for the HTTPRoute to match. |
| worker.httpRoute.labels | object | `{}` | Additional HTTPRoute labels. |
| worker.httpRoute.parentRefs | list | `[]` | Parent references (Gateways) to attach the HTTPRoute to. |
| worker.httpRoute.rules | list | `[]` | Routing rules for the HTTPRoute. |

#### Image

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.image.pullPolicy | string | `"IfNotPresent"` | Image pull policy for the app. |
| worker.image.registry | string | `"ghcr.io"` | Registry to use for the app. |
| worker.image.repository | string | `"ia-generative/abrege/worker"` | Repository to use for the app. |
| worker.image.tag | string | `""` | Tag to use for the app. Overrides the image tag whose default is the chart appVersion. |

#### Ingress

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.ingress.annotations | object | `{}` | Additional ingress annotations. |
| worker.ingress.className | string | `""` | Defines which ingress controller will implement the resource. |
| worker.ingress.enabled | bool | `false` | Whether or not ingress should be enabled. |
| worker.ingress.hosts[0].name | string | `"domain.local"` | Name of the host record. |
| worker.ingress.hosts[0].paths[0].backend.portNumber | string | `nil` | Port used by the backend service linked to the path (leave null to use the app service port). |
| worker.ingress.hosts[0].paths[0].backend.serviceName | string | `""` | Name of the backend service linked to the path (leave empty to use the app service). |
| worker.ingress.hosts[0].paths[0].path | string | `"/"` | Path of the host record to manage routing. |
| worker.ingress.hosts[0].paths[0].pathType | string | `"Prefix"` | Path type of the host record. |
| worker.ingress.labels | object | `{}` | Additional ingress labels. |
| worker.ingress.tls | list | `[]` | Enable TLS configuration. |

#### KedaAutoscaler

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.kedaAutoscaler.behavior.scaleDown.stabilizationWindowSeconds | int | `300` | Stabilization window for scaling down (in seconds). |
| worker.kedaAutoscaler.behavior.scaleUp.stabilizationWindowSeconds | int | `30` | Stabilization window for scaling up (in seconds). |
| worker.kedaAutoscaler.cooldownPeriod | int | `300` | Cooldown period before scaling down (in seconds). |
| worker.kedaAutoscaler.enabled | bool | `false` | Enable KEDA autoscaling. |
| worker.kedaAutoscaler.fallback.failureThreshold | int | `3` | Failure threshold to activate fallback. |
| worker.kedaAutoscaler.fallback.replicas | int | `1` | Number of replicas during fallback. |
| worker.kedaAutoscaler.maxReplicaCount | int | `10` | Maximum number of replicas. |
| worker.kedaAutoscaler.minReplicaCount | int | `1` | Minimum number of replicas. |
| worker.kedaAutoscaler.pollingInterval | int | `30` | Interval between trigger checks (in seconds). |
| worker.kedaAutoscaler.redis.address | string | `""` | Redis server address. Leave empty to use the default `redis.fullnameOverride`/`redis.service.port` from the bundled Redis chart. |
| worker.kedaAutoscaler.redis.authenticationRef | string | `"abrege-worker"` | Name of the KEDA `TriggerAuthentication` resource (created by this chart when `redis.secretRef`/`redis.secretKey` below are set) that supplies Redis credentials to the `ScaledObject`. |
| worker.kedaAutoscaler.redis.listLength | string | `"5"` | Redis list target length. |
| worker.kedaAutoscaler.redis.listName | string | `"celery"` | Redis list name to monitor. |
| worker.kedaAutoscaler.redis.password | string | `""` | Redis password (optional). |
| worker.kedaAutoscaler.redis.secretKey | string | `""` | Redis authentication secret key. |
| worker.kedaAutoscaler.redis.secretRef | string | `""` | Redis authentication secret name. |

#### Metrics

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.metrics.enabled | bool | `false` | Deploy metrics service. |
| worker.metrics.service.annotations | object | `{}` | Metrics service annotations. |
| worker.metrics.service.labels | object | `{}` | Metrics service labels. |
| worker.metrics.service.port | int | `9000` | Metrics service port. |
| worker.metrics.service.portName | string | `"metrics"` | Metrics service port name. |
| worker.metrics.service.targetPort | int | `9000` | Metrics service target port. |
| worker.metrics.serviceMonitor.annotations | object | `{}` | Prometheus ServiceMonitor annotations. |
| worker.metrics.serviceMonitor.enabled | bool | `false` | Enable a prometheus ServiceMonitor. |
| worker.metrics.serviceMonitor.endpoints[0].basicAuth.password | string | `""` | The secret in the service monitor namespace that contains the password for authentication. |
| worker.metrics.serviceMonitor.endpoints[0].basicAuth.username | string | `""` | The secret in the service monitor namespace that contains the username for authentication. |
| worker.metrics.serviceMonitor.endpoints[0].bearerTokenSecret.key | string | `""` | Secret key to mount to read bearer token for scraping targets. The secret needs to be in the same namespace as the service monitor and accessible by the Prometheus Operator. |
| worker.metrics.serviceMonitor.endpoints[0].bearerTokenSecret.name | string | `""` | Secret name to mount to read bearer token for scraping targets. The secret needs to be in the same namespace as the service monitor and accessible by the Prometheus Operator. |
| worker.metrics.serviceMonitor.endpoints[0].honorLabels | bool | `false` | When true, honorLabels preserves the metric’s labels when they collide with the target’s labels. |
| worker.metrics.serviceMonitor.endpoints[0].interval | string | `"30s"` | Prometheus ServiceMonitor interval. |
| worker.metrics.serviceMonitor.endpoints[0].metricRelabelings | list | `[]` | Prometheus MetricRelabelConfigs to apply to samples before ingestion. |
| worker.metrics.serviceMonitor.endpoints[0].path | string | `"/metrics"` | Path used by the Prometheus ServiceMonitor to scrape metrics. |
| worker.metrics.serviceMonitor.endpoints[0].relabelings | list | `[]` | Prometheus RelabelConfigs to apply to samples before scraping. |
| worker.metrics.serviceMonitor.endpoints[0].scheme | string | `""` | Prometheus ServiceMonitor scheme. |
| worker.metrics.serviceMonitor.endpoints[0].scrapeTimeout | string | `"10s"` | Prometheus ServiceMonitor scrapeTimeout. If empty, Prometheus uses the global scrape timeout unless it is less than the target's scrape interval value in which the latter is used. |
| worker.metrics.serviceMonitor.endpoints[0].selector | object | `{}` | Prometheus ServiceMonitor selector. |
| worker.metrics.serviceMonitor.endpoints[0].tlsConfig | object | `{}` | Prometheus ServiceMonitor tlsConfig. |
| worker.metrics.serviceMonitor.labels | object | `{}` | Prometheus ServiceMonitor labels. |

#### NetworkPolicy

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.networkPolicy.create | bool | `false` | Create NetworkPolicy object for the app. |
| worker.networkPolicy.egress | list | `[]` | Egress rules for the NetworkPolicy object. |
| worker.networkPolicy.ingress | list | `[]` | Ingress rules for the NetworkPolicy object. |
| worker.networkPolicy.policyTypes | list | `["Ingress"]` | Policy types used in the NetworkPolicy object. |

#### Pdb

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.pdb.annotations | object | `{}` | Annotations to be added to app pdb. |
| worker.pdb.enabled | bool | `false` | Deploy a PodDisruptionBudget for the app |
| worker.pdb.labels | object | `{}` | Labels to be added to app pdb. |
| worker.pdb.maxUnavailable | string | `""` | Number of pods that are unavailable after eviction as number or percentage (eg.: 50%). Has higher precedence over `worker.pdb.minAvailable`. |
| worker.pdb.minAvailable | string | `""` (defaults to 0 if not specified) | Number of pods that are available after eviction as number or percentage (eg.: 50%). |

#### Probes

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.probes.livenessProbe | object | `{}` | Worker liveness probe. Empty by default, same reasoning as `startupProbe` above. |
| worker.probes.readinessProbe | object | `{}` | Worker readiness probe. Empty by default, same reasoning as `startupProbe` above. |
| worker.probes.startupProbe | object | `{}` | Worker startup probe. Empty by default: this component only consumes a Celery queue and exposes no HTTP endpoint to probe (unlike `api`/`frontend`). Defined using `toYaml`, so any Kubernetes probe (`httpGet`, `exec`, `tcpSocket`, ...) can be set here. |

#### Resources

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.resources.limits.cpu | string | `"2"` | CPU limit for the app. |
| worker.resources.limits.memory | string | `"4Gi"` | Memory limit for the app. |
| worker.resources.requests.cpu | string | `"2"` | CPU request for the app. |
| worker.resources.requests.memory | string | `"4Gi"` | Memory request for the app. |

#### Service

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.service.enabled | bool | `false` | Whether or not to create a Service for the app. Disabled by default: this component only consumes a Celery queue and never accepts traffic. |
| worker.service.extraPorts | list | `[]` | Extra service ports. |
| worker.service.nodePort | int | `31000` | Port used when type is `NodePort` to expose the service on the given node port. |
| worker.service.port | int | `80` | Port used by the service. |
| worker.service.portName | string | `"http"` | Port name used by the service. |
| worker.service.protocol | string | `"TCP"` | Protocol used by the service. |
| worker.service.type | string | `"ClusterIP"` | Type of service to create for the app. |

#### ServiceAccount

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.serviceAccount.annotations | object | `{}` | Annotations applied to created service account. |
| worker.serviceAccount.automountServiceAccountToken | bool | `false` | Should the service account access token be automount in the pod. |
| worker.serviceAccount.clusterRole.create | bool | `false` | Should the clusterRole be created. |
| worker.serviceAccount.clusterRole.rules | list | `[]` | ClusterRole rules associated with the service account. |
| worker.serviceAccount.create | bool | `false` | Create a service account. |
| worker.serviceAccount.enabled | bool | `false` | Enable the service account. |
| worker.serviceAccount.name | string | `""` | Service account name. |
| worker.serviceAccount.role.create | bool | `false` | Should the role be created. |
| worker.serviceAccount.role.rules | list | `[]` | Role rules associated with the service account. |

#### Strategy

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| worker.strategy.rollingUpdate.maxSurge | int | `1` | The maximum number of pods that can be scheduled above the desired number of pods. |
| worker.strategy.rollingUpdate.maxUnavailable | int | `1` | The maximum number of pods that can be unavailable during the update process. |
| worker.strategy.type | string | `"RollingUpdate"` | Strategy type used to replace old Pods by new ones, can be `Recreate` or `RollingUpdate`. |

## Sources

**Source code:**

* <https://github.com/IA-Generative/abrege>

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
