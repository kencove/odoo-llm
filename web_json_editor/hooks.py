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
    """Run before module install to add llm_role column and index."""
    table = "mail_message"
    column = "llm_role"
    try:
        if not _column_exists(cr, table, column):
            _logger.info("[WEB_JSON_EDITOR] Adding %s.%s column before install", table, column)
            cr.execute(f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR")
            _logger.info("[WEB_JSON_EDITOR] Column added: %s.%s", table, column)
        else:
            _logger.info("[WEB_JSON_EDITOR] Column already exists: %s.%s", table, column)
        index_name = f"{table}_{column}_idx"
        _logger.info("[WEB_JSON_EDITOR] Ensuring index %s on %s(%s)", index_name, table, column)
        cr.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column})")
        _logger.info("[WEB_JSON_EDITOR] Index ensured: %s", index_name)
    except Exception:
        _logger.exception(
            "[WEB_JSON_EDITOR] pre_init_hook failed while preparing %s.%s", table, column
        )
        # Allow install to continue; column will be created later by ORM if needed
        # but the exception is logged for visibility.
