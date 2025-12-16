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

    This prevents Odoo from preparing computation for a new stored field
    across the entire mail_message table on first install.
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

        # Create index concurrently when possible
        index_name = f"{table}_{column}_idx"
        _logger.info("[LLM] Ensuring index %s on %s(%s)", index_name, table, column)
        try:
            cr.execute(
                f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} ON {table} ({column})"
            )
            _logger.info("[LLM] Index ensured concurrently: %s", index_name)
        except Exception:
            # Fallback without concurrently (older PG or transaction context)
            _logger.warning(
                "[LLM] Concurrent index creation failed; attempting regular creation"
            )
            cr.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column})")
            _logger.info("[LLM] Index ensured: %s", index_name)
    except Exception:
        _logger.exception(
            "[LLM] pre_init_hook failed while preparing %s.%s", table, column
        )
        # Allow install to continue; column will be created later by ORM if needed
        # but the exception is logged for visibility.
