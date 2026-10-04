# Preserve training behavior checkpoints

Later Hard snapshots regressed relative to a preserved earlier model. Receipts
currently retain a behavior SHA but the underlying canonical file is overwritten.
Keep the exact input checkpoint for each training batch so a replay can identify
an evaluable model. Do not change actions, rewards, learner math or frozen tests.

1. Add a trainer-level regression for two batches: both games share one immutable
   behavior snapshot per batch, the next batch sees the updated model, receipt
   hashes match retained bytes, and canonical resume state still advances.
2. Before training collection, copy the canonical bytes to a unique batch path.
   Workers load that immutable copy; receipts retain both canonical and behavior
   paths. Keep snapshots for failed batches for diagnosis. Evaluation/random
   modes continue using the user's supplied frozen file without extra copies.
3. Run the complete local suite and short real train/resume/frozen games. Verify
   checkpoint hashes and that candidate/helper scratch cleanup is unchanged.
4. Review and integrate after the currently running curriculum terminates. Use
   retained models to compare future checkpoints rather than relying on the final
   state. Keep known weak models out of the strength acceptance result.

Validation: all 60 unittest checks pass, and an independent read-only review
found no defects. Real DQN and PPO each completed four training games, two
resume games and two frozen evaluation games at a 120-second game limit, with
no failures. All were timeouts, so these verify infrastructure only. DQN resumed
with six episodes/six attempts/672 updates; PPO with six/six/12. Training retained
two batch snapshots and resume retained one, all receipt hashes match retained
bytes, and all replays are nonempty. Frozen evaluation retained no extra history
and left each supplied checkpoint byte-for-byte unchanged. No candidate or
learner scratch files remained. Evidence lives in this worktree's ignored
`logs/history-{dqn,ppo}-{train,resume,eval}/` folders.
