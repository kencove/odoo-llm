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
    """Run before module install to add user_vote column.

    Pre-creates the user_vote column to avoid ORM creation during field registration,
    which would be slow on large mail_message tables.
    """
    table = "mail_message"
    column = "user_vote"
    try:
        if not _column_exists(cr, table, column):
            _logger.info(
                "[LLM_THREAD] Adding %s.%s column with default value", table, column
            )
            # Add column with default to avoid full table rewrite
            cr.execute(f"ALTER TABLE {table} ADD COLUMN {column} INTEGER DEFAULT 0")
            _logger.info("[LLM_THREAD] Column added: %s.%s", table, column)
        else:
            _logger.info("[LLM_THREAD] Column already exists: %s.%s", table, column)
    except Exception:
        _logger.exception(
            "[LLM_THREAD] pre_init_hook failed while preparing %s.%s", table, column
        )
        # Allow install to continue; column will be created later by ORM if needed
