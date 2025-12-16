import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Add llm_role column and create index efficiently for large databases.

    This migration:
    1. Adds the llm_role column via SQL (prevents Odoo from computing all values)
    2. Creates an index using CONCURRENTLY to avoid blocking

    This avoids the "Prepare computation" step that hangs on large databases.
    """
    _logger.info("Setting up mail_message.llm_role field...")

    try:
        # First check if the column exists
        cr.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'mail_message'
            AND column_name = 'llm_role'
        """)

        if not cr.fetchone():
            _logger.info("Adding llm_role column to mail_message...")
            # Add column as NULL - Odoo will populate it via compute method as records are accessed
            cr.execute("""
                ALTER TABLE mail_message
                ADD COLUMN llm_role VARCHAR
            """)
            _logger.info("✓ Successfully added llm_role column")
        else:
            _logger.info("Column llm_role already exists")

        # Check if index already exists
        cr.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'mail_message'
            AND indexname = 'mail_message_llm_role_index'
        """)

        if cr.fetchone():
            _logger.info("Index mail_message_llm_role_index already exists, skipping")
            return

        # Create index concurrently to avoid blocking
        # Note: This can't be done in a transaction, but Odoo migrations
        # are typically run outside transactions or we can catch the exception
        try:
            _logger.info("Creating index CONCURRENTLY (non-blocking)...")
            cr.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS mail_message_llm_role_index
                ON mail_message (llm_role)
            """)
            _logger.info("✓ Successfully created index on mail_message.llm_role")
        except Exception as e:
            # If CONCURRENTLY fails (e.g., in transaction), fall back to regular CREATE INDEX
            _logger.warning(f"CONCURRENT index creation failed: {e}")
            _logger.info("Falling back to regular index creation...")

            cr.execute("""
                CREATE INDEX IF NOT EXISTS mail_message_llm_role_index
                ON mail_message (llm_role)
            """)
            _logger.info(
                "✓ Successfully created index on mail_message.llm_role (regular)"
            )

    except Exception as e:
        _logger.error(f"Error creating llm_role index: {e}")
        # Don't raise - allow module to install even if index creation fails
        # The index improves performance but isn't strictly required for functionality
