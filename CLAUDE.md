You are a senior Django engineer. Build a production-ready Django web app (Django 5+, Python 3.12) for church facility management focused on doing the basics extremely well: repair requests (work orders) and asset overview.

CRITICAL REQUIREMENTS
1) The entire app must be bilingual:
   - Primary language: Dutch (nl)
   - Secondary language: English (en)
   - Default UI language: Dutch
   - English is fallback where translations are missing
   - Provide a clear language switcher (NL / EN) on every page
   - Use Django i18n properly: gettext, locale files, and translated labels
   - Provide Dutch-first copy. English should be concise.

2) Accessibility & older users (high priority):
   - Use large font sizes (base at least 18px), large clickable areas, high contrast
   - Avoid dense tables; add spacing and clear headings
   - Use plain language, avoid jargon
   - Minimal steps to submit a repair request (target < 60 seconds)
   - Provide a “simple view” layout: one-column, big buttons, few controls
   - Ensure keyboard navigation and screen-reader friendly markup (labels, aria)
   - Meet WCAG AA basics (contrast, focus states, readable forms)

TECH/STACK
- Django + Django templates (no SPA). Use Bootstrap 5.
- Use Django auth and groups/permissions.
- SQLite for dev; Postgres-ready for prod.
- Django admin enabled for power-user management, but provide friendly UI for everyone.

INTERNATIONALIZATION (i18n) DETAILS
- settings.py:
  - LANGUAGES = [("nl", "Nederlands"), ("en", "English")]
  - LANGUAGE_CODE = "nl"
  - USE_I18N = True, LocaleMiddleware enabled
- All user-facing text must be wrapped in gettext_lazy / gettext.
- Provide compiled translation catalogs:
  - locale/nl/LC_MESSAGES/django.po
  - locale/en/LC_MESSAGES/django.po
- Use Dutch-first copy and terminology suitable for a church facilities context.

CORE ENTITIES (models)
1) Location (Locatie)
- name (naam), parent (bovenliggende locatie), notes (notities)

2) Asset (Object / Installatie)
- asset_tag (uniek, bv. "HVAC-01")
- name (naam), category (categorie), location (locatie FK)
- manufacturer, model, serial_number (optioneel)
- install_date (optioneel)
- status (Operationeel, Aandacht Nodig, Buiten Gebruik, Afgevoerd)
- criticality (Laag/Middel/Hoog)
- warranty_end_date (optioneel)
- photo (optioneel), description

3) RepairRequest (Reparatieverzoek / Werkbon)
- title (titel)
- description (omschrijving)
- location (locatie FK)
- asset (optioneel FK)
- priority (Laag/Normaal/Hoog/Spoed)
- status (Nieuw, Getriageerd, Bezig, Wacht, Gereed, Gesloten)
- requester_name (naam melder)
- requester_email (optioneel)
- requester_phone (optioneel)
- preferred_contact_method (Email/Telefoon)
- created_at, updated_at
- assigned_to (FK User, optioneel)
- triaged_by (FK User, optioneel)
- due_date (optioneel)
- resolution_summary (optioneel)
- closed_at (optioneel)
- attachments (meerdere foto’s/bestanden)

4) WorkLog (Logboek / Tijdlijn)
- repair_request (FK)
- author (FK User of nullable voor systeem)
- entry_type (Notitie, Statuswijziging, Toewijzing, Tijdsbesteding)
- note (tekst)
- minutes_spent (optioneel)
- created_at

REQUIRED FEATURES
A) Request submission form (very easy)
- Route: /requests/new
- Keep it short: Titel, Omschrijving, Locatie, (optioneel) Object/Installatie, Prioriteit, Naam melder, (optioneel) Email/Telefoon
- After submit: confirmation page with request ID (Werkbonnummer) + next steps
- Email notification to facilities inbox (configurable)

B) Facilities dashboard (Overzicht)
- Route: /dashboard
- Triage inbox for Nieuw/Getriageerd
- Filters: status, prioriteit, locatie, toegewezen aan
- Quick actions: status wijzigen, toewijzen, due date, interne notitie
- Highlight urgent and overdue items with clear badges (also accessible)

C) Request list and request detail
- /requests/ (facilities sees all; requesters see their own)
- /requests/<id>/ detail page:
  - clear summary
  - big action buttons
  - timeline/logbook
  - attachments upload/download
  - status and assignment history

D) Asset overview
- /assets/ list with filters: locatie, categorie, status, criticality
- /assets/<id>/ detail: fields + open requests + recent work
- CSV import/export for assets (simple mapping)

E) Permissions
- Group "Aanvragers" (Requesters): create requests, view own requests
- Group "Facilitair" (Facilities): view all, triage/assign/update, view assets
- Group "Beheerders" (Admins): full access
- Enforce in views and templates (no hidden-but-accessible actions)

F) Auditability
- Every status change and assignment change automatically creates a WorkLog entry.
- Attachments validated (images/pdf), size limits, safe filenames.

UX REQUIREMENTS (senior-friendly)
- Base font-size >= 18px, big buttons (min height ~44px)
- Large spacing, readable forms, clear error messages
- Avoid long dropdowns when possible; use typeahead only if it stays simple
- Provide “Print” button on request detail and asset detail (printer-friendly CSS)
- Provide simple empty states: what to do next in Dutch-first copy

PAGES / ROUTES
- / (home with two big actions: "Reparatie melden" and "Overzicht")
- /requests/new
- /dashboard
- /requests/
- /requests/<id>/
- /assets/
- /assets/<id>/
- /account/login, /account/logout (or default auth routes)

DELIVERABLES
- Complete Django project with apps: core (locations/assets), requests (repair requests/work logs), accounts/permissions
- Migrations
- Templates with Bootstrap 5, senior-friendly styling
- Tests: permissions, request creation, status transition logging, language switching
- README:
  - setup
  - how to create initial groups and assign users
  - how to generate/compile translations (makemessages/compilemessages)
  - how to set FACILITIES_INBOX_EMAIL and email backend

CONFIG
- Settings: FACILITIES_INBOX_EMAIL, DEFAULT_FROM_EMAIL
- Dev uses console email backend; prod is configurable.

NON-GOALS (not now)
- Inventory/parts, vendor contracts, budgeting, advanced preventive maintenance, multi-tenant

