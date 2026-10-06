# Connect saved spatial observations to human imitation

Goal: the learner must receive the saved terrain and fog-safe map information, rather than coordinates alone. The target audit found 390/2302 human points in hidden/fogged pixels, so preserve all target candidates.

First implementation: reuse the existing native grid decoder; encode all pixels of each eight-tile candidate cell for terrain height, pathing, placement, visibility and creep, with a padding mask for partial edge cells and normalized coordinates. Preserve exact raw cell coverage; no target-specific feature insertion or legality mask. These five grids are the first spatial integration, not completion of effects/radar or the final observation interface.

- [x] Test native orientation, binary/byte images, cell-edge padding, pixel sensitivity and identical candidate coverage.
- [ ] Add a learned shared spatial embedding to point ranking and global command context; analytic gradients, checkpoint compatibility, explicit opt-in trainer flag and source bindings. Keep legacy outputs unchanged.
- [ ] Check representative memory/compute costs before a frozen supervised run. Same split/seed/budget; diagnose field-level errors and compare full commands. No RL or native promotion merely from a sensory implementation.

Do not edit fit04's bound production files while its handle32360 is live. The new spatial utility and tests can be developed independently. Wait for fit04's terminal report and checkpoint comparison before connecting it to the current model. Professional demonstration extraction and the full micro/Hard/higher-difficulty roadmap remain open.

Preparatory utility `src/learning/entity_spatial.py` reuses the decoder without modifying fit04's bound files. Each candidate has two coordinates, all 8x8x5 grid pixels and an 8x8 validity mask (386 floats). Tests were observed failing before implementation; all232 tests now pass in9.904s, Ruff/diff checks green. Profile receipt `logs/roadmap/spatial-patch-profile-01.json`: estimated whole-teaching feature payload3178146440bytes, not RSS; per-game sampled conversion3.51-5.57ms, isolated float32 32-wide embedding plus weight-gradient0.110-0.144ms/call with two BLAS threads. This is not complete-policy throughput. No fitted model consumes the new utility yet; connection and gradient checks remain open.
