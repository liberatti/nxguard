local redis = require "resty.redis"
local utils = require "nxguard.utils"

-- Sensor security blocking -------------------------------------------------
local src_ip = utils.get_client_ip()

-- Check RBL -----------------------------------------------------------------
if not ngx.var.cache_server_url == ngx.null then
    local red = redis:new()
    red:set_timeout(1000)

    local ok, err = red:connect(ngx.var.cache_server_url, ngx.var.cache_server_port)
    if not ok then
        utils.respond(ngx.HTTP_INTERNAL_SERVER_ERROR, "Cache server failed: " .. ngx.var.cache_server_url .. " " .. err)
        ngx.exit(ngx.HTTP_FORBIDDEN)
    end
    local rbl_check, err = red:get("rbl:" .. src_ip)
    if err then
        utils.respond(ngx.HTTP_INTERNAL_SERVER_ERROR, "Cache server failed: " .. ngx.var.cache_server_url .. " " .. err)
        ngx.exit(ngx.HTTP_FORBIDDEN)
    end

    if not rbl_check == ngx.null then
        utils.respond(ngx.HTTP_FORBIDDEN, "IP '", src_ip, "' blocked by RBL.")
        ngx.exit(ngx.HTTP_FORBIDDEN)
    end
    red:set_keepalive(10000, 100)
end
