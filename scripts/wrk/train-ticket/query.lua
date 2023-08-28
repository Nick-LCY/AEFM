socket = require "socket"
local host = "http://localhost:8080"
local req = {}

function init()
    local method = "POST"
    local path = "http://localhost:32677/api/v1/travelservice/trips/left"
    local headers = {}
    headers["Content-Type"] = "application/json"

    local body
    local datetime = "2100-11-31"
    local startPlace, endPlace

    startPlace = "shanghai"
    endPlace = "suzhou"
    body = '{"departureTime":"' .. datetime .. '","startingPlace":"' .. startPlace .. '","endPlace":"' .. endPlace ..
               '"}'
    req["0"] = wrk.format(method, path, headers, body)

    startPlace = "suzhou"
    endPlace = "shanghai"
    body = '{"departureTime":"' .. datetime .. '","startingPlace":"' .. startPlace .. '","endPlace":"' .. endPlace ..
               '"}'
    req["1"] = wrk.format(method, path, headers, body)
end

request = function()
    local coin = math.random()
    if coin < 0.5 then
        -- Request with less span
        return req["0"]
    else
        -- Request with more span
        return req["1"]
    end
end
