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

ngx.status = status
ngx.header["X-Request-Id"] = request_id
ngx.header.content_type = "application/json"
ngx.say(cjson.encode({
    status = status,
    error = default_error,
    message = message,
    request_id = request_id
}))
return ngx.exit(ngx.HTTP_OK)
