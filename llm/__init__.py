from . import models
from . import wizards
from . import hooks

# Expose pre_init_hook for Odoo installer
from .hooks import pre_init_hook