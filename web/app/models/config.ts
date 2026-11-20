
export interface ConfigLogging {
    mode: 'local' | 'elasticsearch' | string;
    type?: string;
    audit_log_parts?: string;
    index_url?: string;
    index_username?: string;
    index_password?: string;
    dashboard_url?: string;
    dashboard_username?: string;
    dashboard_password?: string;
    url?: string;
    username?: string;
    password?: string;
}

export interface ConfigPurge {
    enabled: boolean;
    purge_after: number;
}

export interface ConfigAuditSettings {
    retain_versions: number;
}

export interface ConfigIpxa {
    url?: string;
    key?: string;
}

export interface IpxaStats {
    cache_size: number;
    feeds_bypass: number;
    feeds_reputation: number;
    geoip_entries: number;
    rbl_size: number;
}

export interface Config {
    _id: string;
    ca_certificate: string;
    ca_private: string;
    acme_directory_url: string;
    dns_resolver?: string;
    logging?: ConfigLogging;
    purge: ConfigPurge;
    audit?: ConfigAuditSettings;
    ipxa?: ConfigIpxa;
}
export interface EngineNode {
    _id: string;
    role: string;
    scn: string;
    status: string; // ACTIVE, ERROR
    last_check: string;
    version: string;
    net_recv: number;
    net_send: number;
}
export interface Health {
    nodes: EngineNode[];
}

export interface ConfigAuditHistoryItem {
    _id: number;
    scn: string;
    created_at: string;
    is_active: boolean;
    jcs_hash: string;
    counts: {
        services: number;
        upstreams: number;
        sensors: number;
        certificates: number;
    };
    patch_summary: {
        total: number;
        add: number;
        remove: number;
        replace: number;
        move?: number;
        copy?: number;
        affected_paths: string[];
    };
    deepdiff_summary?: DeepDiffSummary;
}

export interface DeepDiffChange {
    type: 'changed' | 'added' | 'removed';
    category: string;
    path: string;
    human_path: string;
    old_value?: any;
    new_value?: any;
}

export interface DeepDiffSummary {
    total: number;
    values_changed: number;
    items_added: number;
    items_removed: number;
    type_changes?: number;
}

export interface DeepDiffResult {
    available: boolean;
    raw: Record<string, any>;
    summary: DeepDiffSummary;
    changes: DeepDiffChange[];
}

export interface JsonPatchOperation {
    op: 'add' | 'remove' | 'replace' | 'move' | 'copy' | 'test' | string;
    path: string;
    value?: any;
    from?: string;
    from_value?: any;
}

export interface ConfigVersionDiff {
    target: {
        _id: number;
        scn: string;
        created_at: string;
        jcs_hash: string;
        canonical_json: string;
        raw_data: any;
    };
    base: {
        _id?: number;
        scn?: string;
        created_at?: string;
        jcs_hash?: string;
        canonical_json?: string;
        raw_data?: any;
    };
    rfc6902_patch: JsonPatchOperation[];
    patch_summary: {
        total: number;
        add: number;
        remove: number;
        replace: number;
        affected_paths: string[];
    };
    deepdiff?: DeepDiffResult;
}
