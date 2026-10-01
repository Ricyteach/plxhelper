# plxhelper
Plaxis 3D helper scripts.

## Status and notes for picking this back up (2026-10)

`main` is the last state that passes its own test suite (29 tests, excluding the
live-Plaxis tests). Unfinished work from July 2023 is on the `local-work-2023`
branch. It does not import: `helper_metaclasses.py` has a syntax error,
`plaxis_helper.py` imports `D2Point_co` / `D2PointPair_co` that `geo.py` no longer
defines, and `add_pipe_structure` was moved into `pipe_structure.py` but ended up
indented inside `class PipeStructure`. Do not merge it as-is.

The version of this library that built the July 2023 reline job models was never
committed and could not be recovered.

### What is worth keeping

- **Material data in tables (`tsv/`).** Duncan-Selig soils, Ms tables, Weholite
  pipe, plates and live loads as data, selected with calls like
  `material_creator("weholite_pipe", 160, 54.0, "Long", 50)`. Easy to audit.
- **Pipe shapes as plain Python.** `PipeArchProfile` / `RoundShape` produce segment
  data that `add_pipe_structure` turns into Plaxis geometry. The shape side is
  testable without Plaxis.
- **The `@phase(parent)` decorator.** Builds the staged-construction phase tree
  explicitly, which matches how Plaxis phases actually work.
- **`TaskChain`.** Named, resumable model-building steps.

### What to change

1. **Drop the import-time global connection.** `connect_server()` fills
   module-level `s_i` / `g_i`, and `pipe_structure.py` connects just by being
   imported. Pass an explicit session object into the functions instead. This also
   removes the `pipe` -> `plaxis_helper` <- `pipe_structure` import tangle and makes
   mocking straightforward.
2. **Keep geometry free of Plaxis calls.** Shape and coordinate math in pure
   modules with their own tests; a thin layer that issues the `g_i` commands.
3. **Pin the version per job.** Record the plxhelper commit hash or tag in every
   job folder (or vendor a copy). Without it, an old job script cannot be re-run.
4. **Store every object later phases need.** Job scripts kept setup objects as
   locals (host pipe volume, reline plate, interface) and later phases referenced
   them on the shared namespace, or referenced names that were never created
   (`hl93_*` vs `hs25_*`). Have each task return what it creates, or validate the
   namespace before the phase step.
