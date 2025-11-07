local cjson = require "cjson"

local function get_client_ip()
    local ip = ngx.var.http_x_forwarded_for
    if ip == nil or ip == "" then
        ip = ngx.var.http_x_real_ip
    end
    if ip == nil or ip == "" then
        ip = ngx.var.remote_addr
    end
    if ip then
        local first_ip = string.match(ip, "([^,]+)")
        return first_ip or ip
    end
    return ngx.var.remote_addr
end

local function respond(code, _msg)
    ngx.status = code
    ngx.say(cjson.encode({ error = "Access forbidden", message = _msg }))
    -- ngx.log(ngx.ERR, _msg)
end