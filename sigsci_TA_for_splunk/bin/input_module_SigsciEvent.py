
# encoding = utf-8

import os
import sys
import time
#import datetime
from datetime import datetime, timedelta
import json
import calendar
import requests

'''
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating
    the modular input.
'''
def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    # This example accesses the modular input variable
    # site = definition.parameters.get('site', None)
    pass

def collect_events(helper, inputs, ew):
    """Implement your data collection logic here"""

    loglevel = helper.get_log_level()
    # Proxy setting configuration
    proxy_settings = helper.get_proxy()

    #User credentials
    account = helper.get_user_credential("username")
    #Global variable configuration
    email = helper.get_global_setting("email")
    password = helper.get_global_setting("password")
    #site_name = helper.get_global_setting('site')
    corp_name = helper.get_global_setting("corp")
    
    api_host = 'https://dashboard.signalsciences.net'
    helper.log_debug("email: %s" % email)
    helper.log_debug("corp: %s" % corp_name)

    helper.log_info("log message")
    helper.log_debug("log message")


    #Definition for error handling on the response code

    def checkResponse(code, responseText):
        if code == 400:
            helper.log_error("Bad API Request (ResponseCode: %s)" % (code))
            helper.log_error("ResponseError: %s" % responseText)
            helper.log_error('url: %s' % url)
            helper.log_error('from: %s' % from_time)
            helper.log_error('until: %s' % until_time)
            helper.log_error('email: %s' % email)
            helper.log_error('Corp: %s' % corp_name)
            helper.log_error('SiteName: %s' % site_name)
            exit(code)
        elif code == 500:
            helper.log_error("Caused an Internal Server error (ResponseCode: %s)" % (code))
            helper.log_error("ResponseError: %s" % responseText)
            helper.log_error('url: %s' % url)
            helper.log_error('from: %s' % from_time)
            helper.log_error('until: %s' % until_time)
            helper.log_error('email: %s' % email)
            helper.log_error('Corp: %s' % corp_name)
            helper.log_error('SiteName: %s' % site_name)
            exit(code)
        elif code == 401:
            helper.log_error("Unauthorized, likely bad credentials or site configuration, or lack of permissions (ResponseCode: %s)" % (code))
            helper.log_error("ResponseError: %s" % responseText)
            helper.log_error('email: %s' % email)
            helper.log_error('Corp: %s' % corp_name)
            helper.log_error('SiteName: %s' % site_name)
            exit(code)
        elif code >= 400 and code <= 599:
            helper.log_error("ResponseError: %s" % responseText)
            helper.log_error('url: %s' % url)
            helper.log_error('from: %s' % from_time)
            helper.log_error('until: %s' % until_time)
            helper.log_error('email: %s' % email)
            helper.log_error('Corp: %s' % corp_name)
            helper.log_error('SiteName: %s' % site_name)
            exit(code)

    helper.log_info("Authenticating to SigSci API")
    # Authenticate
    authUrl = api_host + '/api/v0/auth'
    auth = requests.post(
        authUrl,
        data = {"email": email, "password": password}
    )
    content = {"email": email, "password": password}
    # method = "POST"
    # auth = helper.send_http_request(authUrl, method, parameters=None, payload=content,
    #                           headers=None, cookies=None, verify=True, cert=None, timeout=None, use_proxy=True, data=content)

    authCode = auth.status_code
    authError = auth.text

    checkResponse(authCode, authError)

    parsed_response = auth.json()
    token = parsed_response['token']
    helper.log_info("Authenticated")

    def pullEvents (curSite, delta, key=None):
        # Calculate UTC timestamps for the previous full hour
        # E.g. if now is 9:05 AM UTC, the timestamps will be 8:00 AM and 9:00 AM
        site_name = curSite
        until_time = datetime.utcnow() - timedelta(minutes=5)
        until_time = until_time.replace(second=0, microsecond=0)
        from_time = until_time - timedelta(minutes=delta)
        until_time = calendar.timegm(until_time.utctimetuple())
        from_time = calendar.timegm(from_time.utctimetuple())

        helper.log_debug("From: %s\nUntil:%s" % (from_time, until_time))

        # Loop across all the data and output it in one big JSON object
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer %s' % token
        }

        #url = api_host + ('/api/v0/corps/%s/sites/%s/feed/requests?from=%s&until=%s' % (corp_name, site_name, from_time, until_time))
        url = api_host + ('/api/v0/corps/%s/sites/%s/analytics/events?from=%s&until=%s' % (corp_name, site_name, from_time, until_time))
        loop = True

        counter = 1
        helper.log_info("Pulling requests from requests API")
        while loop:
            helper.log_info("Processing page %s" % counter)
            # response_raw = requests.get(url, headers=headers,proxies=proxyDict)
            method = "GET"
            response_raw = helper.send_http_request(url, method, parameters=None, payload=None,
                                  headers=headers, cookies=None, verify=True, cert=None, timeout=None, use_proxy=True)
            responseCode = response_raw.status_code
            responseError = response_raw.text

            checkResponse(responseCode, responseError)


            response = json.loads(response_raw.text)


            for request in response['data']:
                data = json.dumps(request)
                helper.log_debug("%s" % data)
                
                if key is None:
                    event = helper.new_event(source=helper.get_input_name(), index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=data)
                else:
                    indexes = helper.get_output_index()
                    curIndex = indexes[key]
                    types = helper.get_sourcetype()
                    curType = types[key]
                    event = helper.new_event(source=helper.get_input_name(), index=curIndex, sourcetype=curType, data=data)

                try:
                    ew.write_event(event)
                except Exception as e:
                    raise e

            if "next" in response and "uri" in response['next']:
                next_url = response['next']['uri']
                if next_url == '':
                    loop = False
                    helper.log_info("Finished Page %s" % counter)
                    counter += 1
                else:
                    url = api_host + next_url
                    helper.log_info("Finished Page %s" % counter)
                    counter += 1
            else:
                loop = False

    multiCheck = helper.get_arg('delta')

    if type (multiCheck) is dict:
        for activeInput in multiCheck:
            delta = int(multiCheck[activeInput])
            allSites = helper.get_arg('site')
            site = allSites[activeInput]
            helper.log_debug("site: %s" % site)
            pullEvents(key=activeInput, curSite=site, delta=delta)
    
    else:
        delta = int(helper.get_arg('delta'))
    	site = helper.get_arg('site')
        helper.log_debug("site: %s" % site)
        pullEvents(site, delta)

    helper.log_info("Finished Pulling events")

