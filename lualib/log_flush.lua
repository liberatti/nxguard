local _M = {}
local log_buffer = ngx.shared.log_buffer

local function flush_to_file(path)
    local keys = log_buffer:get_keys(0)
    if #keys == 0 then
        return
    end

    local file, err = io.open(path, "a")
    if not file then
        ngx.log(ngx.ERR, "Failed to open log file: ", err)
        return
    end

    for _, key in ipairs(keys) do
        local json_line = log_buffer:get(key)
        if json_line then
            file:write(json_line .. "\n")
            log_buffer:delete(key)
        end
    end

    file:close()
end

function _M.start(path, interval)
    local function flush_timer(premature)
        if premature then
            return
        end
        flush_to_file(path)
    end

    -- Cria um timer que executa a cada 'interval' segundos
    local ok, err = ngx.timer.every(interval or 2, flush_timer)
    if not ok then
        ngx.log(ngx.ERR, "failed to start log flush timer: ", err)
    end
end

return _M
