local cjson = require "cjson.safe"
local log_buffer = ngx.shared.log_buffer

local map = {
    PASSED = "allowed",
    DELAYED = "delayed",
    REJECTED = "blocked"
}
local raw_status = ngx.var.limit_req_status
local rate_limit_action = map[raw_status] or raw_status or "-"

local log_data = {
    time = ngx.localtime(),
    uniqueid = ngx.var.request_id or "-",
    service = ngx.var.service or "-",
    route = ngx.var.route or "-",
    upstream = {
        name = ngx.var.upstream or "-",
        target = ngx.var.upstream_addr or "-"
    },
    host = ngx.var.http_host or "-",
    remote_addr = ngx.var.remote_addr or "-",
    remote_port = tonumber(ngx.var.remote_port) or 0,
    server_port = tonumber(ngx.var.server_port) or 0,
    request_line = ngx.var.request or "-",
    method = ngx.var.real_method or ngx.var.request_method or "-",
    status = tonumber(ngx.var.status) or 0,
    bytes_in = tonumber(ngx.var.request_length) or 0,
    bytes_out = tonumber(ngx.var.body_bytes_sent) or 0,
    duration = tonumber(ngx.var.request_time) or 0,
    uht = tonumber(ngx.var.upstream_header_time) or 0,
    urt = tonumber(ngx.var.upstream_response_time) or 0,
    referer = ngx.var.http_referer or "-",
    user_agent = ngx.var.http_user_agent or "-",
    sensor = ngx.ctx.sensor,
    rate_limit = {
        action = rate_limit_action
    },
    geoip = {
        ans_number = ngx.ctx.geoip_ans_number or "-",
        ans_description = ngx.ctx.geoip_ans_description or "-",
        country_code = ngx.ctx.geoip_country_code or "-",
        action = ngx.ctx.geoip_action
    },
    reputation = ngx.ctx.reputation,
    mtls = {
        enabled = ngx.var.ssl_client_verify and true or false,
        verified = ngx.var.ssl_client_verify == "SUCCESS"
    }
}

local json_line = cjson.encode(log_data)

local key = ngx.now() .. ":" .. math.random()
local ok, err = log_buffer:set(key, json_line)
if not ok then
    ngx.log(ngx.ERR, "log buffer set failed: ", err)
end

-- (Opcional) enviar para API de monitoramento
-- local http = require "resty.http"
-- local httpc = http.new()
-- httpc:request_uri("http://metrics.nxguard.local/ingest", {
--     method = "POST",
--     body = msg,
--     headers = { ["Content-Type"] = "application/json" },
-- })
