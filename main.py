import urllib.parse
import requests
from py_spoo_url import Shortener

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

            model = vac_details[CONF_MODEL]

            schema = json.dumps(
                json.loads(device["schema"]), indent=2, ensure_ascii=False
            ).replace("\n", "\r\n")

            markdown = "```json\r\nyarr\r\n" + schema + "\r\n```"

            issues = requests.get(
                "https://api.github.com/repos/CodeFoodPixels/robovac-schema/issues?state=all&sort=created&direction=asc"
            ).json()

            found = False
            exact = False
            matched_issue = 0
            for issue in issues:
                if issue["title"] == model:
                    matched_issue = issue["html_url"]
                    if issue["body"] == markdown:
                        exact = True
                    else:
                        comments = requests.get(issue["comments_url"]).json()
                        for comment in comments:
                            if comment["body"] == markdown:
                                exact = True
                                break
                    found = True
                    break

            print("")
            print("Schema for {}:".format(model))
            print(markdown)
            print("")
            if found and exact:
                print("This schema has already been submitted!")
            elif found:
                print(
                    "A schema for this vacuum has been submitted, but does not match this one."
                )
                print("Please add your schema as a comment to this issue:")
                print(matched_issue)
            else:
                short_url = Shortener().shorten(
                    "https://github.com/codefoodpixels/robovac-schema/issues/new?title={}&body={}".format(
                        model, urllib.parse.quote_plus(markdown)
                    )
                )

                print("Submit this using the following link:")
                print(short_url)
            print("")

    return response


print("********** Robovac Schema Grabber **********")

# username = input("Anker/Eufy Username: ")
# password = getpass()

username = "speedysurfer2205@gmail.com"
password = "55HjL2Ye3OQZzg@G89V3"

get_eufy_vacuums({"username": username, "password": password})
