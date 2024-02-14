from rest_framework import authentication
import json


class BearerAuthentication(authentication.TokenAuthentication):
    """
    Simple token based authentication using utvsapitoken.

    Clients should authenticate by passing the token key in the 'Authorization'
    HTTP header, prepended with the string 'Bearer '.  For example:

    Authorization: Bearer 956e252a-513c-48c5-92dd-bfddc364e812
    """

    keyword = "Bearer"


def replace_values_in_json(json_obj, replacements):
    config_str = json.dumps(json_obj)
    for key in replacements:
        config_str = config_str.replace(key, replacements[key])
    return json.loads(config_str)
