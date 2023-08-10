from tuyawebapi import TuyaAPISession
from eufywebapi import EufyLogon

from getpass import getpass

CONF_CLIENT_ID = "CONF_CLIENT_ID"
CONF_PHONE_CODE = "CONF_PHONE_CODE"
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
  print("    t9147_sdk_flag: {}".format(
    user_response["user_info"]["t9147_sdk_flag"]))
  print("    Success")
  print("Getting Eufy device info")
  response = eufy_session.get_device_info(
    user_response["user_info"]["request_host"],
    user_response["user_info"]["id"],
    user_response["access_token"],
  )
  device_response = response.json()
  print("    Success")

  self[CONF_CLIENT_ID] = user_response["user_info"]["id"]
  self[CONF_PHONE_CODE] = user_response["user_info"]["phone_code"]

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
                               country_code=self[CONF_PHONE_CODE])
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
