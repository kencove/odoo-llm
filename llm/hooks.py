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
    """Run before module install to add llm_role column and index.

    Since llm_role is now a direct field (not computed), this ensures
    the column and index exist before ORM field registration.
    This prevents expensive operations during module installation on large tables.
    """
    table = "mail_message"
    column = "llm_role"
    index = "mail_message_llm_role_index"

    try:
        if not _column_exists(cr, table, column):
            _logger.info("[LLM] Adding %s.%s column before install", table, column)
            cr.execute(f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR")
            _logger.info("[LLM] Column added: %s.%s", table, column)
        else:
            _logger.info("[LLM] Column already exists: %s.%s", table, column)

        # Add index for performance (CONCURRENTLY to avoid locks)
        cr.execute(
            """
            SELECT 1
            FROM pg_indexes
            WHERE tablename = %s AND indexname = %s
            """,
            (table, index),
        )
        if not cr.fetchone():
            _logger.info("[LLM] Creating index %s on %s.%s", index, table, column)
            cr.execute(
                f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index} ON {table} ({column})"
            )
            _logger.info("[LLM] Index created: %s", index)
        else:
            _logger.info("[LLM] Index already exists: %s", index)

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

        # Get LLM role mappings
        id_to_role, _ = MailMessage.get_llm_roles()

        if id_to_role:
            _logger.info(
                "[LLM] post_init_hook: updating messages with SQL for performance"
            )

            # Use direct SQL UPDATE for each role to avoid ORM overhead on large tables
            for subtype_id, role in id_to_role.items():
                cr.execute(
                    """
                    UPDATE mail_message
                    SET llm_role = %s
                    WHERE subtype_id = %s AND (llm_role IS NULL OR llm_role != %s)
                    """,
                    (role, subtype_id, role),
                )
                if cr.rowcount:
                    _logger.info(
                        "[LLM] Updated %d messages with role '%s'", cr.rowcount, role
                    )

        _logger.info("[LLM] post_init_hook: llm_role population complete")
    except Exception:
        _logger.exception("[LLM] post_init_hook failed")
