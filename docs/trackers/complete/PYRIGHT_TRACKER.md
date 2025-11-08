## Pyright Type-Check Tracker

_Updated after `hatch run pyright` on 2025-11-08 (0 errors)._ 

### Summary

- Total type errors: **0** across **0** files.
- Config/test constructors, fake repositories, Stripe client/dispatcher typing, and security/persistence edge cases have all been corrected.
- `hatch run pyright` _and_ `hatch run lint` now pass cleanly; re-run both commands after any future typing work to keep this state.

### Notes

- This tracker has been reset now that the backlog is clear. Document any new regressions here with the failing file, rule, and owner so we can keep Pyright at zero.
