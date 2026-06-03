local redis = require "resty.redis"
local utils = require "nxguard.utils"
local cjson = require "cjson"
local http_ok, http = pcall(require, "resty.http")

-- Sensor security blocking -------------------------------------------------
local src_ip = utils.get_client_ip()

ngx.ctx.sensor = {
    name = ngx.var.sensor,
    action = "allowed"
}

if http_ok and ngx.var.ipxa_url and ngx.var.ipxa_url ~= "" then
    local httpc = http.new()
    httpc:set_timeout(5000)  -- 5 seconds
    local res, err = httpc:request_uri(ngx.var.ipxa_url .. "/api/ip/" .. src_ip, {
        method = "GET",
        headers = {
            ["Content-Type"] = "application/json",
            ["x-api-key"] = ngx.var.ipxa_key
        },
    })

    if res and (res.status == 200 or res.status == 201) then
        local data, decode_err = cjson.decode(res.body)
        if data then
            ngx.ctx.reputation = {
                action = "allowed",
                sources = {}
            }
            if data.reputation then
                local reputation_check_list = {}
                for feed in string.gmatch(ngx.var.blq_rbl or "", "([^|]+)") do
                    reputation_check_list[feed] = true
                end
                for _, item in ipairs(data.reputation) do
                    if item.feed then
                        if reputation_check_list[item.feed] then
                            if item.cls == 'deny' then
                                ngx.ctx.reputation.action = "blocked"
                                ngx.ctx.sensor.action = "blocked"
                            end
                        end
                        ngx.ctx.reputation.sources[#ngx.ctx.reputation.sources + 1] = item.feed
                    end
                end
            end
            if data.geoip then
                ngx.ctx.geoip_action = "allowed"
                ngx.ctx.geoip = data.geoip
                local geoip_check_list = {}
                for g in string.gmatch(ngx.var.blq_geo or "", "([^|]+)") do
                    geoip_check_list[g] = true
                end
                for _, item in ipairs(data.geoip) do
                    if item.country_code then
                        if geoip_check_list[item.country_code] then
                            ngx.ctx.geo.action = "blocked"
                            ngx.ctx.sensor.action = "blocked"
                        end
                    end
                end
            end
        else
            ngx.log(ngx.ERR, "Error decoding ipxa data: ", decode_err or "unknown error")
        end
    elseif err then
        ngx.log(ngx.ERR, "ipxa request failed: ", err)
    end
end
if ngx.ctx.sensor.action == "blocked" then
    utils.respond(403, "IP '" .. src_ip .. "' blocked by Sensor.")
end
-- Check RBL -----------------------------------------------------------------
--[[
if ngx.var.cache_server_url and ngx.var.cache_server_url ~= "" then
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

    if rbl_check ~= ngx.null then
        utils.respond(ngx.HTTP_FORBIDDEN, "IP '", src_ip, "' blocked by RBL.")
        ngx.exit(ngx.HTTP_FORBIDDEN)
    end
    red:set_keepalive(10000, 100)
end
]]
