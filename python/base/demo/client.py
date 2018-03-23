#!/usr/bin/env python3.5
from kubernetes.client import CoreV1Api, ApiClient
from kubernetes import config as k8sconfig, stream, watch
import json, requests
from io import BytesIO, StringIO
from logging import getLogger

from . import state, State, models
from .decorators import expiring_cache

if state.KUBERNETES_TOKEN_PATH is None or state.KUBERNETES_CA_PATH is None:
    k8sconfig.incluster_config.load_incluster_config()
else:
    k8sconfig.incluster_config.InClusterConfigLoader(
        state.KUBERNETES_TOKEN_PATH,
        state.KUBERNETES_CA_PATH).load_and_set()

k8sclient = State()
k8sclient.v1 = CoreV1Api()
k8sclient.api = ApiClient()

logger = getLogger(__name__)

def serialize(value):
    return k8sclient.api.sanitize_for_serialization(value)

def _build_Pod(k8sPod):
    name = k8sPod.metadata.name
    ip = k8sPod.status.pod_ip
    phase = k8sPod.status.phase
    statuses = k8sPod.status.container_statuses
    statuses = list(map(lambda x: x.state, statuses if statuses is not None else [] ))
    state = list(map(lambda x: 't' if x.terminated is not None else
        'w' if x.waiting is not None else
        'r'
        , statuses))
    calculated_state = ['Terminating' if 't' in state and 'Running' == phase else
        'Terminating' if 't' in state else
        'Creating' if 'w' in state else
        'Creating' if phase == 'Pending' else
        'Crashing' if phase in [ 'Failed', 'Unknown' ] else
        'Running'][0]
    logger.info("%s: phase=%s; state=%s; calc_state=%s", name, phase, state, calculated_state)
    volume = list(filter(lambda x: x.persistent_volume_claim is not None, k8sPod.spec.volumes))
    volume = volume[0].persistent_volume_claim.claim_name if volume else ''
    return models.Pod(name, ip, phase, calculated_state, volume)

def generator_my_pods_watch():
    func = k8sclient.v1.list_namespaced_pod
    ns = state.namespace
    name = state.NAME
    w = watch.Watch()
    def generate(w, func, ns, name):
        for event in w.stream(func, _request_timeout=60, namespace=ns, label_selector='name='+name):
            pod = _build_Pod(event['object'])
            pod = dict(type=serialize(event['type']), object=pod.asdict())
            yield 'event: ' + pod['type'].lower() + '\n' + \
                'data: ' + json.dumps(pod) + '\n\n'
    return generate(w, func, ns, name)

@expiring_cache(maxsize=2)
def get_my_pods():
    return nocache_get_my_pods();

def nocache_get_my_pods():
    pods = k8sclient.v1.list_namespaced_pod(namespace=state.namespace, label_selector='name='+state.NAME)
    # pods = list(filter(lambda x: x.status.phase == 'Running', pods.items))
    ret  = list(map(lambda x: _build_Pod(x), pods.items))
    return models.PodList(*ret)

@expiring_cache(maxsize=2)
def get_my_pvcs():
    ret = k8sclient.v1.list_namespaced_persistent_volume_claim(namespace=state.namespace)
    items = list(filter(lambda x: x.metadata.name.startswith('%s-claim-' % state.NAME), ret.items))
    ret = []
    for pvc in items:
        item = models.Pvc(pvc.metadata.name, pvc.status.access_modes[0], pvc.status.capacity['storage'])
        ret.append(item)
    return models.PvcList(*ret)

def _get_url_from_pod_via_exec(pod_name, url):
    resp = stream.stream(k8sclient.v1.connect_post_namespaced_pod_exec,
        pod_name,
        state.namespace,
        command=['/usr/bin/curl', '-s', '-i', url],
        _preload_content=False,
        _request_timeout=state.DEMO_REQUEST_TIMEOUT,
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False)

    resp.run_forever(timeout = state.DEMO_REQUEST_TIMEOUT)
    ret = resp.read_all()
    resp.close()
    logger.debug("%s", ret)
    buf = StringIO(ret)
    headers={'content-type': 'text/html'}
    body=status=reason=None
    for line in buf:
        line=line.strip()
        logger.debug("Line: %s", line)
        if status is None:
            rc = line.split(' ')
            try:
                status = int(rc[1])
                reason = ' '.join(rc[2:])
            except (ValueError, IndexError) as ex:
                logger.info("fault while extracting status and reason: %s", ex)
                pass
            logger.info("status=%s; rc=%s", status, rc)
            continue
        if body is None:
            if not line.strip():
                body=''
                break
            v = line.split(':')
            k = v.pop(0).lower()
            v = ':'.join(v).strip()
            logger.debug("k=%s; v=%s", k, v)
            headers[k] = v.strip()
            continue

    logger.info("headers=%s", headers)
    body = buf.read()

    resp = requests.Response()
    resp.status_code = status or 200
    resp.reason = reason or 'OK'
    body = body.encode('utf-8')
    resp.headers.update(headers)
    resp.headers['content-length'] = len(body)
    resp.raw = BytesIO(body)
    logger.debug("%s", resp.__dict__)
    return resp

def get_url_from_pod(pod_name, url_path):
    pods = get_my_pods()
    pod = list(filter(lambda x: x.pod_name == pod_name, pods.items))
    if not pod:
        raise ValueError("pod not found: %s" % pod_name)
    pod = pod.pop()
    pod_host = pod.ip_address
    pod_port = state.DEMO_PORT
    if state.DEMO_HOST_OVERRIDE:
        logger.info("Overriding host(%s) for testing to: %s", pod_host, state.DEMO_HOST_OVERRIDE)
        pod_host = state.DEMO_HOST_OVERRIDE
    url = "http://%s:%s%s" % (pod_host, pod_port, url_path)
    logger.debug("Crafted url: %s", url)
    if state.DEMO_HOST_OVERRIDE:
        logger.info("Calling pod [%s] via exec for testing: %s", pod_name, url)
        resp = _get_url_from_pod_via_exec(pod_name, url)
    else:
        logger.debug("Calling pod(%s) requests.get(%s)", pod_name, url)
        resp = requests.get(url)
    ret = models.Remote(pod, url, resp.status_code, resp.reason, resp.headers, resp.text, None)

    if resp.headers['content-type'] == 'application/json':
        try:
            ret.body = resp.json()
        except ValueError as ex:
            logger.exception("Unable to parse json")
            ret.fault = str(ex)
    logger.debug("About to return: %s", ret)
    return ret
