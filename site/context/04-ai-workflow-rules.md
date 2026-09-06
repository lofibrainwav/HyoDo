# 04 AI workflow rules

The order is Spec → Plan → Build → Review. Do not skip a step and do not
combine steps to save time.

1. **Spec**: state what the change must do and what it must not do, with
   acceptance checks that a script can run (`npm run build`, Lighthouse
   budget, reduced-motion screenshot).
2. **Plan**: list files touched and the order of work. One feature at a
   time. The hero scene, the scroll motion, and the fallbacks are three
   features, not one.
3. **Build**: implement the smallest slice that can be verified, verify it,
   then continue. Keep the page usable at every step.
4. **Review**: run the build, open the page, check the console for errors,
   check `prefers-reduced-motion`, check a 375px viewport, and record the
   result in `06-progress.md` before declaring the slice done.

Rules that override convenience:

- Never report a step as done without the command output that proves it.
- Never add a dependency without writing why in `02-architecture.md`.
- Never put a claim on the page that the repository does not measure.
- When a decision is a matter of taste (color, motion feel, copy tone), stop
  and ask the owner instead of guessing.
