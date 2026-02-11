local cjson = require "cjson.safe"

ngx.header["Content-Type"] = "application/json; charset=utf-8"
ngx.header["Cache-Control"] = "no-cache, no-store, must-revalidate"
ngx.header["Pragma"] = "no-cache"

local status = ngx.status or 500
local descriptions = {
    [400] = "Bad request",
    [401] = "Unauthorized",
    [403] = "Access forbidden",
    [404] = "Resource not found",
    [429] = "RateLimit Triggered",
    [500] = "Internal server error",
    [502] = "Bad gateway",
    [503] = "Service unavailable",
    [504] = "Gateway timeout"
}

local description = descriptions[status] or "Unexpected error"

local resposta = {
    remote_addr = ngx.var.remote_addr,
    request_id = ngx.var.request_id,
    status = status,
    description = description,
    request = ngx.var.request_uri or ngx.var.request
}

local json = cjson.encode(resposta) or '{"error":"encoding failed"}'
ngx.say(json)