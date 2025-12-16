import logging

_logger = logging.getLogger(__name__)


def _column_exists(cr, table, column):
    cr.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return bool(cr.fetchone())


def pre_init_hook(cr):
    """Run before module install to add llm_role column.

    Since llm_role is now a direct field (not computed), this just ensures
    the column exists to prevent ORM creation during field registration.
    """
    table = "mail_message"
    column = "llm_role"

    try:
        if not _column_exists(cr, table, column):
            _logger.info("[LLM] Adding %s.%s column before install", table, column)
            cr.execute(f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR")
            _logger.info("[LLM] Column added: %s.%s", table, column)
        else:
            _logger.info("[LLM] Column already exists: %s.%s", table, column)
    except Exception:
        _logger.exception(
            "[LLM] pre_init_hook failed while preparing %s.%s", table, column
        )
        # Allow install to continue; column will be created later by ORM if needed.


def post_init_hook(cr, registry):
    """Run after module install to populate llm_role for existing messages."""
    from odoo.api import Environment

    _logger.info("[LLM] post_init_hook: populating llm_role for existing messages")
    try:
        env = Environment(cr, 2, {})  # uid=2 (usually admin in tests)
        MailMessage = env["mail.message"]
        
        # Get all records with a subtype and populate llm_role
        messages = MailMessage.search([(("subtype_id", "!=", False))])
        if messages:
            _logger.info("[LLM] post_init_hook: updating %d messages with subtypes", len(messages))
            for message in messages:
                message._on_change_subtype_id()
        
        _logger.info("[LLM] post_init_hook: llm_role population complete")
    except Exception:
        _logger.exception("[LLM] post_init_hook failed")
