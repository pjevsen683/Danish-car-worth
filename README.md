# Danish Car Value (Home Assistant Custom Component)

This custom integration adds a set of Home Assistant sensors that retrieve the current market valuation for a Danish vehicle based on its licence plate by calling the public endpoints behind [tjekbil.dk](https://www.tjekbil.dk/).

## Features

- Fetches the latest `low`, `average`, and `high` price estimates (DKK) once every 24 hours
- Exposes additional attributes with mileage, headline text, and a direct search link on tjekbil.dk
- Groups the generated entities under a single device per licence plate for easy navigation in the UI

## Installation

1. Copy the `custom_components/danish_car_value` folder into your Home Assistant configuration directory
2. Restart Home Assistant to load the new platform

## Configuration

This integration is configured via YAML using the legacy sensor platform syntax. Each configured plate creates three sensors (minimum, average, maximum price).

```yaml
sensor:
  - platform: danish_car_value
    plate: AF39992
    name: Ford Mondeo Value
```

### Options

| Option | Type | Required | Description |
| ------ | ---- | -------- | ----------- |
| `plate` | string | ✅ | Danish licence plate (letters and numbers only) |
| `name` | string | ❌ | Friendly name prefix used for the generated sensors |

## Entity Overview

For the example above you will get:

- `sensor.ford_mondeo_value_minimum_price_af39992`
- `sensor.ford_mondeo_value_average_price_af39992`
- `sensor.ford_mondeo_value_maximum_price_af39992`

Each sensor includes attributes such as:

- `plate`
- `search_url`
- `price_count`
- `mileage`
- `brand`, `model`, `variant`

## Notes

- Updates are rate-limited to once per day to respect the upstream service
- The valuation endpoints occasionally return 0 values if the dataset is too small; the sensors will simply report 0 DKK in that case
- The integration relies on anonymous access to tjekbil.dk; if the service introduces stricter rate limits an automation that spreads requests over time is recommended

## Troubleshooting

- Check the Home Assistant logs for messages tagged `danish_car_value` if sensors fail to update
- Make sure the licence plate exists; values are only returned for plates present in the Danish Motor Registry
