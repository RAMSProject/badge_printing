from sideboard.lib import parse_config

from uber.config import c

badge_print_config = parse_config(__file__)
c.include_plugin_config(badge_print_config)
