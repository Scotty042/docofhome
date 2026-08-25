# Sprint 0008 – Usability, module settings, visuals, and archive

## Scope

- Display the running application version in the footer.
- Allow modules to be shown or hidden in the navigation without deleting data.
- Increment inventory numbers from the Asset editor.
- Select Asset-Type icons visually instead of entering MDI names manually.
- Store one optional product image URL and reuse it for assigned Assets.
- Add explanatory hints for settings, master data, products, and Assets.
- Provide a central read-only archive for Assets, electrical distributions, and protective devices.

## Archive behavior

Archiving remains a soft delete. The record keeps its UUID, Tectoryn code, timestamps,
relationships, and historical electrical placement. Archived records are excluded from normal
active selections but remain visible through the permanent **Archiv** navigation item.

The archive contains three views:

- Assets, with a read-only detail page.
- Electrical distributions, with their historical detail page.
- Protective devices, including their original distribution, area, row, module position, and
  archive timestamp when those values are known.

Asset and electrical overview pages also offer an **Archivierte anzeigen** switch. Archived
records are visually marked and cannot be edited, replaced, or archived again.

## Restore policy

Restore is intentionally not part of this sprint. A safe restore workflow must first verify:

- whether the Asset or electrical role has already been replaced,
- whether its original code and identity are still valid,
- whether its original distribution, field, area, row, and module position still exist,
- whether the former module positions are now occupied,
- whether the original location and dependent references are active.

Until these checks exist, archive access is read-only.

## Compatibility

Migration `0009` is additive. Existing installations retain current module visibility and all
existing products remain valid without an image. The archive feature uses existing soft-delete
columns and therefore requires no additional database migration.
