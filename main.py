from countries import (
    get_phone_code_by_country_code,
    get_phone_code_by_region,
    get_region_by_country_code,
    get_region_by_phone_code,
)
from tuyawebapi import TuyaAPISession
from eufywebapi import EufyLogon

from getpass import getpass

import json

CONF_CLIENT_ID = "CONF_CLIENT_ID"
CONF_PHONE_CODE = "CONF_PHONE_CODE"
CONF_TIMEZONE = "CONF_TIMEZONE"
CONF_ID = "CONF_ID"
CONF_MODEL = "CONF_MODEL"
CONF_NAME = "CONF_NAME"
CONF_DESCRIPTION = "CONF_DESCRIPTION"
CONF_MAC = "CONF_MAC"
CONF_IP_ADDRESS = "CONF_IP_ADDRESS"
CONF_VACS = "CONF_VACS"
CONF_ACCESS_TOKEN = "CONF_ACCESS_TOKEN"
CONF_LOCATION = "CONF_LOCATION"
CONF_AUTODISCOVERY = "CONF_AUTODISCOVERY"
CONF_REGION = "CONF_REGION"
CONF_COUNTRY_CODE = "CONF_COUNTRY_CODE"
CONF_TIME_ZONE = "CONF_TIME_ZONE"


class CannotConnect(BaseException):
    """Error to indicate we cannot connect."""


class InvalidAuth(BaseException):
    """Error to indicate there is invalid auth."""


def get_eufy_vacuums(self):
    """Login to Eufy and get the vacuum details"""

    eufy_session = EufyLogon(self["username"], self["password"])
    response = eufy_session.get_user_info()
    if response.status_code != 200:
        raise CannotConnect

    user_response = response.json()
    if user_response["res_code"] != 1:
        raise InvalidAuth

    response = eufy_session.get_device_info(
        user_response["user_info"]["request_host"],
        user_response["user_info"]["id"],
        user_response["access_token"],
    )

    device_response = response.json()

    response = eufy_session.get_user_settings(
        user_response["user_info"]["request_host"],
        user_response["user_info"]["id"],
        user_response["access_token"],
    )
    settings_response = response.json()

    self[CONF_CLIENT_ID] = user_response["user_info"]["id"]
    if (
        "tuya_home" in settings_response["setting"]["home_setting"]
        and "tuya_region_code"
        in settings_response["setting"]["home_setting"]["tuya_home"]
    ):
        self[CONF_REGION] = settings_response["setting"]["home_setting"]["tuya_home"][
            "tuya_region_code"
        ]
        if user_response["user_info"]["phone_code"]:
            self[CONF_COUNTRY_CODE] = user_response["user_info"]["phone_code"]
        else:
            self[CONF_COUNTRY_CODE] = get_phone_code_by_region(self[CONF_REGION])
    elif user_response["user_info"]["phone_code"]:
        self[CONF_REGION] = get_region_by_phone_code(
            user_response["user_info"]["phone_code"]
        )
        self[CONF_COUNTRY_CODE] = user_response["user_info"]["phone_code"]
    elif user_response["user_info"]["country"]:
        self[CONF_REGION] = get_region_by_country_code(
            user_response["user_info"]["country"]
        )
        self[CONF_COUNTRY_CODE] = get_phone_code_by_country_code(
            user_response["user_info"]["country"]
        )
    else:
        self[CONF_REGION] = "EU"
        self[CONF_COUNTRY_CODE] = "44"

    self[CONF_TIME_ZONE] = user_response["user_info"]["timezone"]

    tuya_client = TuyaAPISession(
        username="eh-" + self[CONF_CLIENT_ID],
        region=self[CONF_REGION],
        timezone=self[CONF_TIME_ZONE],
        phone_code=self[CONF_COUNTRY_CODE],
    )

    items = device_response["items"]
    self[CONF_VACS] = {}
    for item in items:
        if item["device"]["product"]["appliance"] == "Cleaning":
            try:
                device = tuya_client.get_device(item["device"]["id"])

                vac_details = {
                    CONF_ID: item["device"]["id"],
                    CONF_MODEL: item["device"]["product"]["product_code"],
                    CONF_NAME: item["device"]["alias_name"],
                    CONF_DESCRIPTION: item["device"]["name"],
                    CONF_MAC: item["device"]["wifi"]["mac"],
                    CONF_IP_ADDRESS: "",
                    CONF_AUTODISCOVERY: True,
                    CONF_ACCESS_TOKEN: device["localKey"],
                }
                self[CONF_VACS][item["device"]["id"]] = vac_details

                print("")
                print("Schema for {}:".format(vac_details[CONF_MODEL]))
                print(json.dumps(json.loads(device["schema"]), indent=2))
                print("")
            except:
                return

    return response


print("********** Robovac Schema Grabber **********")

username = input("Anker/Eufy Username: ")
password = getpass()

get_eufy_vacuums({"username": username, "password": password})
