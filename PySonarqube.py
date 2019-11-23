#!/usr/bin/env python

__author__ = "Anand Tiwari (http://twitter.com/anandtiwarics)"
__contributors__ = ["Anand Tiwari"]
__status__ = "Production"
__license__ = "MIT"

import requests
import json
from requests.auth import HTTPBasicAuth


class SonarqubeAPI(object):
    def __init__(self, host, port, user, password):

        self.host = host
        self.port = port
        self.user = user
        self.password = password

    def projects(self):
        """
        :return: Information about all active projects.
        """
        return self._request('GET', '/api/projects/search')

    def issues(self, project_key):
        """

        :return:
        """
        return self._request('GET', '/api/issues/search?componentKeys=%s&types=%s' % (project_key, 'VULNERABILITY'))

    def _request(self, method, url, params=None, headers=None):
        """Common handler for all the HTTP requests."""
        if not params:
            params = {}

        # set default headers
        if not headers:
            headers = {
                'accept': '*/*'
            }
            if method == 'POST' or method == 'PUT':
                headers.update({'Content-Type': 'application/json'})
        try:
            response = requests.request(method=method, url=self.host + ':' + self.port + url,
                                        auth=HTTPBasicAuth(self.user, self.password))

            try:
                response.raise_for_status()

                response_code = response.status_code
                success = True if response_code // 100 == 2 else False
                if response.text:
                    try:
                        data = response.json()
                    except ValueError:
                        data = response.content
                else:
                    data = ''

                return SonarqubeResponse(success=success, response_code=response_code, data=data)
            except ValueError as e:
                return SonarqubeResponse(success=False, message="JSON response could not be decoded {}.".format(e))
            except requests.exceptions.HTTPError as e:
                if response.status_code == 400:
                    return SonarqubeResponse(success=False, response_code=400, message='Bad Request')
                else:
                    return SonarqubeResponse(
                        message='There was an error while handling the request. {}'.format(response.content),
                        success=False)
        except Exception as e:
            return SonarqubeResponse(success=False, message='Eerror is %s' % e)


class SonarqubeResponse(object):
    """Container for all sonarqube REST API response, even errors."""

    def __init__(self, success, message='OK', response_code=-1, data=None):
        self.message = message
        self.success = success
        self.response_code = response_code
        self.data = data

    def __str__(self):
        if self.data:
            return str(self.data)
        else:
            return self.message

    def data_json(self, pintu=False):
        """Returns the data as a valid JSON String."""
        if pintu:
            return json.dumps(self.data, sort_keys=True, indent=4, separators=(',', ': '))
        else:
            return json.dumps(self.data)
