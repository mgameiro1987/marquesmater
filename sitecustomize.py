"""MarquesMater startup hook: synchronize RIDA catalog metadata from the V37 Excel-derived master data and keep Excel imports enriched. It preserves stock and images."""
try:
    import v99_catalog_import_api as importer
    from v9_10_12_rida_enrichment import enrich_existing, enrich_row
    _original_row_payload = importer._row_payload
    def _rida_row_payload(raw):
        return enrich_row(_original_row_payload(raw))
    importer._row_payload = _rida_row_payload
    result = enrich_existing()
    print("RIDA catalog enrichment:", result)
except Exception as exc:
    print("RIDA catalog enrichment skipped:", exc)
