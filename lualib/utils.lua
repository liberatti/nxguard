local cjson = require "cjson.safe"

local _M = {}

function _M.get_client_ip()
    local ip = ngx.var.http_x_forwarded_for

    if not ip or ip == "" then
        ip = ngx.var.http_x_real_ip
    end

    if not ip or ip == "" then
        ip = ngx.var.remote_addr
    end

    if ip then
        -- pega apenas o primeiro IP da lista
        local first_ip = ip:match("([^,%s]+)")
        return first_ip or ip
    end

    return ngx.var.remote_addr
end

function _M.respond(code, _msg)
    ngx.ctx.response_blocked = true
    ngx.ctx.response_message = _msg

    ngx.status = code
    ngx.header["Content-Type"] = "application/json; charset=utf-8"

    local body = {
        error = "Access forbidden",
        message = _msg
    }

    ngx.say(cjson.encode(body))
    return ngx.exit(code)
end

return _M
