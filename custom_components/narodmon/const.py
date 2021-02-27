#
#  Copyright (c) 2021, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)
#
"""
The NarodMon.ru Cloud Integration Component.

For more details about this sensor, please refer to the documentation at
https://github.com/Limych/ha-narodmon/
"""

# Base component constants
VERSION = "dev"
ISSUE_URL = "https://github.com/Limych/ha-narodmon/issues"

DOMAIN = "narodmon"

CONF_APIKEY = "apikey"

DEFAULT_NAME = "NarodMon"
DEFAULT_SCAN_INTERVAL = 180
DEFAULT_VERIFY_SSL = True
DEFAULT_TIMEOUT = 10
