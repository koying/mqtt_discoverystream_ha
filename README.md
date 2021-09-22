# MQTT DiscoveryStream integration for Home Assistant

This is an "extension" of the builtin [`mqtt_statestream`](https://www.home-assistant.io/integrations/mqtt_statestream/) integration.  
Besides the functionalities of the hereabove, it also allows to publish and handles an [MQTT "disvovery"](https://www.home-assistant.io/docs/mqtt/discovery) setup.

## Changelog

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

## Pre-requistes

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

| key                | default | required | description                                                                |
| ------------------ | ------- | -------- | -------------------------------------------------------------------------- |
| base_topic         | none    | yes      | Base topic used to generate the actual topic used to publish.              |
| publish_attributes | false   | no       | Publish attributes of the entity as well as the state.                     |
| publish_timestamps | false   | no       | Publish the last_changed and last_updated timestamps for the entity.       |
| publish_discovery  | false   | no       | Publish the discovery topic ("config").                                    |
| include / exclude  | none    | no       | Configure which integrations should be included / exluded from publishing. |

## Credits

- This custom component is based upon the `mqtt_statestream` one from HA Core.  
