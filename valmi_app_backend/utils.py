from rest_framework import authentication


class BearerAuthentication(authentication.TokenAuthentication):
    """
    Simple token based authentication using utvsapitoken.

    Clients should authenticate by passing the token key in the 'Authorization'
    HTTP header, prepended with the string 'Bearer '.  For example:

    Authorization: Bearer 956e252a-513c-48c5-92dd-bfddc364e812
    """

    keyword = "Bearer"


def replace_values_in_json(json_obj, replacements):
    for key, value in json_obj.items():
        if isinstance(value, dict):
            replace_values_in_json(value, replacements)
        elif key in replacements:
            replacement_value = replacements.get(key)
            if replacement_value is not None:
                json_obj[key] = replacement_value
