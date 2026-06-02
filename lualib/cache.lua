local _M = {}
local cjson = require("cjson")

function _M.new(maxsize, ttl)
    local self = {}
    local CACHE_TTL = ttl or 30
    local dict = ngx.shared.ip_cache

    if not dict then
        ngx.log(ngx.ERR, "lua_shared_dict 'ip_cache' not found in nginx.conf")
    end

    function self.get(key)
        if not dict then return nil end
        local val = dict:get(key)
        if val then
            local ok, data = pcall(cjson.decode, val)
            if ok then return data end
        end
        return nil
    end

    function self.set(key, data)
        if not dict then return end
        local ok, val = pcall(cjson.encode, data)
        if ok then
            dict:set(key, val, CACHE_TTL)
        end
    end

    function self.size()
        return 0
    end

    return self
end

return _M