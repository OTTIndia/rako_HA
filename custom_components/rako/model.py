from typing import TypedDict

class RakoDomainEntryData(TypedDict):
    rako_bridge_client: "RakoBridge"
    rako_light_map: dict
    rako_switch_map: dict
    rako_cover_map: dict
    rako_rgbw_map: dict
    rako_listener_task: object
