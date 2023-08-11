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


class CannotConnect(BaseException):
  """Error to indicate we cannot connect."""


class InvalidAuth(BaseException):
  """Error to indicate there is invalid auth."""


def get_eufy_vacuums(self):
  """Login to Eufy and get the vacuum details"""

  eufy_session = EufyLogon(self["username"], self["password"])
  print("Logging in to Eufy")
  response = eufy_session.get_user_info()
  if response.status_code != 200:
    raise CannotConnect

  user_response = response.json()
  if user_response["res_code"] != 1:
    raise InvalidAuth

  print("    Success")
  print("Getting Eufy device info")
  response = eufy_session.get_device_info(
    user_response["user_info"]["request_host"],
    user_response["user_info"]["id"],
    user_response["access_token"],
  )
  device_response = response.json()
  print("    Success")

  response = eufy_session.get_user_settings(
    user_response["user_info"]["request_host"],
    user_response["user_info"]["id"],
    user_response["access_token"],
  )
  settings_response = response.json()

  self[CONF_CLIENT_ID] = user_response["user_info"]["id"]
  self[CONF_PHONE_CODE] = settings_response["setting"]["home_setting"]["tuya_home"]["tuya_region_code"]
  self[CONF_TIMEZONE] = user_response["user_info"]["timezone"]

  debug_user_response = user_response["user_info"].copy()
  debug_user_response["id"] = "REDACTED"
  debug_user_response["nick_name"] = "REDACTED"
  debug_user_response["email"] = "REDACTED"
  debug_user_response["mobile"] = "REDACTED"

  print("user response")
  print(json.dumps(debug_user_response, indent=4))
  debug_settings_response = settings_response["setting"].copy()
  debug_settings_response["user_id"] = "REDACTED"
  debug_settings_response["home_setting"]["tuya_home"]["tuya_home_id"] = "REDACTED"

  print("settings response")
  print(json.dumps(debug_settings_response, indent=4))


  # self[CONF_VACS] = {}
  items = device_response["items"]
  allvacs = {}
  for item in items:
    if item["device"]["product"]["appliance"] == "Cleaning":
      vac_details = {
        CONF_ID: item["device"]["id"],
        CONF_MODEL: item["device"]["product"]["product_code"],
        CONF_NAME: item["device"]["alias_name"],
        CONF_DESCRIPTION: item["device"]["name"],
        CONF_MAC: item["device"]["wifi"]["mac"],
        CONF_IP_ADDRESS: "",
      }
      allvacs[item["device"]["id"]] = vac_details
  self[CONF_VACS] = allvacs

  tuya_client = TuyaAPISession(username="eh-" + self[CONF_CLIENT_ID],
                               country_code=self[CONF_PHONE_CODE],
                               timezone=self[CONF_TIMEZONE])
  for home in tuya_client.list_homes():
    for device in tuya_client.list_devices(home["groupId"]):
      self[CONF_VACS][device["devId"]][CONF_ACCESS_TOKEN] = device["localKey"]
      self[CONF_VACS][device["devId"]][CONF_LOCATION] = home["groupId"]
  return response


print("********** Robovac Auth Tester **********")

username = input("Anker/Eufy Username: ")
password = getpass()

get_eufy_vacuums({"username": username, "password": password})

print("Test script ran successfully")
