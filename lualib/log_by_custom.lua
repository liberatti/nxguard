local cjson = require "cjson.safe"
local log_buffer = ngx.shared.log_buffer
local log_data = {
    time = ngx.localtime(),
    service = ngx.var.service or "-",
    route = ngx.var.route or "-",
    upstream = ngx.var.upstream or "-",
    target_addr = ngx.var.upstream_addr or "-",
    sensor = ngx.var.sensor or "-",
    uniqueid = ngx.var.request_id or "-",
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
    limit_req_status = ngx.var.limit_req_status or "-",
    geoip_status = ngx.var.geoip_status or "-",
    rbl_status = ngx.var.rbl_status or "-"
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
