export interface RuleCategory {
    _id?: string;
    name: string;
    phase?: number;
    file?: string;
    scope?: string;
    seq?: number;
    system?: boolean;
    provider: string;
    rules?: Array<SecRule>;
    exclusions?: number[];
    mandatory?: boolean;
}

export interface SecRule {
    schema_type: string;
    code: number;
    msg: string;
    action: string;
    active: boolean;
    phase: string;
    severity?: string;
    tags?: string[];
    logging: string;
    auditLog: string;
    comment: string;
    condition: string;
    scope: string;
}

export interface SensorSecurity {
    geo_codes?: string[];
    geo_codes_count?: number;
    reputation?: string[];
    reputation_count?: number;
    trusted?: string[];
    trusted_count?: number;
}

export interface SensorScore {
    inbound?: number;
    outbound?: number;
}

export interface SensorVariables {
    allowed_http_versions?: string[] | string;
    max_file_size?: number;
    restricted_extensions?: string[] | string;
    max_num_args?: number;
    arg_name_length?: number;
    arg_length?: number;
}

export interface SensorInspection {
    score?: SensorScore;
    level?: number;
    variables?: SensorVariables;
}

export interface Sensor {
    _id?: any;
    name: string;
    description?: string;
    categories?: string[];
    categories_count?: number;
    exclusions?: number[];
    security?: SensorSecurity;
    inspection?: SensorInspection;
}

export interface SecRuleCustom {
    code: number;
    active: boolean;
    logging: boolean;
    auditLog: boolean;
    action: string;
}