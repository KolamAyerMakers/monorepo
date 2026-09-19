# Demo your site

Quest: demo-site

## Mission

Give a five-minute demonstration of something you choose from your project. Support the claim with real evidence and explain one real failure and recovery. This is not a mandatory tour of every artifact.

## Choose The Claim

You might show an automatically refreshed report, a reachable page and its service route, your checker's diagnosis and repair, or a source handoff that a peer could operate. Choose evidence that fits, rather than running every command you know.

Prepare in your own classroom account. If you chose an optional Bandit investigation, exit it back to your laptop, then switch to classroom SSH and confirm the account and hostname before project commands. Do not exchange passwords with a peer.

## Five-Minute Shape

| Time | Show |
|---|---|
| 0:00-0:30 | What you chose and why it matters |
| 0:30-3:00 | The result and evidence supporting your claim |
| 3:00-4:30 | A real failure, diagnosis, repair, and recovery evidence |
| 4:30-5:00 | What you learned and one question |

Rehearse once before the protected demo block. Open the pages or logs you will need, and keep credentials out of view. Do not create a risky live failure just to make the presentation dramatic.

## Evidence You Can Use

- Automation: a journal activation after the timer started, without a manual build, plus changed facts in the public report. The pre-start script refreshes facts before npm builds; npm alone does not regenerate the report.
- Serving: a successful local and public request with the expected page body, supported by request logs and an outside browser view. An active unit alone does not prove this.
- Handoff: the README, site source, two scripts, and three units visible in Forgejo, plus the peer's successful operation and an instruction you improved. A local commit listing alone is insufficient.
- Recovery: the actual symptom, observation that narrowed the cause, repair, and response or content proving recovery. Do not replace observed errors with expected successes.

Use the [S10 fallback demo commands](../sessions/S10/self-study.md#demo-script) only when useful for preparation or diagnosis. They include computing the port directly, pausing automation and waiting for a build before body comparisons, checking routes, and restoring the hourly timer. For live automation proof, use [S9's observation procedure](../sessions/S09/self-study.md#witness-automatic-publication) instead of manually starting a service and calling it automatic.

## If Something Fails

Show the failure honestly. A static `404` suggests inspecting source/build/output; a personal URL `502` calls for comparing local reachability, the port, and the service journal. If local service works but public routing fails, collect the evidence for staff rather than changing shared DNS or proxy settings.

If you have no recovered example yet, agree on a safe preparation exercise such as the [owner-operated README test](write-readme.md#peer-operation-test), not an improvised break during your five minutes. If the issue remains unresolved or sessions were missed, agree on a reduced scope, name the missing evidence, and date the recovery action. Recorded evidence can be used when access is unavailable if you state its date and limitations.

## After The Demo

Keep one useful question or observation from the audience. Follow [Write the next path](write-next-path.md) to choose a next action and date; a private note or calendar is sufficient when publishing is not meaningful.

## Related Reading

- [README writing](../concepts/readme-writing.md)
- [Source handoff](prepare-source-handoff.md)
- [S10 self-study](../sessions/S10/self-study.md)
