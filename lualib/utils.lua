local _M = {}

function _M.parse_list(str)
    local t = {}
    if not str then return t end

    for code in string.gmatch(str, "([^,]+)") do
        code = string.upper((code:gsub("%s+", "")))
        t[code] = true
    end

    return t
end

function _M.get_header(headers, name)
    if not headers then
        return nil
    end

    for k, v in pairs(headers) do
        if string.lower(k) == string.lower(name) then
            return v
        end
    end

    return nil
end

function _M.get_client_ip()
    local ip = ngx.var.http_x_forwarded_for

    if not ip or ip == "" then
        ip = ngx.var.http_x_real_ip
    end

    if not ip or ip == "" then
        ip = ngx.var.remote_addr
    end

    if ip then
        local first_ip = ip:match("([^,%s]+)")
        return first_ip or ip
    end

    return ngx.var.remote_addr
end

function _M.respond(code, _msg)
    local request_id = ngx.var.request_id
    ngx.header["X-Message"] = _msg
    ngx.header["X-Request-Id"] = request_id
    ngx.log(ngx.ERR, "[block] [", request_id, "]: ", _msg)
    return ngx.exit(code)
end

return _M