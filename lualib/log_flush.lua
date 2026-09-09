local _M = {}
local log_buffer = ngx.shared.log_buffer

local function flush_to_file(base_path)
    local keys = log_buffer:get_keys(0)
    if not keys or #keys == 0 then
        return
    end

    local file_handles = {}

    for _, key in ipairs(keys) do
        local json_line = log_buffer:get(key)
        if json_line then
            local service = key:match("^([^:]+):") or "default"
            local file = file_handles[service]
            if not file then
                local log_path = string.format("%s/logs/access-%s.log", base_path, service)
                local err
                file, err = io.open(log_path, "a")
                if file then
                    file_handles[service] = file
                else
                    ngx.log(ngx.ERR, "Failed to open log file: ", log_path, " error: ", err)
                end
            end

            if file then
                file:write(json_line .. "\n")
                log_buffer:delete(key)
            end
        end
    end

    for _, f in pairs(file_handles) do
        f:close()
    end
end

function _M.start(base_path, interval)
    local function flush_timer(premature)
        if premature then
            return
        end
        flush_to_file(base_path)
    end

    local ok, err = ngx.timer.every(interval or 2, flush_timer)
    if not ok then
        ngx.log(ngx.ERR, "failed to start log flush timer: ", err)
    end
end

local function flush_to_remote(opts)
    if not opts then
        return
    end

    local keys = log_buffer:get_keys(0)
    if not keys or #keys == 0 then
        return
    end

    local options = type(opts) == "table" and opts or { url = tostring(opts) }
    local url = options.url
    if not url or url == "" then
        ngx.log(ngx.WARN, "flush_to_remote: url is not configured")
        return
    end

    local http_ok, http = pcall(require, "resty.http")
    if not http_ok then
        ngx.log(ngx.ERR, "resty.http module not available: ", http)
        return
    end

    local index_name = options.index or "nxguard_trn"
    local bulk_lines = {}
    local keys_to_delete = {}

    for _, key in ipairs(keys) do
        local json_line = log_buffer:get(key)
        if json_line and json_line ~= "" then
            table.insert(bulk_lines, string.format('{"index":{"_index":"%s"}}\n%s\n', index_name, json_line))
            table.insert(keys_to_delete, key)
        end
    end

    if #bulk_lines == 0 then
        return
    end

    local endpoint = url
    if not endpoint:find("/_bulk$") then
        if endpoint:sub(-1) == "/" then
            endpoint = endpoint .. "_bulk"
        else
            endpoint = endpoint .. "/_bulk"
        end
    end

    local headers = {
        ["Content-Type"] = "application/x-ndjson",
    }
    if options.username and options.username ~= "" and options.password and options.password ~= "" then
        headers["Authorization"] = "Basic " .. ngx.encode_base64(options.username .. ":" .. options.password)
    end

    local httpc = http.new()
    httpc:set_timeout(options.timeout or 5000)

    local payload = table.concat(bulk_lines, "")
    local res, err = httpc:request_uri(endpoint, {
        method = "POST",
        body = payload,
        headers = headers,
        ssl_verify = false,
    })

    if not res then
        ngx.log(ngx.ERR, "Failed to send logs to remote OpenSearch: ", err)
        return
    end

    if res.status >= 200 and res.status < 300 then
        for _, key in ipairs(keys_to_delete) do
            log_buffer:delete(key)
        end
    else
        ngx.log(ngx.ERR, "Remote OpenSearch flush returned status ", res.status, ": ", res.body or "")
    end
end

function _M.start_remote(opts, interval)
    local function flush_remote_timer(premature)
        if premature then
            return
        end
        flush_to_remote(opts)
    end

    local ok, err = ngx.timer.every(interval or 2, flush_remote_timer)
    if not ok then
        ngx.log(ngx.ERR, "failed to start remote log flush timer: ", err)
    end
end

return _M
