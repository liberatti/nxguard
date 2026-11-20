import copy
import hashlib
import json
import re
from typing import Any, Dict, List, Optional

try:
    from deepdiff import DeepDiff
except ImportError:
    DeepDiff = None

from api.middleware.logging_manager import logger
from api.middleware.socket_manager import emit_event
from api.repository.config_repository import ChangeDao, ConfigBackupDao, ConfigDao
import engine.admin as c_admin
import engine.build as c_builder


def _to_json_compatible(obj: Any) -> Any:
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _to_json_compatible(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_compatible(item) for item in obj]
    return obj


def humanize_deepdiff_path(path_str: str, root_obj: Any) -> str:
    """Converts a DeepDiff root path into a human-readable breadcrumb trail.

    If an array item has a 'name', 'path', or '_id', it uses the identifier
    instead of the numerical index.
    """
    tokens = re.findall(r"\[(?:'([^']*)'|(\d+))\]", path_str)
    parts = []
    curr = root_obj
    for str_key, int_key in tokens:
        if str_key:
            parts.append(str_key)
            if isinstance(curr, dict):
                curr = curr.get(str_key)
            else:
                curr = None
        elif int_key:
            idx = int(int_key)
            name = None
            if isinstance(curr, list) and 0 <= idx < len(curr):
                item = curr[idx]
                if isinstance(item, dict):
                    name = item.get("name") or item.get("path") or item.get("_id")
                curr = item
            else:
                curr = None
            if name:
                parts.append(f"[{name}]")
            else:
                parts.append(f"[{idx}]")
    return " → ".join(parts) if parts else path_str


