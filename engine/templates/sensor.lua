local http_ok, http = pcall(require, "resty.http")
local cache = require("nxguard.cache").new(1000, 30)
local utils = require("nxguard.utils")
local cjson = require("cjson")

local BLOCKED_COUNTRIES = utils.parse_list("{{blq_geo}}")
local BLOCKED_RBL = utils.parse_list("{{blq_rbl}}")
local TRUSTED = utils.parse_list("{{trusted}}")

local ip = utils.get_client_ip()

ngx.ctx.country_code = "--"
ngx.ctx.risk_score = 0
ngx.ctx.trusted = false

local cached = cache.get(ip)
if cached then
    ngx.ctx.country_code = cached.country_code
    ngx.ctx.risk_score = cached.risk_score
    ngx.ctx.trusted = cached.trusted
    ngx.ctx.ipxa = "cached"
else
    local httpc = http.new()
    httpc:set_timeout(2000)

    local res, err = httpc:request_uri("{{ipxa_url}}/api/ip/info/" .. ip, {
        method = "GET",
        headers = {
            ["content-type"] = "application/json",
            ["x-api-key"] = "{{ipxa_key}}",
        },
    })

    if res and res.status == 200 and res.body then
        local ok, body = pcall(cjson.decode, res.body)
        if ok and type(body) == "table" then
            ngx.ctx.ipxa = "hit"
            if body.location and body.location.country_code then
                ngx.ctx.country_code = body.location.country_code
            end
            if body.security then
                ngx.ctx.risk_score = tonumber(body.security.risk_score) or 0
                ngx.ctx.trusted = (body.security.trusted == true or string.lower(tostring(body.security.trusted)) == "true")
            end
        end
    else
        ngx.log(ngx.ERR, "[ipxa-api] request failed for IP: ", ip, " | status: ", res and res.status or "nil", " | error: ", err or "none")
    end

    cache.set(ip, {
        country_code = ngx.ctx.country_code,
        risk_score = ngx.ctx.risk_score,
        trusted = ngx.ctx.trusted
    })
end

ngx.req.set_header("X-NXG-Country-Code", ngx.ctx.country_code or "--")
ngx.req.set_header("X-NXG-Risk-Score", tostring(ngx.ctx.risk_score or 0))
ngx.req.set_header("X-NXG-Trusted", tostring(ngx.ctx.trusted or false))
if ngx.ctx.ipxa then
    ngx.req.set_header("X-NXG-IPXA", ngx.ctx.ipxa)
end

if not ngx.ctx.trusted then
    if ngx.ctx.country_code and BLOCKED_COUNTRIES[ngx.ctx.country_code] then
        ngx.ctx.geoip_action = "blocked"
        ngx.req.set_header("X-NXG-GeoIP-Action", "blocked")
        return utils.respond(ngx.HTTP_FORBIDDEN,
            "[block/geo-ip]: " .. ip .. " country_code=" .. ngx.ctx.country_code)
    else
        ngx.ctx.geoip_action = "allowed"
        ngx.req.set_header("X-NXG-GeoIP-Action", "allowed")
    end

    if tonumber(ngx.ctx.risk_score) > 0 then
        ngx.ctx.reputation_action = "blocked"
        ngx.req.set_header("X-NXG-Reputation-Action", "blocked")
        return utils.respond(ngx.HTTP_FORBIDDEN,
            "[block/risk-score]: " .. ip .. " risk_score=" .. ngx.ctx.risk_score)
    else
        ngx.ctx.reputation_action = "allowed"
        ngx.req.set_header("X-NXG-Reputation-Action", "allowed")
    end
end