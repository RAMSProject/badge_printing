from os.path import join

from uber.jinja import template_overrides
from uber.utils import mount_site_sections, static_overrides
from .config import badge_print_config
from . import models  # noqa: F401

static_overrides(join(badge_print_config['module_root'], 'static'))
template_overrides(join(badge_print_config['module_root'], 'templates'))

mount_site_sections(badge_print_config['module_root'])
