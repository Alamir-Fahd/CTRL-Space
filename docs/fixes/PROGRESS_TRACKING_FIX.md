# Progress tracking — investigation result

**Finding: the reported problem did not reproduce.** Before changing any code, this was checked against the actual running application, not assumed from the bug description.

## What was checked
- `lesson_progress` table: a real `(user_id, lesson_id)` join table, one row per actual completion, inserted only by `POST /api/lessons/:id/complete` for the signed-in user.
- `GET /api/lessons`: each lesson's `completed` flag is a live `SELECT 1 FROM lesson_progress WHERE user_id=? AND lesson_id=?` — never a default or hardcoded value.
- `GET /api/me`: `lessons_completed` / `challenges_passed` counts are `COUNT(*)` queries scoped to the real signed-in user's ID.
- Frontend (`frontend/app/js/screens-c.js` `vLearn()`): `done / l.items.length * 100` — computed from the real `completed` flags above, not a stored or cached percentage.

## Live verification (not just code reading)
Registered a genuinely new, never-used-before account and checked `/api/lessons` immediately after:
```
Fresh user: 0/5 lessons completed = 0 %
per-lesson completed flags: [False, False, False, False, False]
```
Exactly matches the spec's own stated expectation ("If a user has completed 0 out of 8: Progress = 0%").

## Conclusion
No fix was needed or made here — the existing implementation already satisfies every rule in the original request (real per-user records, 0% for new users, never assumed-complete, no cross-user visibility, correct recalculation, persists across refresh because it's a real database row, not client state). Challenge progress (`challenge_attempts`, scored server-side) follows the identical pattern and was spot-checked the same way.

If a *different* specific screen was showing a misleading percentage that this investigation didn't cover, point to that exact screen and it can be checked the same way — but the two most likely places (Learning Studio completion, and the `/api/me` counts that feed the Profile and Impact Dashboard) are both confirmed accurate.
