## 0.2.2

- Added: Two new built-in activity templates: **Essentials** (👕) with 14 clothing and personal items (t-shirts, underwear, socks, trousers, wallet, phone, medication, etc.) and **Toiletries** (🧴) with 15 hygiene items (toothbrush, toothpaste, shampoo, soap, deodorant, face wash, etc.); both appear at the top of the template list as universal trip additions
- Added: Essentials and Toiletries are pre-selected by default when creating a new trip (both HA addon and React frontend)
- Fixed: Built-in activity templates: replaced locale-specific abbreviations with generic English equivalents — "Passport / KTP" → "Passport / ID Card" (Flight template), "Car registration / STNK" → "Car registration documents" (Road Trip template)
- Fixed: Template item editor: essential star (★) now turns gold/amber when toggled on, making the state visually distinct; also replaced `classList.toggle(force)` with explicit `add`/`remove` for cross-browser reliability (Safari)

---

[Full changelog](https://github.com/nsaputro/siap-jalan/blob/main/CHANGELOG.md)
