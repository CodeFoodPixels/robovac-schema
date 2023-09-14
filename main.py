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

  tuya_client = TuyaAPISession(username="eh-" + self[CONF_CLIENT_ID],
                               country_code=self[CONF_PHONE_CODE],
                               timezone=self[CONF_TIMEZONE])

  items = device_response["items"]
  print("Devices")
  for item in items:
    if item["device"]["product"]["appliance"] == "Cleaning":
      print("    Cleaning device: {} ({})".format(item["device"]["alias_name"], item["device"]["id"]))
      try:
        device = tuya_client.get_device(item["device"]["id"])
        print("        Found device in tuya")
        print("            {}".format(device["name"]))
        print("            {}".format(device["schema"]))
      except:
        print("        Could not find device on tuya")
    else:
      print("    Non-cleaning device: {} ({})".format(item["device"]["alias_name"], item["device"]["id"]))

  return response


print("********** Robovac Auth Tester **********")

username = input("Anker/Eufy Username: ")
password = getpass()

get_eufy_vacuums({"username": username, "password": password})

print("Test script ran successfully")
