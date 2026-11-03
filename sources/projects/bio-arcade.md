# Bio Arcade series

- ORIGIN | Started as an Anthropic-Courses-style lesson+video+quiz for Arkansas undergraduates under AR INBRE. After early feedback that the format was too passive, pivoted into six mobile-first browser games where the game mechanic *is* the biology, not decoration on top of it.

- SIX GAMES | Polymerase Runner (transcription, base pairing, T→U at the transcription zone). Ribosome Snake (translation, codons AUG → stop, release factors at UAA/UAG/UGA). Fold-Tris (hydrophobic effect, misfolding, chaperones). Phagocyte Patrol (phagocytosis, opsonization, innate + adaptive together). Drug Flight (pharmacokinetics, therapeutic window, hepatic/renal clearance). Lysis Lab (wall-targeting antibiotics, β-lactamase, clavulanate).

- LOOP | Every game follows the same three-step loop: Learn (flashcard) → Play (the mechanic is the concept) → Check (6-question quiz, pass at 5). The loop is the pedagogically defensible unit, not the games individually — that distinction matters for IP and for funding reviewers.

- MOBILE FIRST | Students mostly play on phones, so every game is single-file HTML, phone-friendly, under 6 minutes per module. The constraint "one concept per game, defensible to a reviewer" has been a better teacher of scientific communication than any paper I've written.

- CANVAS TEXT GOTCHA | Early Polymerase Runner rendered all HUD text inside the canvas. Looked fuzzy on retina phones. Rebuilt so HUD text lives in HTML, canvas handles only the game mechanic. Added devicePixelRatio-aware canvas sizing. Lesson: canvas is for the thing that moves; HTML is for the thing that reads.

- DARK MODE MISMATCH | Live GitHub Pages looked different from local testing. Spent an hour hunting a CSS-path bug that didn't exist. Actual cause: macOS dark appearance was auto-switching the arcade pages to a charcoal theme while the main site stayed cream. Fix: pinned every arcade page to light mode via `data-theme="light"` on `<html>`. Lesson: when "it works locally but not deployed," check the viewer's OS, not just the build.

- JUMP SPACING | Obstacle spacing in Polymerase Runner was tight enough that reaction time wasn't the game — it was luck. Playtested with students, widened the gaps, added tunable URL/console parameters for speed and board height so I can retune without redeploying.

- QUIZ CAROUSEL | First draft showed all 6 quiz questions at once. Students either overran or gave up. Rebuilt as a one-question-at-a-time carousel; completion rates went up visibly. The all-at-once version was faster to build and wrong.

- NAMED SIMPLIFICATIONS | Every game states its own simplifications in-game ("the ribosome does not actually look like a snake"). Not an afterthought — this is what makes the games defensible to NIH/ODSS/NSF reviewers who worry that gamified biology teaches wrong intuitions.

- OPEN AND SEPARATE | Hub lives at kalyanidhusia.github.io/student_training/, arcade at kalyanidhusia.github.io/bio-arcade/. Kept as separate repo so the IP conversation (BioVentures, Zenodo DOI, licensing) can happen later without entangling the main site. The gameplay loop is the defensible contribution, not the games.

- FUNDING LINE | Released under AR INBRE, supported by NIH NIGMS P20 GM103429. Educational content, not medical advice. Reviewers can trace the artifact to the grant that funded it.

- TELEMETRY QUESTION | Open design question: a zero-PII telemetry layer that both serves NIH/ODSS evaluation metrics *and* becomes a student data-analysis exercise. The data students generate playing the games becomes the data they analyze — a loop worth building if it holds up.
