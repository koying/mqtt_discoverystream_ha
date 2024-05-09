# MQTT DiscoveryStream integration for Home Assistant

This is an "extension" of the builtin [`mqtt_statestream`](https://www.home-assistant.io/integrations/mqtt_statestream/) integration.  
Besides the functionalities of the hereabove, it also allows to publish and handles an [MQTT "discovery"](https://www.home-assistant.io/docs/mqtt/discovery) setup.

## Changelog

### 1.4

- FIX: MQTT race condition at startup

### 1.3

- FIX: name when entity is not in entity registry

### 1.2

- FIX: Avoid duplicating entity and device names + icon support (@rohankapoorcom)
- ADD: button entities support (@rohankapoorcom)
- ADD: input_booleans entities support (@rohankapoorcom)
- ADD: devcontainer support (@rohankapoorcom)

### 1.1

unreleased

### 1.0

- FIX: ha.components depreciation
- FIX: Only handle service calls for discoveries we published
- ADD: customize unique prefix
- FIX: color attr when turned off
- FIX: always publish
- FIX: availability

### 0.9

- Fix `async_get_registry` warning

### 0.8

- Add "discovery_topic" to split config and state topics

### 0.7

- Fix availability for lights

### 0.6

- Adapt to 2021.12

### 0.5

- Add device support
- FIX color support
- Add availability support

### 0.4


- Add device_tracker
- Add light transitions
- Initial HACS release

### 0.3

- Manage color temperature

### 0.3

- Fix binary_sensors

### 0.1

- Initial release:
  Handles:
    - sensors
    - switches
    - lights (partial)

## Pre-requisites

1. MQTT configured

## Installation

### HACS

1. Launch HACS
1. Navigate to the Integrations section
1. "+ Explore & Add Repositories" button in the bottom-right
1. Search for "MQTT DiscoveryStream"
1. Select "Install this repository"
1. Restart Home Assistant

### Home Assistant

The integration is configured via YAML only.

Example:

```yaml
mqtt_discoverystream:
  base_topic: test_HA
  publish_attributes: false
  publish_timestamps: true
  publish_discovery: true
  include:
    entities:
      - sensor.owm_hourly_humidity
      - sensor.jellyfin_cloud
      - light.wled_esp
  exclude:
    entities:
      - sensor.plug_xiaomi_1_electrical_measurement
```

## Configuration

### Options

This integration can only be configuration via YAML.
The base options are the same as the mqtt_statestream one. 

| key                | default | required | description                                                                  |
| ------------------ | ------- | -------- | ---------------------------------------------------------------------------- |
| base_topic         | none    | yes      | Base topic used to generate the actual topic used to publish.                |
| discovery_topic    | none    | no       | Topic where the configuration topics will be created. Defaults to base_topic |
| publish_attributes | false   | no       | Publish attributes of the entity as well as the state.                       |
| publish_timestamps | false   | no       | Publish the last_changed and last_updated timestamps for the entity.         |
| publish_discovery  | false   | no       | Publish the discovery topic ("config").                                      |
| include / exclude  | none    | no       | Configure which integrations should be included / excluded from publishing.  |

## Credits

- This custom component is based upon the `mqtt_statestream` one from HA Core.  
