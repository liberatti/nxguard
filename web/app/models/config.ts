
export interface ConfigArchive {
    enabled: boolean;
    archive_after: number;
    type: string;
    url: string;
    username: string;
    password: string;
}

export interface ConfigPurge {
    enabled: boolean;
    purge_after: number;
}

export interface ConfigIpxa {
    url?: string;
    key?: string;
}

export interface Config {
    _id: string;
    ca_certificate: string;
    ca_private: string;
    acme_directory_url: string;
    dns_resolver?: string;
    archive: ConfigArchive;
    purge: ConfigPurge;
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
