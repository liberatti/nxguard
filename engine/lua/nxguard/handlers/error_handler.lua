local cjson = require "cjson"

local errors = {
    [ngx.HTTP_BAD_REQUEST] = "Bad Request",
    [ngx.HTTP_UNAUTHORIZED] = "Unauthorized",
    [ngx.HTTP_FORBIDDEN] = "Forbidden",
    [ngx.HTTP_NOT_FOUND] = "Not Found",
    [ngx.HTTP_NOT_ALLOWED] = "Method Not Allowed",
    [ngx.HTTP_INTERNAL_SERVER_ERROR] = "Internal Server Error",
    [ngx.HTTP_BAD_GATEWAY] = "Bad Gateway",
    [ngx.HTTP_SERVICE_UNAVAILABLE] = "Service Unavailable",
    [ngx.HTTP_GATEWAY_TIMEOUT] = "Gateway Timeout"
}

local status = ngx.status
local default_error = errors[status] or "Error"
local message = ngx.header["X-Message"] or default_error

ngx.header["X-Message"] = nil
local request_id = ngx.var.request_id

local upstream_status = ngx.var.upstream_status
local is_upstream = (upstream_status ~= nil and upstream_status ~= "" and upstream_status ~= "-")

local blocked_by = nil
if status == 403 then
    if is_upstream then
        blocked_by = "upstream"
    elseif (ngx.ctx.sensor and ngx.ctx.sensor.action == "blocked")
        or ngx.ctx.geoip_action == "blocked"
        or ngx.ctx.reputation_action == "blocked"
        or ngx.ctx.blocked_by == "sensor" then
        blocked_by = "sensor"
    else
        blocked_by = "waf"
    end
end

ngx.status = status
ngx.header.content_type = "application/json"

local payload = {
    status = status,
    error = default_error,
    message = message,
    request_id = request_id
}
if blocked_by then
    payload.blocked_by = blocked_by
end

ngx.say(cjson.encode(payload))
return ngx.exit(ngx.HTTP_OK)
