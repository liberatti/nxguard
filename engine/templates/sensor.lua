local http_ok, http = pcall(require, "resty.http")
local cache = require("cache").new(1000, 30)
local utils = require("utils")
local cjson = require("cjson")

local BLOCKED_COUNTRIES = utils.parse_list("{{blq_geo}}")
local BLOCKED_RBL = utils.parse_list("{{blq_rbl}}")
local TRUSTED = utils.parse_list("{{trusted}}")

local ip = utils.get_client_ip()

ngx.header["X-Request-Id"] = ngx.var.request_id

ngx.ctx.country_code = "--"
ngx.ctx.risk_score = -1
ngx.ctx.trusted = false

local cached = cache.get(ip)
local api_ok = false
if cached then
    ngx.ctx.country_code = cached.country_code
    ngx.ctx.risk_score = cached.risk_score
    ngx.ctx.trusted = cached.trusted
    api_ok = "cached"
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

    if res and res.status == 200 and res.headers then
        api_ok = true
        local headers = res.headers

        ngx.ctx.country_code = utils.get_header(headers, "x-country-code") or "--"
        ngx.ctx.risk_score = tonumber(utils.get_header(headers, "x-risk-score")) or -1
        ngx.ctx.trusted = (string.lower(tostring(utils.get_header(headers, "x-trusted"))) == "true")
    end

    if ngx.ctx.country_code and ngx.ctx.risk_score ~= -1 then
        cache.set(ip, {
            country_code = ngx.ctx.country_code,
            risk_score = ngx.ctx.risk_score,
            trusted = ngx.ctx.trusted
        })
    end
end

if not ngx.ctx.trusted then
    if ngx.ctx.country_code and BLOCKED_COUNTRIES[ngx.ctx.country_code] then
        return utils.respond(ngx.HTTP_FORBIDDEN,
            "[block/geo-ip]: " .. ip .. " country_code=" .. ngx.ctx.country_code)
    end

    if tonumber(ngx.ctx.risk_score) > 0 then
        return utils.respond(ngx.HTTP_FORBIDDEN,
            "[block/risk-score]: " .. ip .. " risk_score=" .. ngx.ctx.risk_score)
    end
end