def compute_deepdiff(
    src: Dict[str, Any], dst: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculates a semantic structural diff using DeepDiff and structures the output."""
    clean_src = _to_json_compatible(copy.deepcopy(src or {}))
    clean_dst = _to_json_compatible(copy.deepcopy(dst or {}))

    if DeepDiff is None:
        return {
            "available": False,
            "raw": {},
            "summary": {"total": 0, "values_changed": 0, "items_added": 0, "items_removed": 0, "type_changes": 0},
            "changes": [],
        }

    try:
        diff = DeepDiff(clean_src, clean_dst, ignore_order=True)
        raw = json.loads(diff.to_json())
    except Exception as ex:
        logger.warning(f"DeepDiff calculation failed: {ex}")
        return {
            "available": False,
            "raw": {},
            "summary": {"total": 0, "values_changed": 0, "items_added": 0, "items_removed": 0, "type_changes": 0},
            "changes": [],
        }

    changes = []
    summary = {
        "total": 0,
        "values_changed": 0,
        "items_added": 0,
        "items_removed": 0,
        "type_changes": 0,
    }

    def _iter_diff_items(category_data):
        if isinstance(category_data, dict):
            return category_data.items()
        elif isinstance(category_data, (list, set, tuple)):
            return [(item, None) if not isinstance(item, tuple) else item for item in category_data]
        return []

    # 1. Values changed
    for path, change in _iter_diff_items(raw.get("values_changed")):
        summary["values_changed"] += 1
        old_val = change.get("old_value") if isinstance(change, dict) else None
        new_val = change.get("new_value") if isinstance(change, dict) else None
        changes.append({
            "type": "changed",
            "category": "values_changed",
            "path": str(path),
            "human_path": humanize_deepdiff_path(str(path), clean_src) or humanize_deepdiff_path(str(path), clean_dst),
            "old_value": old_val,
            "new_value": new_val,
        })

    # 2. Dictionary items added
    for path, val in _iter_diff_items(raw.get("dictionary_item_added")):
        summary["items_added"] += 1
        changes.append({
            "type": "added",
            "category": "dictionary_item_added",
            "path": str(path),
            "human_path": humanize_deepdiff_path(str(path), clean_dst),
            "new_value": val,
        })

    # 3. Dictionary items removed
    for path, val in _iter_diff_items(raw.get("dictionary_item_removed")):
        summary["items_removed"] += 1
        changes.append({
            "type": "removed",
            "category": "dictionary_item_removed",
            "path": str(path),
            "human_path": humanize_deepdiff_path(str(path), clean_src),
            "old_value": val,
        })

    # 4. Iterable items added
    for path, val in _iter_diff_items(raw.get("iterable_item_added")):
        summary["items_added"] += 1
        changes.append({
            "type": "added",
            "category": "iterable_item_added",
            "path": str(path),
            "human_path": humanize_deepdiff_path(str(path), clean_dst),
            "new_value": val,
        })

    # 5. Iterable items removed
    for path, val in _iter_diff_items(raw.get("iterable_item_removed")):
        summary["items_removed"] += 1
        changes.append({
            "type": "removed",
            "category": "iterable_item_removed",
            "path": str(path),
            "human_path": humanize_deepdiff_path(str(path), clean_src),
            "old_value": val,
        })

    # 6. Type changes
    for path, change in _iter_diff_items(raw.get("type_changes")):
        summary["type_changes"] += 1
        old_val = change.get("old_value") if isinstance(change, dict) else None
        new_val = change.get("new_value") if isinstance(change, dict) else None
        changes.append({
            "type": "changed",
            "category": "type_changes",
            "path": str(path),
            "human_path": humanize_deepdiff_path(str(path), clean_src),
            "old_value": old_val,
            "new_value": new_val,
        })

    summary["total"] = len(changes)

    return {
        "available": True,
        "raw": raw,
        "summary": summary,
        "changes": changes,
    }


def rfc8785_canonicalize(data: Any) -> str:
    """Serializes data to a deterministic JSON string according to RFC 8785 (JCS).

    - Keys are sorted strictly by UTF-16 code units.
    - Insignificant whitespace is eliminated (separators=(',', ':')).
    - Strings are encoded with minimal required escaping.
    - Numbers and booleans follow IEEE 754 / standard JSON canonical forms.
    """
    if data is None:
        return "null"
    elif isinstance(data, bool):
        return "true" if data else "false"
    elif isinstance(data, int):
        return str(data)
    elif isinstance(data, float):
        if data.is_integer():
            return str(int(data))
        return json.dumps(data)
    elif isinstance(data, str):
        return json.dumps(data, ensure_ascii=False)
    elif isinstance(data, (list, tuple)):
        return "[" + ",".join(rfc8785_canonicalize(item) for item in data) + "]"
    elif isinstance(data, dict):
        sorted_keys = sorted(data.keys(), key=lambda k: k.encode("utf-16be"))
        return (
            "{"
            + ",".join(
                json.dumps(k, ensure_ascii=False) + ":" + rfc8785_canonicalize(data[k])
                for k in sorted_keys
            )
            + "}"
        )
    else:
        return json.dumps(str(data), ensure_ascii=False)


def compute_jcs_hash(data: Any) -> str:
    """Computes the SHA-256 hexadecimal digest of an RFC 8785 canonical JSON payload."""
    canonical_str = rfc8785_canonicalize(data)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def clean_data_for_restore(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes configuration data from backup so that it can be safely re-inserted

    into DuckDB without transient runtime or rendering artifacts.
    """
    data = copy.deepcopy(raw_data or {})

    SERVICE_COLS = {
        "_id", "certificate_id", "name", "body_limit", "timeout", "active",
        "buffer", "rate_limit_per_sec", "bindings", "headers", "compression_types",
        "sans", "ssl_protocols", "ssl_client_ca", "ssl_client_auth", "routes"
    }
    UPSTREAM_COLS = {
        "_id", "name", "description", "retry", "retry_timeout", "conn_timeout",
        "protocol", "script_path", "type", "targets", "persist", "index", "content"
    }
    SENSOR_COLS = {
        "_id", "name", "description", "categories", "exclusions", "security", "inspection"
    }
    CERTIFICATE_COLS = {
        "_id", "name", "subjects", "chain", "certificate", "private_key",
        "ssl_client_ca", "not_before", "not_after", "status", "provider", "force_renew"
    }
    ROUTE_COLS = {
        "_id", "service_id", "upstream_id", "sensor_id", "monitor_only",
        "name", "type", "paths", "cache_methods", "allowed_methods",
        "allowed_content_type", "redirect"
    }

    if "upstreams" in data and isinstance(data["upstreams"], list):
        cleaned_upstreams = []
        for u in data["upstreams"]:
            if isinstance(u, dict):
                u_copy = {k: v for k, v in u.items() if k in UPSTREAM_COLS}
                if isinstance(u_copy.get("persist"), dict):
                    p_copy = dict(u_copy["persist"])
                    p_copy.pop("cookie_var", None)
                    u_copy["persist"] = p_copy
                if isinstance(u_copy.get("targets"), list):
                    cleaned_targets = []
                    for t in u_copy["targets"]:
                        if isinstance(t, dict):
                            t_copy = dict(t)
                            t_copy.pop("healthy", None)
                            cleaned_targets.append(t_copy)
                        else:
                            cleaned_targets.append(t)
                    u_copy["targets"] = cleaned_targets
                cleaned_upstreams.append(u_copy)
            else:
                cleaned_upstreams.append(u)
        data["upstreams"] = cleaned_upstreams

    if "sensors" in data and isinstance(data["sensors"], list):
        data["sensors"] = [
            {k: v for k, v in s.items() if k in SENSOR_COLS}
            if isinstance(s, dict) else s
            for s in data["sensors"]
        ]

    if "certificates" in data and isinstance(data["certificates"], list):
        data["certificates"] = [
            {k: v for k, v in c.items() if k in CERTIFICATE_COLS}
            if isinstance(c, dict) else c
            for c in data["certificates"]
        ]

    if "services" in data and isinstance(data["services"], list):
        cleaned_services = []
        for s in data["services"]:
            if isinstance(s, dict):
                cert_val = s.get("certificate")
                cert_id = s.get("certificate_id")
                if not cert_id and isinstance(cert_val, dict):
                    cert_id = cert_val.get("_id")
                    if not cert_id and "name" in cert_val:
                        cert_name = cert_val["name"]
                        for c in data.get("certificates", []):
                            if isinstance(c, dict) and c.get("name") == cert_name:
                                cert_id = c.get("_id")
                                break

                s_copy = {k: v for k, v in s.items() if k in SERVICE_COLS}
                if cert_id:
                    s_copy["certificate_id"] = cert_id

                if "routes" in s_copy and isinstance(s_copy["routes"], list):
                    cleaned_routes = []
                    for r in s_copy["routes"]:
                        if isinstance(r, dict):
                            ups_val = r.get("upstream")
                            ups_id = r.get("upstream_id")
                            if not ups_id and isinstance(ups_val, dict):
                                ups_id = ups_val.get("_id")
                                if not ups_id and "name" in ups_val:
                                    ups_name = ups_val["name"]
                                    for u in data.get("upstreams", []):
                                        if isinstance(u, dict) and u.get("name") == ups_name:
                                            ups_id = u.get("_id")
                                            break

                            sns_val = r.get("sensor")
                            sns_id = r.get("sensor_id")
                            if not sns_id and isinstance(sns_val, dict):
                                sns_id = sns_val.get("_id")
                                if not sns_id and "name" in sns_val:
                                    sns_name = sns_val["name"]
                                    for sn in data.get("sensors", []):
                                        if isinstance(sn, dict) and sn.get("name") == sns_name:
                                            sns_id = sn.get("_id")
                                            break

                            r_copy = {k: v for k, v in r.items() if k in ROUTE_COLS}
                            if ups_id is not None:
                                r_copy["upstream_id"] = ups_id
                            if sns_id is not None:
                                r_copy["sensor_id"] = sns_id
                            cleaned_routes.append(r_copy)
                        else:
                            cleaned_routes.append(r)
                    s_copy["routes"] = cleaned_routes
                cleaned_services.append(s_copy)
            else:
                cleaned_services.append(s)
        data["services"] = cleaned_services

    return data


class ConfigAuditService:
    """Service orchestrating configuration audit history, integrity checksums,

    and DeepDiff semantic diff calculations.
    """

    rfc8785_canonicalize = staticmethod(rfc8785_canonicalize)
    compute_jcs_hash = staticmethod(compute_jcs_hash)
    compute_deepdiff = staticmethod(compute_deepdiff)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_history(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Returns paginated configuration history with RFC 8785 checksums and DeepDiff summaries."""
        page = max(1, int(page))
        per_page = max(1, min(100, int(per_page)))
        offset = (page - 1) * per_page

        with ConfigBackupDao() as backup_dao, ConfigDao() as config_dao:
            active_scn = config_dao.get_active_scn()
            total = backup_dao.count_all()
            backups = backup_dao.get_history(limit=per_page, offset=offset)

            items = []
            for b in backups:
                data = b.get("data")
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except Exception:
                        data = {}
                elif not isinstance(data, dict):
                    data = {}

                jcs_hash = compute_jcs_hash(data)
                services_count = len(data.get("services") or [])
                upstreams_count = len(data.get("upstreams") or [])
                sensors_count = len(data.get("sensors") or [])
                certificates_count = len(data.get("certificates") or [])

                predecessor = backup_dao.get_predecessor(b.get("_id", 0))
                deepdiff_summary = {"total": 0, "values_changed": 0, "items_added": 0, "items_removed": 0, "type_changes": 0}
                if predecessor and predecessor.get("data"):
                    prev_data = predecessor["data"]
                    if isinstance(prev_data, str):
                        try:
                            prev_data = json.loads(prev_data)
                        except Exception:
                            prev_data = {}
                    deepdiff_data = compute_deepdiff(prev_data, data)
                    deepdiff_summary = deepdiff_data.get("summary", deepdiff_summary)

                created_at = b.get("created_at")
                if hasattr(created_at, "isoformat"):
                    created_at_str = created_at.isoformat()
                else:
                    created_at_str = str(created_at) if created_at else None

                items.append(
                    {
                        "_id": b.get("_id"),
                        "scn": b.get("scn"),
                        "created_at": created_at_str,
                        "is_active": (b.get("scn") == active_scn),
                        "jcs_hash": jcs_hash,
                        "counts": {
                            "services": services_count,
                            "upstreams": upstreams_count,
                            "sensors": sensors_count,
                            "certificates": certificates_count,
                        },
                        "deepdiff_summary": deepdiff_summary,
                    }
                )

            return {
                "total": total,
                "page": page,
                "per_page": per_page,
                "active_scn": active_scn,
                "data": items,
            }

    def get_version_diff(
        self, scn: str, base_scn: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Calculates DeepDiff semantic representations between two SCN versions."""
        with ConfigBackupDao() as backup_dao:
            target_record = backup_dao.get_by_scn(scn)
            if not target_record:
                return None

            target_data = target_record.get("data")
            if isinstance(target_data, str):
                target_data = json.loads(target_data)
            elif not isinstance(target_data, dict):
                target_data = {}

            if base_scn:
                base_record = backup_dao.get_by_scn(base_scn)
            else:
                base_record = backup_dao.get_predecessor(target_record.get("_id", 0))

            if base_record:
                base_data = base_record.get("data")
                if isinstance(base_data, str):
                    base_data = json.loads(base_data)
                elif not isinstance(base_data, dict):
                    base_data = {}
            else:
                base_data = {}

            target_canonical = rfc8785_canonicalize(target_data)
            base_canonical = rfc8785_canonicalize(base_data)

            target_hash = hashlib.sha256(target_canonical.encode("utf-8")).hexdigest()
            base_hash = hashlib.sha256(base_canonical.encode("utf-8")).hexdigest()

            # Compute Semantic DeepDiff
            deepdiff_res = compute_deepdiff(base_data, target_data)

            return {
                "target": {
                    "_id": target_record.get("_id"),
                    "scn": target_record.get("scn"),
                    "created_at": (
                        target_record["created_at"].isoformat()
                        if hasattr(target_record.get("created_at"), "isoformat")
                        else str(target_record.get("created_at"))
                    ),
                    "jcs_hash": target_hash,
                    "raw_data": target_data,
                },
                "base": {
                    "_id": base_record.get("_id") if base_record else None,
                    "scn": base_record.get("scn") if base_record else None,
                    "created_at": (
                        base_record["created_at"].isoformat()
                        if base_record and hasattr(base_record.get("created_at"), "isoformat")
                        else str(base_record.get("created_at")) if base_record else None
                    ),
                    "jcs_hash": base_hash if base_record else None,
                    "raw_data": base_data,
                },
                "deepdiff": deepdiff_res,
            }

    def restore_version(self, scn: str) -> Dict[str, Any]:
        """Restores a historical configuration version, validates and applies it."""
        with ConfigBackupDao() as backup_dao:
            backup = backup_dao.get_by_scn(scn)
            if not backup or "data" not in backup:
                raise ValueError(f"Configuration version {scn} not found")

            data = backup["data"]
            if isinstance(data, str):
                data = json.loads(data)

        # Restore configuration in DuckDB repository tables
        sanitized_data = clean_data_for_restore(data)
        c_builder.init_from_data(data=sanitized_data)

        # Validate restored configuration
        conf = c_builder.get_config()
        val = c_admin.validate(conf)
        if not val or val.get("status") != "ok":
            msg = val.get("message") if val else "Validation failed"
            raise RuntimeError(f"Configuration validation failed: {msg}")

        # Apply restored configuration
        cst = c_admin.apply(val["scn"])
        if not cst or cst.get("status") != "ok":
            msg = cst.get("message") if cst else "Apply failed"
            raise RuntimeError(f"Failed to apply restored configuration: {msg}")

        with ChangeDao() as change_dao:
            change_dao.delete_all()

        emit_event("tracking_aply")
        emit_event("tracking_evt")

        logger.info(f"Configuration successfully restored to version SCN {scn} (new active SCN: {val['scn']})")
        return {
            "status": "ok",
            "restored_scn": scn,
            "active_scn": val["scn"],
            "message": "Configuration successfully restored and applied",
        }

    def consolidate_and_prune_history(
        self, retain_versions: Optional[int] = None
    ) -> Dict[str, Any]:
        """Prunes historical configuration versions exceeding the retention limit while consolidating a baseline.

        - Preserves the active running configuration SCN.
        - Retains the most recent `retain_versions` (default 50).
        - Identifies the predecessor of the oldest retained version and preserves it as the consolidated baseline.
        - Deletes all versions older than the consolidated baseline.
        """
        with ConfigDao() as config_dao, ConfigBackupDao() as backup_dao:
            active_cfg = config_dao.get_active() or {}
            active_scn = active_cfg.get("active_scn")
            if retain_versions is None or retain_versions <= 0:
                audit_cfg = active_cfg.get("audit") or {}
                if isinstance(audit_cfg, dict):
                    retain_versions = audit_cfg.get("retain_versions", 50)
                else:
                    retain_versions = 50
            retain_versions = max(1, int(retain_versions))

            all_backups = backup_dao.get_history(limit=10000, offset=0)
            total_records = len(all_backups)

            if total_records <= retain_versions:
                return {
                    "status": "ok",
                    "total": total_records,
                    "retained": total_records,
                    "pruned": 0,
                    "baseline_scn": None,
                    "message": f"Total versions ({total_records}) does not exceed retention limit ({retain_versions}). No pruning needed.",
                }

            retained_records = all_backups[:retain_versions]
            retained_ids = {r["_id"] for r in retained_records if "_id" in r}

            oldest_retained = retained_records[-1]
            oldest_retained_id = oldest_retained.get("_id", 0)

            baseline_record = backup_dao.get_predecessor(oldest_retained_id)
            baseline_id = baseline_record.get("_id") if baseline_record else None
            baseline_scn = baseline_record.get("scn") if baseline_record else None

            active_record_id = None
            if active_scn:
                for b in all_backups:
                    if b.get("scn") == active_scn:
                        active_record_id = b.get("_id")
                        break

            keep_ids = set(retained_ids)
            if baseline_id is not None:
                keep_ids.add(baseline_id)
            if active_record_id is not None:
                keep_ids.add(active_record_id)

            ids_to_prune = [
                b["_id"]
                for b in all_backups
                if b.get("_id") is not None and b["_id"] not in keep_ids
            ]

            pruned_count = 0
            if ids_to_prune:
                pruned_count = backup_dao.delete_versions_by_ids(ids_to_prune)

            logger.info(
                f"Configuration history consolidation & prune complete: "
                f"retained={len(keep_ids)}, pruned={pruned_count}, "
                f"baseline_scn={baseline_scn} (ID={baseline_id})"
            )

            return {
                "status": "ok",
                "total_before": total_records,
                "retained": len(keep_ids),
                "pruned": pruned_count,
                "baseline_scn": baseline_scn,
                "message": f"Successfully pruned {pruned_count} old versions. Baseline consolidated at SCN {baseline_scn}.",
            }
