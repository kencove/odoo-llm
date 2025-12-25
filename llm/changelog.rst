16.0.1.4.2 (2025-12-15)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] **CRITICAL** Fixed module hanging during upgrade on large databases
* [IMP] Changed llm_role index creation from ORM to SQL migration script
* [IMP] Index now created using CONCURRENTLY to avoid blocking operations
* [IMP] Safe for databases with millions of mail_message records
* [DOC] Added migration performance notes for large database deployments

16.0.1.4.1 (2025-11-17)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Fixed wizard_id not being set on llm.fetch.models.line records
* [IMP] Refactored model fetching: moved logic from wizard default_get() to provider action_fetch_models()
* [IMP] Moved _determine_model_use() from wizard to provider for better extensibility
* [REM] Removed wizard write() override workaround
* [ADD] Comprehensive docstrings with extension pattern examples
* [ADD] Documented standard capability names and priority order

16.0.1.1.0 (2025-03-06)
~~~~~~~~~~~~~~~~~~~~~~~

* [ADD] Tool support framework in base LLM models
* [IMP] Enhanced provider interface to support tool execution
* [IMP] Updated model handling for function calling capabilities

16.0.1.0.0 (2025-01-02)
~~~~~~~~~~~~~~~~~~~~~~~

* [INIT] Initial release of the module
