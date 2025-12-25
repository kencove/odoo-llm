from . import models
from . import wizards
from . import hooks

# Expose hooks for Odoo installer
from .hooks import pre_init_hook, post_init_hook
