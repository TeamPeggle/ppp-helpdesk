from __future__ import print_function
import json
import os
from functools import cache


def get_namespaced_env(prefix, obj):
    return {
        key[len(prefix) + 2:]: value
        for key, value in obj.items()
        if key.startswith(prefix + '__')
    }


def get_namespaces(env_dict):
    return set(
        name.split('__')[0]
        for name in env_dict.keys()
        if len(name.split('__')) > 1
    )


def get_keys(env_dict):
    return [
        name
        for name in env_dict.keys()
        if len(name.split('__')) == 1
    ]


def parse_env_list(value):
    if value is None or len(value) == 0:
        return []

    try:
        json_value = json.loads(value)
        if isinstance(json_value, list):
            return [
                str(x)
                for x in json_value
            ]
    except json.JSONDecodeError:
        pass

    return value.split(",")


def parse_api_keys_from_env(env_dict):
    api_keys = {}

    for namespace in get_namespaces(env_dict):
        api_keys[namespace.lower()] = parse_api_keys_from_env(
            get_namespaced_env(namespace, env_dict)
        )

    for key in get_keys(env_dict):
        api_keys[key.lower()] = env_dict[key]

    return api_keys


def parse_connection_from_env(env_dict):
    connection = {
        "nick": env_dict.get("NICK"),
        "user": env_dict.get("USER"),
        "realname": env_dict.get("REALNAME"),
        "mode": env_dict.get("MODE"),
        "server": env_dict.get("HOST"),
        "ssl": env_dict.get("SSL"),
        "port": env_dict.get("PORT"),
        "server_password": env_dict.get("PASSWORD"),
        "channels": parse_env_list(env_dict.get("CHANNELS")),
        "nickserv_name": env_dict.get("NICKSERV_NAME"),
        "nickserv_password": env_dict.get("NICKSERV_PASSWORD"),
        "nickserv_command": env_dict.get("NICKSERV_COMMAND"),
        "censored_strings": parse_env_list(env_dict.get("CENSORED_STRINGS")),
        "admins": parse_env_list(env_dict.get("ADMINS")),
    }

    return {
        key: value
        for key, value in connection.items()
        if value is not None and len(value) > 0
    }


def parse_connections_from_env(env_dict):
    return {
        name.lower(): parse_connection_from_env(
            get_namespaced_env(name, env_dict)
        )
        for name in get_namespaces(env_dict)
    }


def parse_config_from_env(env_dict):
    return {
        "connections": parse_connections_from_env(
            get_namespaced_env("CONNECTIONS", env_dict)
        ),
        "prefix": env_dict.get("PREFIX", "."),
        "disabled_plugins": parse_env_list(
            env_dict.get("DISABLED_PLUGINS")
        ),
        "disabled_commands": parse_env_list(
            env_dict.get("DISABLED_COMMANDS")
        ),
        "acls": {},
        "api_keys": parse_api_keys_from_env(
            get_namespaced_env("API_KEYS", env_dict)
        ),
        "censored_strings": parse_env_list(
            env_dict.get("CENSORED_STRINGS")
        ),
    }


@cache
def get_config_from_env():
    env_dict = get_namespaced_env("SKYBOT", os.environ)

    if not env_dict:
        return None

    return parse_config_from_env(env_dict)


def find_config_file():
    file_from_env = os.environ.get("SKYBOT_CONFIG")

    if file_from_env:
        return file_from_env

    # for backwards compatibility, look for either 'config' or 'config.json'
    if os.path.exists("config"):
        return "config"

    if os.path.exists("config.json"):
        return "config.json"

    return None


@cache
def load_config_from_json(filename, _):
    try:
        configuration = json.load(open(filename))
        return configuration
    except json.JSONDecodeError:
        return None


def get_config_from_json():
    config_filename = find_config_file()

    if config_filename is None:
        return None

    # reload config from file if file has changed
    config_mtime = os.stat(config_filename).st_mtime
    return load_config_from_json(config_filename, config_mtime)


def apply_config(bot, config_dict):
    bot.config = config_dict

    for name, connection_config in config_dict["connections"].items():
        if name in bot.conns:
            bot.conns[name].set_conf(connection_config)
        else:
            if connection_config.get("ssl"):
                bot.conns[name] = SSLIRC(connection_config)
            else:
                bot.conns[name] = IRC(connection_config)


last_config = None


def config():
    global last_config

    env_config = get_config_from_env()
    json_config = get_config_from_json()

    active_config = env_config if env_config is not None else json_config

    if last_config == active_config:
        return

    last_config = active_config
    apply_config(bot, active_config)
