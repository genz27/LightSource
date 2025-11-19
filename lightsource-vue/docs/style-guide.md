# LightSource Admin UI Style Guide

## Language
- All admin interface labels and actions use English.
- Standard terms: Users, Providers, Jobs, Assets, Billing, Wallet.

## Layout & Width
- Admin pages share a unified max width: `var(--container-width, 1200px)`.
- Content is centered via `AdminLayout` and constrained in `.admin-wrap` and `.admin-content`.
- Apply the Jobs page width as the standard for all admin pages.

## Navigation Spacing
- Top navigation (`AppLayout`):
  - `.main-nav` and `.actions` use a base gap of `20px` on all breakpoints.
  - Mobile keeps wrap and center alignment.

## Admin Page Header Spacing
- Section headers in admin pages use `gap: 16px` to avoid crowded controls.
- Applies to Users, Jobs, Providers, Assets, Billing pages.

## Controls & Actions
- Buttons use the `pill` style consistently; primary actions use `.pill.accent`.
- Controls (inputs, selects) maintain consistent padding and radii across pages.
- Avoid inline wallet editing in Users page; wallet details are view-only.
- Providers page allows editing `base_url` and `notes`; billing-related edits are not exposed here.

## Users Editing
- Edit modal fields: `Email`, `Username`, `Role`.
- Saving issues two requests: `PATCH /admin/users/{id}` for email/username, and `PATCH /admin/users/{id}/role`.

## Providers Editing
- Edit modal fields: `base_url`, `notes`.
- Secret management uses the dedicated modal and `PATCH /providers/{name}/secret`.

## Responsive Behavior
- Grids collapse with `auto-fit/minmax` patterns; lists maintain readable gaps.
- Navigation and action bars wrap appropriately on small screens.

## Accessibility
- Ensure actionable controls have clear labels and consistent hit areas.
- Keep text contrast consistent with theme variables.

## Visual Tokens
- Use CSS variables defined by the theme: `--panel`, `--border`, `--text`, `--muted`, `--accent`, `--pill`.

## Change Log
- Users: Added edit modal; wallet editing removed; labels normalized to English.
- Providers: Added edit modal for `base_url` and `notes`; labels normalized.
- Billing: Row actions kept to `Open` and `Edit`; labels normalized.
- Navigation: Increased spacing to reduce crowding.
- Width: Standardized to the Jobs page across admin pages.