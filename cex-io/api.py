#!/usr/bin/env python
# -*- coding: utf-8 -*-

# cex-io.api.py - Python wrapper around the CEX.io API.
# Copyright (C) 2014  István Gazsi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import requests
import hmac
import hashlib
from functools import wraps


class CEXApi(object):

    __api_url = "https://cex.io/api/"

    @staticmethod
    def nonce():
        return str(int(time.time() * 1000))

    @staticmethod
    def signature(username, api_key, api_secret, nonce):
        message = nonce + username + api_key
        return hmac.new(api_secret, msg=message, digestmod=hashlib.sha256).hexdigest().upper()

    @staticmethod
    def parse_return(return_value):
        string = None
        dictionary = None

        if isinstance(return_value, (tuple, list)):
            string, dictionary = return_value
        elif isinstance(return_value, dict):
            dictionary = return_value
        elif return_value:
            string = str(return_value).strip('/')

        return string, dictionary


    @classmethod
    def request_url(cls, path):
        return '%s/%s/' % (cls.__api_url.rstrip('/'), path.strip('/'))

    @classmethod
    def get(cls, path, callback=None):
        def get_decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                get_url = cls.request_url(path)
                get_input = f(*args, **kwargs)

                url_ext, get_params = cls.parse_return(get_input)
                if url_ext:
                    get_url = '%s/%s/' % (get_url.rstrip('/'), url_ext)

                r = requests.get(url=get_url, params=get_params, verify=True)

                print(r.url)

                if r.status_code == requests.codes.ok:
                    return r.json()
                else:
                    return None
            return decorated_function
        return get_decorator

    @classmethod
    def post(cls, path, callback=None):
        def post_decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                post_url = cls.request_url(path)
                post_input = f(*args, **kwargs)

                url_ext, post_data = cls.parse_return(post_input)
                if url_ext:
                    post_url = '%s/%s/' % (post_url.rstrip('/'), url_ext)

                r = requests.post(url=post_url, data=post_data, verify=True)

                print(r.url)

                if r.status_code == requests.codes.ok:
                    return r.json()
                else:
                    return None
            return decorated_function
        return post_decorator

    @classmethod
    def private(cls, f):
        @wraps(f)
        def decorated_function(instance, *args, **kwargs):
            post_input = f(instance, *args, **kwargs)

            url_ext, post_data = cls.parse_return(post_input)

            username, api_key, api_secret = instance._username, instance._api_key, instance._api_secret
            nonce = cls.nonce()
            signature = cls.signature(username, api_key, api_secret, nonce)

            private_data = {
                'key':       api_key,
                'nonce':     nonce,
                'signature': signature
            }
            if post_data:
                post_data.update(private_data)
            else:
                post_data = private_data

            return url_ext, post_data
        return decorated_function


class CEX(object):

    """docstring for CEX"""
    def __init__(self, username=None, api_key=None, api_secret=None):
        super(CEX, self).__init__()
        self._credentials(username, api_key, api_secret)

    def _credentials(self, username=None, api_key=None, api_secret=None):
        self._username = username
        self._api_key = api_key
        self._api_secret = api_secret

    @CEXApi.get('/ticker/')
    def ticker(self, pair='GHS/BTC'):
        return pair

    @CEXApi.get('/order_book/')
    def order_book(self, pair='GHS/BTC'):
        return pair

    @CEXApi.get('/trade_history/')
    def trade_history(self, pair='GHS/BTC', since=10):
        return pair, {'since': since}

    @CEXApi.post('/balance/')
    @CEXApi.private
    def balance(self):
        return

    @CEXApi.post('/open_orders/')
    @CEXApi.private
    def open_orders(self, pair='GHS/BTC'):
        return pair

    @CEXApi.post('/place_order/')
    @CEXApi.private
    def place_order(self, order_type, order_amount, order_price, pair='GHS/BTC'):
        return pair, {'type': order_type, 'amount': order_amount, 'price': order_price}

    @CEXApi.post('/cancel_order/')
    @CEXApi.private
    def cancel_order(self, order_id):
        return {'id': order_id}
