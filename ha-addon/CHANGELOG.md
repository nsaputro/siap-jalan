## 0.3.0

- Added: **Import / Export**: download all active and future trips plus customised activity templates as a JSON file (`GET /export`); restore them on any instance with `POST /import` — activity slug conflicts are auto-resolved and packing lists are preserved exactly as exported (both HA addon and React frontend)
- Changed: Import is now tolerant of partial JSON: optional fields fall back to sensible defaults instead of failing validation, so trimmed or hand-edited export files still import cleanly

---

[Full changelog](https://github.com/nsaputro/siap-jalan/blob/main/CHANGELOG.md)
