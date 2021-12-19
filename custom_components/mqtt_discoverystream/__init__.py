"""Publish simple item state changes via MQTT."""
import asyncio
import json
import logging

import voluptuous as vol

from homeassistant.components.mqtt import valid_publish_topic
from homeassistant.const import (
    MATCH_ALL,
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    CONF_INCLUDE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR,
    ATTR_XY_COLOR,
    ATTR_HS_COLOR,
    ATTR_TRANSITION,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_COLOR_TEMP,
    SUPPORT_EFFECT,
)
from homeassistant.helpers import device_registry, entity_registry
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import get_supported_features
from homeassistant.helpers.entityfilter import (
    INCLUDE_EXCLUDE_BASE_FILTER_SCHEMA,
    convert_include_exclude_filter,
)
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.json import JSONEncoder

_LOGGER = logging.getLogger(__name__)

ATTR_COLOR = "color"
ATTR_H = "h"
ATTR_S = "s"
ATTR_X = "x"
ATTR_Y = "y"
ATTR_R = "r"
ATTR_G = "g"
ATTR_B = "b"

CONF_BASE_TOPIC = "base_topic"
CONF_PUBLISH_ATTRIBUTES = "publish_attributes"
CONF_PUBLISH_TIMESTAMPS = "publish_timestamps"
CONF_PUBLISH_DISCOVERY = "publish_discovery"

