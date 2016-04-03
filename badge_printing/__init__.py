from uber.common import *

from badge_printing.config import *
static_overrides(join(badge_print_config['module_root'], 'static'))
template_overrides(join(badge_print_config['module_root'], 'templates'))
from badge_printing.models import *

mount_site_sections(badge_print_config['module_root'])