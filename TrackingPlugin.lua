--[[
    TrackingPlugin.lua
    grandMA3 Lua Plugin for Person Tracking
    
    This plugin reads TrackingX and TrackingY user variables and applies them
    to Pan and Tilt attributes of a moving head fixture.
    
    Setup Instructions:
    1. Create User Variables in MA3:
       - $TrackingX (range 0-100)
       - $TrackingY (range 0-100)
    
    2. Configure OSC Input to write to these variables:
       - /stage/person1/x -> $TrackingX
       - /stage/person1/y -> $TrackingY
    
    3. Install this plugin and start it
    
    Author: Generated for grandMA3 OSC Tracking System
    Version: 1.0
]]

-- Plugin configuration
local CONFIG = {
    FIXTURE_ID = 101,           -- Fixture to control
    UPDATE_RATE = 0.05,         -- Update interval in seconds (20 Hz)
    PAN_MIN = 0,                -- Pan minimum in degrees
    PAN_MAX = 540,              -- Pan maximum in degrees
    TILT_MIN = 0,               -- Tilt minimum in degrees
    TILT_MAX = 270,             -- Tilt maximum in degrees
    INVERT_TILT = true,         -- Invert Y axis for natural movement
    SMOOTHING = 0.2,            -- Smoothing factor (0 = no smoothing, 1 = max smoothing)
}

-- Plugin state
local running = false
local lastPan = 0
local lastTilt = 0

-- Helper function to get user variable value
local function getUserVar(varName)
    local handle = GetVar(varName)
    if handle then
        local value = tonumber(handle)
        return value or 0
    end
    return 0
end

-- Helper function to map value from one range to another
local function mapRange(value, inMin, inMax, outMin, outMax)
    return outMin + (value - inMin) * (outMax - outMin) / (inMax - inMin)
end

-- Helper function to clamp value between min and max
local function clamp(value, min, max)
    if value < min then return min end
    if value > max then return max end
    return value
end

-- Helper function for smoothing (exponential moving average)
local function smooth(current, target, factor)
    return current + (target - current) * (1 - factor)
end

-- Main tracking function
local function updateTracking()
    -- Read user variables (0-100 range)
    local trackingX = getUserVar("TrackingX")
    local trackingY = getUserVar("TrackingY")
    
    -- Clamp input values
    trackingX = clamp(trackingX, 0, 100)
    trackingY = clamp(trackingY, 0, 100)
    
    -- Map to Pan range (0-540 degrees)
    local targetPan = mapRange(trackingX, 0, 100, CONFIG.PAN_MIN, CONFIG.PAN_MAX)
    
    -- Map to Tilt range (0-270 degrees)
    local targetTilt = mapRange(trackingY, 0, 100, CONFIG.TILT_MIN, CONFIG.TILT_MAX)
    
    -- Invert Tilt if configured (so moving up in camera moves light up)
    if CONFIG.INVERT_TILT then
        targetTilt = CONFIG.TILT_MAX - targetTilt
    end
    
    -- Apply smoothing
    if CONFIG.SMOOTHING > 0 then
        targetPan = smooth(lastPan, targetPan, CONFIG.SMOOTHING)
        targetTilt = smooth(lastTilt, targetTilt, CONFIG.SMOOTHING)
    end
    
    -- Update last values
    lastPan = targetPan
    lastTilt = targetTilt
    
    -- Apply to fixture
    -- Note: Using direct attribute commands for real-time control
    Cmd(string.format('Fixture %d At Pan %.2f', CONFIG.FIXTURE_ID, targetPan))
    Cmd(string.format('Fixture %d At Tilt %.2f', CONFIG.FIXTURE_ID, targetTilt))
    
    return true
end

-- Plugin entry point (called when plugin starts)
function Main()
    Printf("=== Person Tracking Plugin Started ===")
    Printf("Fixture ID: " .. CONFIG.FIXTURE_ID)
    Printf("Update Rate: " .. (1/CONFIG.UPDATE_RATE) .. " Hz")
    Printf("Pan Range: " .. CONFIG.PAN_MIN .. "-" .. CONFIG.PAN_MAX .. "°")
    Printf("Tilt Range: " .. CONFIG.TILT_MIN .. "-" .. CONFIG.TILT_MAX .. "°")
    Printf("Tilt Inverted: " .. tostring(CONFIG.INVERT_TILT))
    Printf("Smoothing: " .. (CONFIG.SMOOTHING * 100) .. "%")
    Printf("=====================================")
    
    running = true
    
    -- Initialize last values with current fixture position
    lastPan = CONFIG.PAN_MIN + (CONFIG.PAN_MAX - CONFIG.PAN_MIN) / 2
    lastTilt = CONFIG.TILT_MIN + (CONFIG.TILT_MAX - CONFIG.TILT_MIN) / 2
    
    -- Main loop
    while running do
        local success, err = pcall(updateTracking)
        
        if not success then
            Printf("Error in tracking update: " .. tostring(err))
        end
        
        -- Yield to prevent blocking MA3
        -- This is crucial for performance!
        coroutine.yield(CONFIG.UPDATE_RATE)
    end
    
    Printf("=== Person Tracking Plugin Stopped ===")
end

-- Cleanup function (called when plugin stops)
function Cleanup()
    Printf("Cleaning up Person Tracking Plugin...")
    running = false
    
    -- Optional: Return fixture to home position
    -- Cmd(string.format('Fixture %d At Pan %.2f', CONFIG.FIXTURE_ID, 270))
    -- Cmd(string.format('Fixture %d At Tilt %.2f', CONFIG.FIXTURE_ID, 135))
    
    Printf("Cleanup complete")
end

-- Return plugin information
return Main
