import json
from typing import Dict, Any, List, Optional, Tuple

INDEX_TEMPLATE_NAME = "nxguard_trn_template"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "index": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "refresh_interval": "5s",
    }
}

DEFAULT_MAPPINGS: Dict[str, Any] = {
    "properties": {
        "logtime": {
            "type": "date",
            "format": "strict_date_optional_time||epoch_millis||yyyy-MM-dd'T'HH:mm:ss.SSSSSSZ||yyyy-MM-dd HH:mm:ss||yyyy-MM-dd'T'HH:mm:ssZ",
        },
        "unique_id": {"type": "keyword"},
        "server_id": {"type": "keyword"},
        "action": {"type": "keyword"},
        "limit_req_status": {"type": "keyword"},
        "geoip_status": {"type": "keyword"},
        "rbl_status": {"type": "keyword"},
        "ipxa": {"type": "keyword"},
        "route_name": {"type": "keyword"},
        "route": {
            "properties": {
                "_id": {"type": "keyword"},
                "name": {"type": "keyword"},
            }
        },
        "score": {"type": "integer"},
        "service": {
            "properties": {
                "_id": {"type": "keyword"},
                "name": {"type": "keyword"},
            }
        },
        "sensor": {
            "properties": {
                "_id": {"type": "keyword"},
                "name": {"type": "keyword"},
            }
        },
        "upstream": {
            "properties": {
                "_id": {"type": "keyword"},
                "name": {"type": "keyword"},
            }
        },
        "user_agent": {
            "properties": {
                "family": {"type": "keyword"},
                "major": {"type": "integer"},
                "minor": {"type": "integer"},
            }
        },
        "source": {
            "properties": {
                "ip": {"type": "ip"},
                "port": {"type": "integer"},
                "geo": {
                    "properties": {
                        "ip": {"type": "ip"},
                        "country": {"type": "keyword"},
                    }
                },
            }
        },
        "destination": {
            "properties": {
                "ip": {"type": "ip"},
                "port": {"type": "integer"},
                "host": {"type": "keyword"},
            }
        },
        "rate_limit": {
            "properties": {
                "action": {"type": "keyword"},
                "zone": {"type": "keyword"},
            }
        },
        "geoip": {
            "properties": {
                "action": {"type": "keyword"},
                "country_code": {"type": "keyword"},
            }
        },
        "reputation": {
            "properties": {
                "action": {"type": "keyword"},
                "score": {"type": "integer"},
            }
        },
        "mtls": {
            "properties": {
                "verified": {"type": "boolean"},
                "fingerprint": {"type": "keyword"},
                "subject_dn": {"type": "keyword"},
                "issuer_dn": {"type": "keyword"},
            }
        },
        "http": {
            "properties": {
                "duration": {"type": "float"},
                "uht": {"type": "float"},
                "urt": {"type": "float"},
                "referer": {"type": "keyword"},
                "request_line": {"type": "text"},
                "request": {
                    "properties": {
                        "method": {"type": "keyword"},
                        "uri": {"type": "keyword"},
                        "bytes": {"type": "long"},
                        "headers": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"},
                                "value": {"type": "keyword"},
                            },
                        },
                    }
                },
                "response": {
                    "properties": {
                        "status_code": {"type": "integer"},
                        "bytes": {"type": "long"},
                        "headers": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"},
                                "value": {"type": "keyword"},
                            },
                        },
                    }
                },
            }
        },
        "audit": {
            "properties": {
                "engine": {"type": "keyword"},
                "connector": {"type": "keyword"},
                "mode": {"type": "keyword"},
                "components": {"type": "keyword"},
                "messages": {
                    "type": "nested",
                    "properties": {
                        "rule_code": {"type": "keyword"},
                        "ruleId": {"type": "keyword"},
                        "message": {"type": "text"},
                        "text": {"type": "text"},
                        "severity": {"type": "keyword"},
                        "data": {"type": "text"},
                        "match": {"type": "text"},
                        "reference": {"type": "text"},
                        "file": {"type": "keyword"},
                        "lineNumber": {"type": "keyword"},
                        "tags": {"type": "keyword"},
                        "ver": {"type": "keyword"},
                        "rev": {"type": "keyword"},
                        "maturity": {"type": "keyword"},
                        "accuracy": {"type": "keyword"},
                    },
                },
            }
        },
    }
}