DOMAIN = "mqtt_discoverystream"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: INCLUDE_EXCLUDE_BASE_FILTER_SCHEMA.extend(
            {
                vol.Required(CONF_BASE_TOPIC): valid_publish_topic,
                vol.Optional(CONF_PUBLISH_ATTRIBUTES, default=False): cv.boolean,
                vol.Optional(CONF_PUBLISH_TIMESTAMPS, default=False): cv.boolean,
                vol.Optional(CONF_PUBLISH_DISCOVERY, default=False): cv.boolean,
            }
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Set up the MQTT state feed."""
    conf = config.get(DOMAIN)
    publish_filter = convert_include_exclude_filter(conf)
    has_includes = True if conf.get(CONF_INCLUDE) else False
    base_topic = conf.get(CONF_BASE_TOPIC)
    publish_attributes = conf.get(CONF_PUBLISH_ATTRIBUTES)
    publish_timestamps = conf.get(CONF_PUBLISH_TIMESTAMPS)
    publish_discovery = conf.get(CONF_PUBLISH_DISCOVERY)
    if not base_topic.endswith("/"):
        base_topic = f"{base_topic}/"
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][base_topic] = {}
    hass.data[DOMAIN][base_topic]["conf_published"] = []
    dev_reg = await hass.helpers.device_registry.async_get_registry()
    ent_reg = await hass.helpers.entity_registry.async_get_registry()


    async def message_received(msg):
        """Handle new messages on MQTT."""
        explode_topic = msg.topic.split("/")
        domain = explode_topic[1]
        entity = explode_topic[2]
        element = explode_topic[3]

        _LOGGER.debug(f"Message received: topic {msg.topic}; payload: {msg.payload}")
        if element == "set":
            if msg.payload == STATE_ON:
               await  hass.services.async_call(domain, SERVICE_TURN_ON, {ATTR_ENTITY_ID: f"{domain}.{entity}"})
            elif msg.payload == STATE_OFF:
               await hass.services.async_call(domain, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: f"{domain}.{entity}"})
            else:
                _LOGGER.error(f'Invalid service for "set" - payload: {msg.payload} for {entity}')
        if element == "set_light":
            if domain != "light":
                _LOGGER.error(f'Invalid domain for "set_light" - payload: {msg.payload} for {entity}')
            else:
                payload_json = json.loads(msg.payload)
                service_payload =  {
                    ATTR_ENTITY_ID: f"{domain}.{entity}",
                }
                if ATTR_TRANSITION in payload_json:
                    service_payload[ATTR_TRANSITION] = payload_json[ATTR_TRANSITION]

                if payload_json["state"] == "ON":  
                    if ATTR_BRIGHTNESS in payload_json:
                        service_payload[ATTR_BRIGHTNESS] = payload_json[ATTR_BRIGHTNESS]
                    if ATTR_COLOR_TEMP in payload_json:
                        service_payload[ATTR_COLOR_TEMP] = payload_json[ATTR_COLOR_TEMP]
                    if ATTR_COLOR in payload_json:
                        if ATTR_H in payload_json[ATTR_COLOR]:
                            service_payload[ATTR_HS_COLOR] = [ payload_json[ATTR_COLOR][ATTR_H], payload_json[ATTR_COLOR][ATTR_S] ]
                        if ATTR_X in payload_json[ATTR_COLOR]:
                            service_payload[ATTR_XY_COLOR] = [ payload_json[ATTR_COLOR][ATTR_X], payload_json[ATTR_COLOR][ATTR_Y] ]
                        if ATTR_R in payload_json[ATTR_COLOR]:
                            service_payload[ATTR_RGB_COLOR] = [ payload_json[ATTR_COLOR][ATTR_R], payload_json[ATTR_COLOR][ATTR_G], payload_json[ATTR_COLOR][ATTR_B] ]
                    await hass.services.async_call(domain, SERVICE_TURN_ON, service_payload)
                elif payload_json["state"] == "OFF":
                    await hass.services.async_call(domain, SERVICE_TURN_OFF, service_payload)
                else:
                    _LOGGER.error(f'Invalid state for "set_light" - payload: {msg.payload} for {entity}')


    async def mqtt_publish(topic, payload, qos=None, retain=None):
        if asyncio.iscoroutinefunction(hass.components.mqtt.async_publish):
            await hass.components.mqtt.async_publish(hass, topic, payload, qos, retain)
        else:
            hass.components.mqtt.publish(topic, payload, qos, retain)

    async def _state_publisher(entity_id, old_state, new_state):
        if new_state is None:
            return

        if not publish_filter(entity_id):
            return

        mybase = f"{base_topic}{entity_id.replace('.', '/')}/"

        if publish_timestamps:
            if new_state.last_updated:
                await mqtt_publish(
                    f"{mybase}last_updated", new_state.last_updated.isoformat(), 1, True
                )
            if new_state.last_changed:
                await mqtt_publish(
                    f"{mybase}last_changed", new_state.last_changed.isoformat(), 1, True
                )

        if publish_attributes:
            for key, val in new_state.attributes.items():
                encoded_val = json.dumps(val, cls=JSONEncoder)
                await mqtt_publish(mybase + key, encoded_val, 1, True)

        ent_parts = entity_id.split(".") 
        ent_domain = ent_parts[0]
        ent_id = ent_parts[1]

        if publish_discovery and not entity_id in hass.data[DOMAIN][base_topic]["conf_published"]:
            config = {
                "uniq_id": f"mqtt_{entity_id}",
                "name": ent_id.replace("_", " ") .title(),
                "stat_t": f"{mybase}state",
                "json_attr_t": f"{mybase}attributes",
                "avty_t": f"{mybase}availability"
            }
            if ("device_class" in new_state.attributes):
                config["dev_cla"] = new_state.attributes["device_class"]
            if ("unit_of_measurement" in new_state.attributes):
                config["unit_of_meas"] = new_state.attributes["unit_of_measurement"]
            if ("state_class" in new_state.attributes):
                config["stat_cla"] = new_state.attributes["state_class"]
                
            publish_config = False
            if ent_domain == "sensor" and (has_includes or "device_class" in new_state.attributes):
                publish_config = True

            elif ent_domain == "binary_sensor" and (has_includes or "device_class" in new_state.attributes):
                config["pl_off"] = STATE_OFF
                config["pl_on"] = STATE_ON
                publish_config = True

            elif ent_domain == "switch":
                config["pl_off"] = STATE_OFF
                config["pl_on"] = STATE_ON
                config["cmd_t"] = f"{mybase}set"
                publish_config = True

            elif ent_domain == "device_tracker":
                publish_config = True

            elif ent_domain == "light":
                del config["json_attr_t"]
                config["cmd_t"] = f"{mybase}set_light"
                config["schema"] = "json"

                supported_features = get_supported_features(hass, entity_id)
                if supported_features & SUPPORT_BRIGHTNESS:
                    config["brightness"] = True
                if supported_features & SUPPORT_EFFECT:
                    config["effect"] = True
                if "supported_color_modes" in new_state.attributes:
                    config["color_mode"] = True
                    config["supported_color_modes"] = new_state.attributes["supported_color_modes"]

                publish_config = True

            if publish_config:
                for entry in ent_reg.entities.values():
                    if entry.entity_id != entity_id:
                        continue
                    for device in dev_reg.devices.values():
                        if device.id != entry.device_id:
                            continue
                        config["dev"] = {}
                        if device.manufacturer:
                            config["dev"]["mf"] = device.manufacturer
                        if device.model:
                            config["dev"]["mdl"] = device.model
                        if device.name:
                            config["dev"]["name"] = device.name
                        if device.sw_version:
                            config["dev"]["sw"] = device.sw_version
                        if device.identifiers:
                            config["dev"]["ids"] = [ id[1] for id in device.identifiers ]
                        if device.connections:
                            config["dev"]["cns"] = device.connections

                encoded = json.dumps(config, cls=JSONEncoder)
                await mqtt_publish(f"{mybase}config", encoded, 1, True)
                hass.data[DOMAIN][base_topic]["conf_published"].append(entity_id)

        if publish_discovery:
            if ent_domain == "light":
                payload = {
                    "state": "ON" if new_state.state == STATE_ON else "OFF",
                }
                if ("brightness" in new_state.attributes):
                    payload["brightness"] = new_state.attributes["brightness"]
                if ("color_mode" in new_state.attributes):
                    payload["color_mode"] = new_state.attributes["color_mode"]
                if ("color_temp" in new_state.attributes):
                    payload["color_temp"] = new_state.attributes["color_temp"]
                if ("effect" in new_state.attributes):
                    payload["effect"] = new_state.attributes["effect"]
                
                color = {}
                if ("hs_color" in new_state.attributes):
                    color["h"] = new_state.attributes["hs_color"][0]
                    color["s"] = new_state.attributes["hs_color"][1]
                if ("xy_color" in new_state.attributes):
                    color["x"] = new_state.attributes["xy_color"][0]
                    color["x"] = new_state.attributes["xy_color"][1]
                if ("rgb_color" in new_state.attributes):
                    color["r"] = new_state.attributes["rgb_color"][0]
                    color["g"] = new_state.attributes["rgb_color"][1]
                    color["b"] = new_state.attributes["rgb_color"][2]
                if color:
                    payload["color"] = color

                await mqtt_publish(f"{mybase}state", json.dumps(payload, cls=JSONEncoder), 1, True)

                payload = "offline" if new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, None) else "online"
                await mqtt_publish(f"{mybase}availability", payload, 1, True)
            else:
                payload = new_state.state
                await mqtt_publish(f"{mybase}state", payload, 1, True)

                payload = "offline" if new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, None) else "online"
                await mqtt_publish(f"{mybase}availability", payload, 1, True)

                attributes = {}
                for key, val in new_state.attributes.items():
                    attributes[key] = val
                encoded = json.dumps(attributes, cls=JSONEncoder)
                await mqtt_publish(f"{mybase}attributes", encoded, 1, True)
        else:
            payload = new_state.state
            await mqtt_publish(f"{mybase}state", payload, 1, True)


    if publish_discovery:
        await hass.components.mqtt.async_subscribe(f"{base_topic}switch/+/set", message_received)
        await hass.components.mqtt.async_subscribe(f"{base_topic}light/+/set_light", message_received)

    async_track_state_change(hass, MATCH_ALL, _state_publisher)
    return True

