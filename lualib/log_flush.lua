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

    -- Cria um timer que executa a cada 'interval' segundos
    local ok, err = ngx.timer.every(interval or 2, flush_timer)
    if not ok then
        ngx.log(ngx.ERR, "failed to start log flush timer: ", err)
    end
end

return _M