def build_index_template_payload(
    base_prefix: str, composable: bool = True
) -> Dict[str, Any]:
    """Generates index template payload for composable or legacy OpenSearch/ES APIs."""
    index_patterns = [f"{base_prefix}*", f"{base_prefix}-*"]
    if composable:
        return {
            "index_patterns": index_patterns,
            "template": {
                "settings": DEFAULT_SETTINGS,
                "mappings": DEFAULT_MAPPINGS,
            },
            "priority": 100,
        }
    return {
        "index_patterns": index_patterns,
        "settings": DEFAULT_SETTINGS,
        "mappings": DEFAULT_MAPPINGS,
    }


def build_index_pattern_fields() -> str:
    """Generates field definitions required by OpenSearch Dashboards index patterns."""
    field_defs = [
        {
            "name": "logtime",
            "type": "date",
            "esTypes": ["date"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "_id",
            "type": "string",
            "esTypes": ["_id"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": False,
        },
        {
            "name": "unique_id",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "server_id",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "action",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "limit_req_status",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "geoip_status",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "rbl_status",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "ipxa",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "route_name",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "route.name",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "route._id",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "score",
            "type": "number",
            "esTypes": ["integer"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "service._id",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "service.name",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "sensor._id",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "sensor.name",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "upstream._id",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "upstream.name",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "source.ip",
            "type": "ip",
            "esTypes": ["ip"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "source.port",
            "type": "number",
            "esTypes": ["integer"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "source.geo.country",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "destination.ip",
            "type": "ip",
            "esTypes": ["ip"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "destination.port",
            "type": "number",
            "esTypes": ["integer"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "destination.host",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "rate_limit.action",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "geoip.country_code",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "reputation.action",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "reputation.score",
            "type": "number",
            "esTypes": ["integer"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "http.duration",
            "type": "number",
            "esTypes": ["float"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "http.referer",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "http.request.method",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "http.request.uri",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "http.request.bytes",
            "type": "number",
            "esTypes": ["long"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "http.request.headers.name",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "http.request.headers.value",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "http.response.status_code",
            "type": "number",
            "esTypes": ["integer"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "http.response.bytes",
            "type": "number",
            "esTypes": ["long"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "http.response.headers.name",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "http.response.headers.value",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "user_agent.family",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "audit.messages.rule_code",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
        {
            "name": "audit.messages.message",
            "type": "string",
            "esTypes": ["text"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": False,
            "readFromDocValues": False,
        },
        {
            "name": "audit.messages.severity",
            "type": "string",
            "esTypes": ["keyword"],
            "count": 0,
            "scripted": False,
            "searchable": True,
            "aggregatable": True,
            "readFromDocValues": True,
        },
    ]
    return json.dumps(field_defs)


def build_index_pattern_attributes(title: str) -> Dict[str, Any]:
    """Builds index pattern saved object attributes."""
    return {
        "title": title,
        "timeFieldName": "logtime",
        "fields": build_index_pattern_fields(),
        "fieldFormatMap": json.dumps({"logtime": {"id": "date"}}),
    }


def build_unique_visitors_metric_vis(pattern_id: str) -> Dict[str, Any]:
    """Metric card visualization for Unique Visitors."""
    vis_state = {
        "title": "[Logs] Unique Visitors",
        "type": "metric",
        "params": {
            "metric": {
                "percentageMode": False,
                "useRanges": False,
                "colorSchema": "Green to Red",
                "metricColorMode": "None",
                "style": {
                    "bgFill": "#000",
                    "bgColor": False,
                    "labelColor": False,
                    "subText": "",
                    "fontSize": 48,
                },
            }
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "cardinality",
                "schema": "metric",
                "params": {"field": "source.ip", "customLabel": "Unique Visitors"},
            }
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Unique Visitors",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Contagem de visitantes únicos por IP de origem",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_total_requests_metric_vis(pattern_id: str) -> Dict[str, Any]:
    """Metric card visualization for Total Requests."""
    vis_state = {
        "title": "[Logs] Total Requests",
        "type": "metric",
        "params": {
            "metric": {
                "percentageMode": False,
                "useRanges": False,
                "colorSchema": "Green to Red",
                "metricColorMode": "None",
                "style": {
                    "bgFill": "#000",
                    "bgColor": False,
                    "labelColor": False,
                    "subText": "",
                    "fontSize": 48,
                },
            }
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "count",
                "schema": "metric",
                "params": {"customLabel": "Total Requests"},
            }
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Total Requests",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Volume total de requisições no período",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_total_bytes_metric_vis(pattern_id: str) -> Dict[str, Any]:
    """Metric card visualization for Total Bytes."""
    vis_state = {
        "title": "[Logs] Total Bytes",
        "type": "metric",
        "params": {
            "metric": {
                "percentageMode": False,
                "useRanges": False,
                "colorSchema": "Green to Red",
                "metricColorMode": "None",
                "style": {
                    "bgFill": "#000",
                    "bgColor": False,
                    "labelColor": False,
                    "subText": "",
                    "fontSize": 48,
                },
            }
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "sum",
                "schema": "metric",
                "params": {
                    "field": "http.response.bytes",
                    "customLabel": "Total Bytes Out",
                },
            }
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Total Bytes",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Volume total de bytes transferidos",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_avg_duration_metric_vis(pattern_id: str) -> Dict[str, Any]:
    """Metric card visualization for Average Response Duration."""
    vis_state = {
        "title": "[Logs] Average Duration",
        "type": "metric",
        "params": {
            "metric": {
                "percentageMode": False,
                "useRanges": False,
                "colorSchema": "Green to Red",
                "metricColorMode": "None",
                "style": {
                    "bgFill": "#000",
                    "bgColor": False,
                    "labelColor": False,
                    "subText": "",
                    "fontSize": 48,
                },
            }
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "avg",
                "schema": "metric",
                "params": {
                    "field": "http.duration",
                    "customLabel": "Avg Duration (s)",
                },
            }
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Average Duration",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Tempo médio de resposta (latência) das requisições",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_action_timeline_vis(pattern_id: str) -> Dict[str, Any]:
    """Histogram visualization for transactions over time grouped by action."""
    vis_state = {
        "title": "[Logs] Actions over time",
        "type": "histogram",
        "params": {
            "type": "histogram",
            "grid": {"categoryLines": False},
            "categoryAxes": [
                {
                    "id": "CategoryAxis-1",
                    "type": "category",
                    "position": "bottom",
                    "show": True,
                    "style": {},
                    "scale": {"type": "linear"},
                    "labels": {"show": True, "filter": False, "truncate": 100},
                    "title": {},
                }
            ],
            "valueAxes": [
                {
                    "id": "ValueAxis-1",
                    "name": "LeftAxis-1",
                    "type": "value",
                    "position": "left",
                    "show": True,
                    "style": {},
                    "scale": {"type": "linear", "mode": "normal"},
                    "labels": {
                        "show": True,
                        "rotate": 0,
                        "filter": False,
                        "truncate": 100,
                    },
                    "title": {"text": "Quantidade de Transações"},
                }
            ],
            "seriesParams": [
                {
                    "show": True,
                    "type": "histogram",
                    "mode": "stacked",
                    "data": {"label": "Quantidade", "id": "1"},
                    "valueAxis": "ValueAxis-1",
                    "drawLinesBetweenPoints": True,
                    "showCircles": True,
                }
            ],
            "addTooltip": True,
            "addLegend": True,
            "legendPosition": "right",
            "times": [],
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "count",
                "schema": "metric",
                "params": {},
            },
            {
                "id": "2",
                "enabled": True,
                "type": "date_histogram",
                "schema": "segment",
                "params": {
                    "field": "logtime",
                    "interval": "auto",
                    "min_doc_count": 1,
                },
            },
            {
                "id": "3",
                "enabled": True,
                "type": "terms",
                "schema": "group",
                "params": {
                    "field": "action",
                    "size": 10,
                    "order": "desc",
                    "orderBy": "1",
                },
            },
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Actions over time",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Quantidade de transações por action (ALLOWED, BLOCKED, etc.) ao longo do tempo",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_action_pie_vis(pattern_id: str) -> Dict[str, Any]:
    """Donut visualization for action distribution."""
    vis_state = {
        "title": "[Logs] WAF Actions Distribution",
        "type": "pie",
        "params": {
            "type": "pie",
            "addTooltip": True,
            "addLegend": True,
            "legendPosition": "right",
            "isDonut": True,
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "count",
                "schema": "metric",
                "params": {},
            },
            {
                "id": "2",
                "enabled": True,
                "type": "terms",
                "schema": "segment",
                "params": {
                    "field": "action",
                    "size": 10,
                    "order": "desc",
                    "orderBy": "1",
                },
            },
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] WAF Actions Distribution",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Proporção de ações WAF e Tráfego",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_status_timeline_vis(pattern_id: str) -> Dict[str, Any]:
    """Histogram visualization for HTTP status codes over time."""
    vis_state = {
        "title": "[Logs] Total Requests and Status Codes over time",
        "type": "histogram",
        "params": {
            "type": "histogram",
            "grid": {"categoryLines": False},
            "categoryAxes": [
                {
                    "id": "CategoryAxis-1",
                    "type": "category",
                    "position": "bottom",
                    "show": True,
                    "style": {},
                    "scale": {"type": "linear"},
                    "labels": {"show": True, "filter": False, "truncate": 100},
                    "title": {},
                }
            ],
            "valueAxes": [
                {
                    "id": "ValueAxis-1",
                    "name": "LeftAxis-1",
                    "type": "value",
                    "position": "left",
                    "show": True,
                    "style": {},
                    "scale": {"type": "linear", "mode": "normal"},
                    "labels": {
                        "show": True,
                        "rotate": 0,
                        "filter": False,
                        "truncate": 100,
                    },
                    "title": {"text": "Quantidade"},
                }
            ],
            "seriesParams": [
                {
                    "show": True,
                    "type": "histogram",
                    "mode": "stacked",
                    "data": {"label": "Quantidade", "id": "1"},
                    "valueAxis": "ValueAxis-1",
                    "drawLinesBetweenPoints": True,
                    "showCircles": True,
                }
            ],
            "addTooltip": True,
            "addLegend": True,
            "legendPosition": "right",
            "times": [],
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "count",
                "schema": "metric",
                "params": {},
            },
            {
                "id": "2",
                "enabled": True,
                "type": "date_histogram",
                "schema": "segment",
                "params": {
                    "field": "logtime",
                    "interval": "auto",
                    "min_doc_count": 1,
                },
            },
            {
                "id": "3",
                "enabled": True,
                "type": "terms",
                "schema": "group",
                "params": {
                    "field": "http.response.status_code",
                    "size": 10,
                    "order": "desc",
                    "orderBy": "1",
                },
            },
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Total Requests and Status Codes over time",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Distribuição de códigos de status HTTP ao longo do tempo",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_response_codes_pie_vis(pattern_id: str) -> Dict[str, Any]:
    """Pie/Donut visualization for HTTP response codes distribution."""
    vis_state = {
        "title": "[Logs] Response Codes",
        "type": "pie",
        "params": {
            "type": "pie",
            "addTooltip": True,
            "addLegend": True,
            "legendPosition": "right",
            "isDonut": True,
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "count",
                "schema": "metric",
                "params": {},
            },
            {
                "id": "2",
                "enabled": True,
                "type": "terms",
                "schema": "segment",
                "params": {
                    "field": "http.response.status_code",
                    "size": 10,
                    "order": "desc",
                    "orderBy": "1",
                },
            },
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Response Codes",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Proporção de respostas HTTP por código de status",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_bandwidth_timeline_vis(pattern_id: str) -> Dict[str, Any]:
    """Line visualization for network bandwidth (Bytes In and Out) over time."""
    vis_state = {
        "title": "[Logs] Bandwidth over time",
        "type": "line",
        "params": {
            "type": "line",
            "grid": {"categoryLines": False},
            "categoryAxes": [
                {
                    "id": "CategoryAxis-1",
                    "type": "category",
                    "position": "bottom",
                    "show": True,
                    "style": {},
                    "scale": {"type": "linear"},
                    "labels": {"show": True, "filter": False, "truncate": 100},
                    "title": {},
                }
            ],
            "valueAxes": [
                {
                    "id": "ValueAxis-1",
                    "name": "LeftAxis-1",
                    "type": "value",
                    "position": "left",
                    "show": True,
                    "style": {},
                    "scale": {"type": "linear", "mode": "normal"},
                    "labels": {
                        "show": True,
                        "rotate": 0,
                        "filter": False,
                        "truncate": 100,
                    },
                    "title": {"text": "Bytes"},
                }
            ],
            "seriesParams": [
                {
                    "show": True,
                    "type": "line",
                    "mode": "normal",
                    "data": {"label": "Bytes Out", "id": "1"},
                    "valueAxis": "ValueAxis-1",
                    "drawLinesBetweenPoints": True,
                    "showCircles": True,
                },
                {
                    "show": True,
                    "type": "line",
                    "mode": "normal",
                    "data": {"label": "Bytes In", "id": "2"},
                    "valueAxis": "ValueAxis-1",
                    "drawLinesBetweenPoints": True,
                    "showCircles": True,
                },
            ],
            "addTooltip": True,
            "addLegend": True,
            "legendPosition": "right",
            "times": [],
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "sum",
                "schema": "metric",
                "params": {"field": "http.response.bytes", "customLabel": "Bytes Out"},
            },
            {
                "id": "2",
                "enabled": True,
                "type": "sum",
                "schema": "metric",
                "params": {"field": "http.request.bytes", "customLabel": "Bytes In"},
            },
            {
                "id": "3",
                "enabled": True,
                "type": "date_histogram",
                "schema": "segment",
                "params": {
                    "field": "logtime",
                    "interval": "auto",
                    "min_doc_count": 1,
                },
            },
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Bandwidth over time",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Consumo de banda (Bytes In e Out) na linha do tempo",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_visitors_map_vis(pattern_id: str) -> Dict[str, Any]:
    """Region choropleth map visualization for visitors by country code."""
    vis_state = {
        "title": "[Logs] Visitors Map",
        "type": "region_map",
        "params": {
            "legendPosition": "bottomright",
            "addTooltip": True,
            "colorSchema": "Yellow to Red",
            "selectedLayer": {
                "attribution": '<a href="https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/">Made with Natural Earth</a>',
                "name": "World Countries",
                "format": "geojson",
                "url": "https://vector-maps.opensearch.org/world_countries.geojson",
                "fields": [
                    {"name": "iso2", "description": "Two letter abbreviation"},
                    {"name": "iso3", "description": "Three letter abbreviation"},
                    {"name": "name", "description": "Country name"},
                ],
            },
            "selectedJoinField": {
                "name": "iso2",
                "description": "Two letter abbreviation",
            },
            "isDisplayWarning": True,
            "wms": {"enabled": False},
            "outlineWeight": 1,
            "showAllShapes": True,
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "count",
                "schema": "metric",
                "params": {"customLabel": "Visitors"},
            },
            {
                "id": "2",
                "enabled": True,
                "type": "terms",
                "schema": "segment",
                "params": {
                    "field": "source.geo.country",
                    "size": 100,
                    "order": "desc",
                    "orderBy": "1",
                    "customLabel": "Country",
                },
            },
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Visitors Map",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Mapa mundial de visitantes por país de origem",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_visitors_by_user_agent_vis(pattern_id: str) -> Dict[str, Any]:
    """Donut/Pie visualization for visitors by user agent family."""
    vis_state = {
        "title": "[Logs] Visitors by user agent",
        "type": "pie",
        "params": {
            "type": "pie",
            "addTooltip": True,
            "addLegend": True,
            "legendPosition": "right",
            "isDonut": True,
            "labels": {
                "show": False,
                "values": True,
                "last_level": True,
                "truncate": 100,
            },
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "count",
                "schema": "metric",
                "params": {},
            },
            {
                "id": "2",
                "enabled": True,
                "type": "terms",
                "schema": "segment",
                "params": {
                    "field": "user_agent.family",
                    "size": 10,
                    "order": "desc",
                    "orderBy": "1",
                    "otherBucket": True,
                    "otherBucketLabel": "Other",
                    "missingBucket": False,
                },
            },
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Visitors by user agent",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Distribuição de acessos por família de User Agent / Navegador",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_host_visits_bytes_table_vis(pattern_id: str) -> Dict[str, Any]:
    """Data table visualization for Host, Visits, and Bytes transferred."""
    vis_state = {
        "title": "[Logs] Host, Visits and Bytes Table",
        "type": "table",
        "params": {
            "perPage": 10,
            "showPartialRows": False,
            "showMeticsAtAllLevels": False,
            "sort": {"columnIndex": None, "direction": None},
            "showTotal": True,
            "totalFunc": "sum",
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "count",
                "schema": "metric",
                "params": {"customLabel": "Visits"},
            },
            {
                "id": "2",
                "enabled": True,
                "type": "sum",
                "schema": "metric",
                "params": {
                    "field": "http.response.bytes",
                    "customLabel": "Bytes Out",
                },
            },
            {
                "id": "3",
                "enabled": True,
                "type": "sum",
                "schema": "metric",
                "params": {
                    "field": "http.request.bytes",
                    "customLabel": "Bytes In",
                },
            },
            {
                "id": "4",
                "enabled": True,
                "type": "terms",
                "schema": "bucket",
                "params": {
                    "field": "destination.host",
                    "size": 10,
                    "order": "desc",
                    "orderBy": "1",
                    "customLabel": "Host",
                },
            },
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Host, Visits and Bytes Table",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Tabela de hosts de destino, quantidade de visitas e volume de bytes trafegados",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_top_urls_table_vis(pattern_id: str) -> Dict[str, Any]:
    """Data table visualization for Top URLs / Pages and Average Latency."""
    vis_state = {
        "title": "[Logs] Top URLs and Pages",
        "type": "table",
        "params": {
            "perPage": 10,
            "showPartialRows": False,
            "showMeticsAtAllLevels": False,
            "sort": {"columnIndex": None, "direction": None},
            "showTotal": True,
            "totalFunc": "sum",
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "count",
                "schema": "metric",
                "params": {"customLabel": "Hits"},
            },
            {
                "id": "2",
                "enabled": True,
                "type": "avg",
                "schema": "metric",
                "params": {
                    "field": "http.duration",
                    "customLabel": "Avg Duration (s)",
                },
            },
            {
                "id": "3",
                "enabled": True,
                "type": "terms",
                "schema": "bucket",
                "params": {
                    "field": "http.request.uri",
                    "size": 10,
                    "order": "desc",
                    "orderBy": "1",
                    "customLabel": "URI / Path",
                },
            },
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Top URLs and Pages",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "URLs e caminhos com maior volume de requisições",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_top_services_vis(pattern_id: str) -> Dict[str, Any]:
    """Table visualization for top services and routes."""
    vis_state = {
        "title": "[Logs] Top Services and Routes",
        "type": "table",
        "params": {
            "perPage": 10,
            "showPartialRows": False,
            "showMeticsAtAllLevels": False,
            "sort": {"columnIndex": None, "direction": None},
            "showTotal": True,
            "totalFunc": "sum",
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "count",
                "schema": "metric",
                "params": {},
            },
            {
                "id": "2",
                "enabled": True,
                "type": "terms",
                "schema": "bucket",
                "params": {
                    "field": "service.name",
                    "size": 10,
                    "order": "desc",
                    "orderBy": "1",
                },
            },
            {
                "id": "3",
                "enabled": True,
                "type": "terms",
                "schema": "bucket",
                "params": {
                    "field": "route_name",
                    "size": 10,
                    "order": "desc",
                    "orderBy": "1",
                },
            },
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Top Services and Routes",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Top serviços e rotas com maior volume de tráfego",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def build_top_referrers_table_vis(pattern_id: str) -> Dict[str, Any]:
    """Data table visualization for top HTTP referrers."""
    vis_state = {
        "title": "[Logs] Top Referrers",
        "type": "table",
        "params": {
            "perPage": 10,
            "showPartialRows": False,
            "showMeticsAtAllLevels": False,
            "sort": {"columnIndex": None, "direction": None},
            "showTotal": True,
            "totalFunc": "sum",
        },
        "aggs": [
            {
                "id": "1",
                "enabled": True,
                "type": "count",
                "schema": "metric",
                "params": {"customLabel": "Requests"},
            },
            {
                "id": "2",
                "enabled": True,
                "type": "terms",
                "schema": "bucket",
                "params": {
                    "field": "http.referer",
                    "size": 10,
                    "order": "desc",
                    "orderBy": "1",
                    "customLabel": "HTTP Referer",
                },
            },
        ],
    }
    search_source = {
        "query": {"query": "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    }
    return {
        "title": "[Logs] Top Referrers",
        "visState": json.dumps(vis_state),
        "uiStateJSON": "{}",
        "description": "Principais domínios e páginas de referência (Referer)",
        "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
    }


def get_default_visualizations(
    base_prefix: str,
) -> List[Tuple[str, Dict[str, Any], List[Dict[str, Any]]]]:
    """Returns list of (vis_id, vis_attributes, references) for default Dashboards visualizations."""
    ref = [
        {
            "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
            "type": "index-pattern",
            "id": base_prefix,
        }
    ]
    return [
        (
            f"{base_prefix}_unique_visitors",
            build_unique_visitors_metric_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_total_requests",
            build_total_requests_metric_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_total_bytes",
            build_total_bytes_metric_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_avg_duration",
            build_avg_duration_metric_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_timeline_status",
            build_status_timeline_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_response_codes",
            build_response_codes_pie_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_visitors_map",
            build_visitors_map_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_visitors_by_user_agent",
            build_visitors_by_user_agent_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_bandwidth_timeline",
            build_bandwidth_timeline_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_timeline_action",
            build_action_timeline_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_pie_action",
            build_action_pie_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_host_visits_bytes_table",
            build_host_visits_bytes_table_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_top_urls",
            build_top_urls_table_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_top_services",
            build_top_services_vis(base_prefix),
            ref,
        ),
        (
            f"{base_prefix}_top_referrers",
            build_top_referrers_table_vis(base_prefix),
            ref,
        ),
    ]


def get_default_dashboard(
    base_prefix: str, title: Optional[str] = None
) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    """Returns (dash_id, dash_attributes, references) for the consolidated NxGuard Web Traffic dashboard."""
    dash_id = f"{base_prefix}_dashboard"
    dash_title = title or "NxGuard - [Logs] Web Traffic"

    panels = [
        # Row 1: KPI Metric Cards
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 0, "y": 0, "w": 12, "h": 6, "i": "1"},
            "panelIndex": "1",
            "embeddableConfig": {},
            "panelRefName": "panel_1",
        },
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 12, "y": 0, "w": 12, "h": 6, "i": "2"},
            "panelIndex": "2",
            "embeddableConfig": {},
            "panelRefName": "panel_2",
        },
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 24, "y": 0, "w": 12, "h": 6, "i": "3"},
            "panelIndex": "3",
            "embeddableConfig": {},
            "panelRefName": "panel_3",
        },
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 36, "y": 0, "w": 12, "h": 6, "i": "4"},
            "panelIndex": "4",
            "embeddableConfig": {},
            "panelRefName": "panel_4",
        },
        # Row 2: Status Codes Timeline & Response Codes Pie
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 0, "y": 6, "w": 32, "h": 14, "i": "5"},
            "panelIndex": "5",
            "embeddableConfig": {},
            "panelRefName": "panel_5",
        },
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 32, "y": 6, "w": 16, "h": 14, "i": "6"},
            "panelIndex": "6",
            "embeddableConfig": {},
            "panelRefName": "panel_6",
        },
        # Row 3: Visitors Map & User Agent Distribution
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 0, "y": 20, "w": 28, "h": 15, "i": "7"},
            "panelIndex": "7",
            "embeddableConfig": {},
            "panelRefName": "panel_7",
        },
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 28, "y": 20, "w": 20, "h": 15, "i": "8"},
            "panelIndex": "8",
            "embeddableConfig": {},
            "panelRefName": "panel_8",
        },
        # Row 4: Bandwidth over time & WAF Actions over time
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 0, "y": 35, "w": 24, "h": 14, "i": "9"},
            "panelIndex": "9",
            "embeddableConfig": {},
            "panelRefName": "panel_9",
        },
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 24, "y": 35, "w": 24, "h": 14, "i": "10"},
            "panelIndex": "10",
            "embeddableConfig": {},
            "panelRefName": "panel_10",
        },
        # Row 5: Host Visits & Bytes Table + Top URLs Table
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 0, "y": 49, "w": 24, "h": 14, "i": "11"},
            "panelIndex": "11",
            "embeddableConfig": {},
            "panelRefName": "panel_11",
        },
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 24, "y": 49, "w": 24, "h": 14, "i": "12"},
            "panelIndex": "12",
            "embeddableConfig": {},
            "panelRefName": "panel_12",
        },
        # Row 6: Top Services and Routes + Top Referrers
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 0, "y": 63, "w": 24, "h": 14, "i": "13"},
            "panelIndex": "13",
            "embeddableConfig": {},
            "panelRefName": "panel_13",
        },
        {
            "version": "1.0.0",
            "type": "visualization",
            "gridData": {"x": 24, "y": 63, "w": 24, "h": 14, "i": "14"},
            "panelIndex": "14",
            "embeddableConfig": {},
            "panelRefName": "panel_14",
        },
    ]

    attributes = {
        "title": dash_title,
        "hits": 0,
        "description": "Painel completo de controle de tráfego web e segurança NxGuard ([Logs] Web Traffic)",
        "panelsJSON": json.dumps(panels),
        "optionsJSON": json.dumps({"useMargins": True, "hidePanelTitles": False}),
        "version": 1,
        "timeRestore": True,
        "timeFrom": "now-24h",
        "timeTo": "now",
        "kibanaSavedObjectMeta": {
            "searchSourceJSON": json.dumps(
                {"query": {"query": "", "language": "kuery"}, "filter": []}
            )
        },
    }

    references = [
        {
            "name": "panel_1",
            "type": "visualization",
            "id": f"{base_prefix}_unique_visitors",
        },
        {
            "name": "panel_2",
            "type": "visualization",
            "id": f"{base_prefix}_total_requests",
        },
        {
            "name": "panel_3",
            "type": "visualization",
            "id": f"{base_prefix}_total_bytes",
        },
        {
            "name": "panel_4",
            "type": "visualization",
            "id": f"{base_prefix}_avg_duration",
        },
        {
            "name": "panel_5",
            "type": "visualization",
            "id": f"{base_prefix}_timeline_status",
        },
        {
            "name": "panel_6",
            "type": "visualization",
            "id": f"{base_prefix}_response_codes",
        },
        {
            "name": "panel_7",
            "type": "visualization",
            "id": f"{base_prefix}_visitors_map",
        },
        {
            "name": "panel_8",
            "type": "visualization",
            "id": f"{base_prefix}_visitors_by_user_agent",
        },
        {
            "name": "panel_9",
            "type": "visualization",
            "id": f"{base_prefix}_bandwidth_timeline",
        },
        {
            "name": "panel_10",
            "type": "visualization",
            "id": f"{base_prefix}_timeline_action",
        },
        {
            "name": "panel_11",
            "type": "visualization",
            "id": f"{base_prefix}_host_visits_bytes_table",
        },
        {
            "name": "panel_12",
            "type": "visualization",
            "id": f"{base_prefix}_top_urls",
        },
        {
            "name": "panel_13",
            "type": "visualization",
            "id": f"{base_prefix}_top_services",
        },
        {
            "name": "panel_14",
            "type": "visualization",
            "id": f"{base_prefix}_top_referrers",
        },
    ]

    return dash_id, attributes, references
