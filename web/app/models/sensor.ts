import { Feed } from "./feed";

export interface RuleCategory {
    _id: string;
    name: string;
    rules: Array<SecRule>;
    mandatory: boolean;
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
    reputation?: string[];
    trusted?: string[];
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