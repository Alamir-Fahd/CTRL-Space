# User categories

## The four categories (exact copy from the request, stored verbatim)
| Value | Label | Description |
|---|---|---|
| `student` | Student | For university and school students exploring scientific research. |
| `researcher` | Researcher | For people conducting scientific research and studying experiments. |
| `educator` | Educator / Teacher | For teachers and educators using research materials for learning. |
| `other` | Other | For visitors and users with different interests. |

## Where it lives
- **Database**: `users.category` (nullable `TEXT`, validated server-side against the 4 values — no SQL `CHECK` constraint, to keep the same validation path as `bio`/`interests`).
- **Signup**: `frontend/app/js/screens-a.js` `vRegister()` — a `role="radiogroup"` of 4 selection cards (icon + bold label + description, reusing the existing `.pickrow` component so the visual language matches the rest of the app), one required.
- **Edit later**: `frontend/app/js/screens-d.js` `vEditProfile()` — the same card group, pre-selected to the user's current category.
- **Displayed**: `frontend/app/js/screens-c.js` `vProfile()` — replaces what used to be a hardcoded "Researcher" label for every non-admin user with the user's real selected category (a small honesty fix: the old label was the same generic word for every account regardless of who they actually were).

## Personalization — what was and wasn't done
The request listed example personalization ideas per category (e.g. Student → emphasize Learning Studio). **This pass stores and displays the category accurately; it does not hide or reorder any navigation or features by category** — this is intentional, matching the request's own explicit rule: *"Do not hide important features from users based on their category... Keep authorization separate from user category."* Category is informational/personalization-ready data, not a permissions system. Building actual per-category UI emphasis (e.g. a different Home-screen ordering for Researchers vs Students) is a real, separate design decision that wasn't part of what was asked to be *fixed* here — flagging it as a follow-up if wanted, not silently deciding it on your behalf.

## Tests
- `test_signup_category_saved_and_validated` — valid category saved and returned from `/api/auth/me`; invalid value rejected with `422`; omitted category stays optional (not forced).
- `test_category_update_and_rejects_invalid` — `PATCH /api/me` updates it, persists, rejects garbage values.
- `e2e/mobile_app_test.py` registration test — picks "Researcher" in a real browser, confirms it shows on the real Profile page afterward.
