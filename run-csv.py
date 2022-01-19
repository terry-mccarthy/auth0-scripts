#!/usr/bin/env python3.8
import http.client
import os
import json
import re
import base64
from urllib.parse import urlparse, quote_plus

"""
  Use the token api to reques the access token 
  neet the ENV vars for Client Secret, ID and URL

  curl --request POST \
    --url $URL \
    --header 'content-type: application/json' \
    --data "{\"client_id\":\"$CLIENT_ID\",\"client_secret\":\"$CLIENT_SECRET\",\"audience\":\"$AUDIENCE\",\"grant_type\":\"client_credentials\"}

"""
def get_token(base_url):
  client_id = os.getenv('CLIENT_ID') or Exception('CLIENT_ID env var not defined').throw()
  client_secret = os.getenv('CLIENT_SECRET') or Exception('CLIENT_SECRET env var not defined').throw()

  audience = 'https://' + base_url + '/api/v2/'

  #print(base_url)
  conn = http.client.HTTPSConnection(base_url)

  payload = { 
    'client_id': client_id,
    'client_secret': client_secret,
    'audience': audience,
    'grant_type': 'client_credentials'
  }
  headers = { 'content-type': "application/json" }

  conn.request("POST", "/oauth/token", json.dumps(payload), headers)

  res = conn.getresponse()
  data = res.read()

  res_json = data.decode("utf-8")
  access_token = json.loads(res_json)["access_token"]

  return access_token

"""
"""
def url_from_token(access_token):
  js = access_token.split('.')
  AUTH0_DOMAIN_URL = json.loads(base64.b64decode(js[1]+"==="))["iss"]
  
  url_result = urlparse(AUTH0_DOMAIN_URL)
  #url_result.netloc)
  
  # 'test.vha-dev.auth0.com'
  url = url_result.netloc
  return url

"""
  Create the user in tenant with phone number as MSISDN

  curl --request POST \
      -s -H "Authorization: Bearer ${access_token}" \
      --url ${AUTH0_DOMAIN_URL}api/v2/users \
      --header 'content-type: application/json' \
      --data "${PAYLOAD}"
"""
def create_user(msisdn, access_token):
  base_url = url_from_token(access_token)
  conn = http.client.HTTPSConnection(base_url)

  headers = { 
    'content-type': "application/json", 
    'Authorization': "Bearer {}".format(access_token)
  }

  payload= {
    "phone_verified": True
  }
  payload["connection"] = "sms"
  payload["app_metadata"] = {}
  payload["user_metadata"] = {}
  payload["phone_number"] = "+" + msisdn

  #json.dumps(payload))
  # print("headers", headers)
  # print(",,", json.dumps(payload))
  conn.request("POST", "/api/v2/users", json.dumps(payload), headers)

  res = conn.getresponse()
  data = res.read()
  res_json = json.loads(data.decode("utf-8"))
  if "user_id" in res_json:
    user_id = res_json["user_id"]
  else:
    raise Exception("Bad response from create_user - {}".format(res_json))

  #print(user_id)
  return user_id

"""
curl -X PATCH \
  -H "Authorization: Bearer ${access_token}" \
  -H 'content-type: application/json' \
  -d "${PAYLOAD}" \
  ${AUTH0_DOMAIN_URL}api/v2/users/${user_id}
"""
def update_user(user_id, access_token, block=False):
  base_url = url_from_token(access_token)
  conn = http.client.HTTPSConnection(base_url)

  headers = { 
    'content-type': "application/json", 
    'Authorization': "Bearer {}".format(access_token)
  }

  payload= {
    "blocked": block
  }
  user_encoded = quote_plus(user_id)

  conn.request("PATCH", "/api/v2/users/{}".format(user_encoded), json.dumps(payload), headers)

  res = conn.getresponse()
  data = res.read()
  # res_json = data.decode("utf-8")
  print(user_id, ' is unblocked')
  return


"""
  Update a list of users as defined in file as blocked or unblocked
"""
def update_user_list(filelist, block=True):
  url = os.getenv('URL') or Exception("URL env var not defined 'https://test.vha-dev.auth0.com/oauth/token'").throw()
  url_result = urlparse(url)
  base_url = url_result.netloc
  access_token = get_token(base_url)

  #fileunblock='./csvs/unblock.csv'
  with open(filelist) as f:
    for line in f:
      msisdn = re.search('(\d+).*', line).group(1)
      user_id = create_user(msisdn, access_token)
      update_user(user_id, access_token, block)

###########
update_user_list('./csvs/block.csv', True)
update_user_list('./csvs/unblock.csv', False)