# Original book: independent editorial review

This review concerns the original SVG book only. No purchased artwork was loaded.
The author-inspired lenses are independent agent critiques, not actual author
participation or endorsement. The beginner lens is a simulation, not a user study.

## Review status

| Lens | Status |
| :--- | :--- |
| Linux correctness | Complete; no critical defect, operational/safety corrections required |
| Teaching quality | Complete; five blocking example/recovery defects |
| Julia Evans-inspired visual explanation | Complete; concrete mechanisms and output examples need strengthening |
| Tim Urban-inspired composition | Complete; takes priority in composition conflicts |
| Simulated beginner | Complete; missing context and incomplete examples identified |

## Beginner findings to reconcile

- Make examples runnable and distinguish typed commands, file contents and output:
  reading tools need filenames; redirection and loops must not contain unexplained
  ellipses; append examples need complete pipelines; show a complete restart.
- Clarify Git staging chronology, tracked/untracked files, fetch versus working
  files, and the location, spelling and pattern syntax of `.gitignore`.
- Define home, arguments, Bash/interpreter, permission triplets and directory
  operations before depending on the terms.
- Explain HTTP client, GET/HEAD, header values and URL paths; distinguish illustrative
  404 responses from the actual URL's expected response.
- Define demo prerequisites and syntax (`$HOME`, `&&`, ports/listening), unit
  working directory/startup roles, and the service start limit.
- Make the remote-shell operation explicit, explain returning with `exit`, and
  mention server authenticity verification.
- Reconcile code-typography reports against the latest SVGs: several quoted tokens
  were already corrected before the review; others remain to fix.

All five reviewers reported reading all 55 manifest sources and all twelve contact
sheets. Full-page render inspection varied by reviewer; the Evans- and
Urban-inspired reviewers inspected all 55 PNGs. Their critiques agree on the
consequential defects below. Five disjoint correction batches are complete;
the combined proof has been regenerated and inspected.

## Technical and composition findings to reconcile

The Linux and Urban-inspired reviewers independently confirm the beginner's
main findings. Required fixes include SSH host verification, file-reading inputs,
quoting as data rather than an executable command, false-test wording, matching
the illustrated HTTP status to the requested URL, configured-remote prerequisites,
and clearing a service start limit before restarting.

Urban-inspired priorities add real directory contents instead of an unexplained
door metaphor, a visible staging timeline and commit labels, stream-number
definitions, plain client/port definitions, and moving Python installation away
from the general client/server explanation. Remaining slogan titles and code
fragments need the same whole-book treatment. Existing margins and the revised
mkdir/touch/package pages were positively assessed.

The Evans-inspired review confirms the same misleading examples and calls for
more visible input, output and state changes. Its additional requests for diagrams
and outputs are to be reconciled with Urban's preference for useful brevity:
command tables are acceptable where they explain a real distinction; decoration
and unexplained metaphor are not. All extracted text bounds met the 10 mm rule.

## Reconciled correction plan

| Batch | Scope | Required corrections |
| :--- | :--- | :--- |
| Foundations | Terminal, paths, files, ownership and permissions | Complete reading inputs; typed-command/output labels; Tab completion; home definition; no decorative file legs; actual directory entries; permission-category rules; scoped chmod reversal; save warning. |
| Git | Repository, staging, commit, ignore, remote | Define vocabulary; show stage/edit/stage-again chronology; full commit example; meaningful commit timeline; lowercase `.gitignore` and decoded pattern; fetch does not change working files; configured push destination. |
| Scripts/processes | Bash and running programs | Quoting is data, not printing; define arguments and interpreters; show results; distinguish failed regular-file test from absence; runnable loops; traces versus output; separate process launches and signal targets. |
| Networks/SSH | Network layers, HTTP, local server, remote shell | Verify SSH host identity and explain exit; define client/address/port; actual header values and URL paths; matching HTTP-status examples; complete process/port/page diagnostics; decode guarded local-server setup. |
| Streams/services | Streams, pipes, redirection, tee and user services | Explain identifiers and routing; complete overwrite/append examples; sorting/counting definitions; unit fields and manager scope; actual observations/log following; optional linger policy; reset start limit before restart. |

### Composition decisions

- Retain compact command tables where they answer a useful comparison; the
  Urban-inspired review explicitly accepts them. Add small state/output examples
  where a table or metaphor alone leaves the operation unclear. Do not turn every
  page into a long narrative or add decoration just to resemble an author.
- Keep examples standalone. HTTP's general request page must not silently require
  a server introduced later. A hypothetical response must be labelled hypothetical;
  an operational demonstration must state its server/file prerequisites.
- Preserve generic home-Linux scope, loopback safety, user-manager availability
  and conditional logout policy. Do not erase prerequisites to make pages shorter.
- Reconcile reports against current sources: some monospace fragments had already
  been fixed during review. Apply the typography rule to every remaining literal
  token rather than repeating already-applied changes.

## Final correction outcome

- Git batch complete: five assigned SVGs rendered and inspected by its worker,
  then inspected again during integration. Staging now shows stage → edit →
  stage-again, commits are snapshots, `.gitignore` is literal lowercase with a
  decoded pattern, and remotes explain fetched history versus working files.
  Integration separated the two distro installation lines to remove a collision.
- Scripts/processes batch complete: eight SVGs rendered and inspected by its
  worker and again during integration. Scripts show results, quoting includes
  a full literal-print example, argument flow is explicit, tests distinguish
  non-regular files from missing paths, loops are complete, traces differ from
  output, and process launches/signals have clear targets.
- Network/SSH batch complete: twelve SVGs rendered and inspected by its worker,
  then all twelve inspected during integration. HTTP's 404 is explicitly a
  hypothetical response, the request example has no later-server dependency,
  SSH includes identity verification and exit, and diagnostics show complete
  commands and selected evidence. Integration added the local server's explicit
  served-directory/page purpose and fixed its inline keyboard typography.
- Foundations batch complete: eighteen SVGs rendered and inspected by its worker;
  all integrated pages inspected in the chapter sheets. Reading commands name
  an existing file; definitions, key completion, save warnings and actual
  before/after drawings are present. Permission categories are alternatives,
  directory entries replace the door metaphor, and owner highlights align.
- Streams/services batch complete: twelve SVGs rendered and inspected by its
  worker; integrated chapter sheets inspected, with full-page inspection of the
  annotated unit and recovery page. Streams have named identifiers and routing;
  pipelines are complete; service states, logging and logout policy have visible
  evidence. Conditional start-limit reset precedes the full restart command.
- Final integration regenerated all 55 manifest pages, twelve chapter contact
  sheets, twelve PDF bookmarks and the three-page sample. All twelve sheets were
  inspected. The last ignore-page safety sentence was moved inside the required
  margin, and the repair-page title and final annotation spacing were corrected
  and re-rendered. Minimum extracted text margin: **10.47 mm**.
- Reported defects are addressed; optional requests for more diagrams were
  reconciled with the Urban-inspired preference for compact useful explanations.
  No lesson commands, remote access, purchased-art loading, commits or pushes
  were performed. Actual-size reading approval and printer specifications remain
  outside this editorial review.

## Complementary edition

User-approved additions cover all six high-value topics and all five second-tier
topics proposed after the initial review. Fourteen new source pages cover eleven
topics without squeezing distinct concepts into one page:

- Text search with `grep` and path search with `find`.
- Quoted filenames and shell wildcard expansion, on separate pages before file
  operations that could otherwise misinterpret the reader's filenames.
- General exit status and conditional commands; child-process environment
  inheritance and `PATH` lookup, each with its own mechanism diagram.
- Safe Git recovery: unstaging preserves working edits; explicit last-commit
  restoration can erase working edits and must carry an adjacent warning.
- Filesystem capacity versus directory usage, recursive directory copying,
  symbolic links, interactive foreground/background jobs, and independent backups
  versus same-disk Git history.

`contents.toml` places these by prerequisite, not by their new source directory.
The complementary edition has 69 pages across thirteen chapters. All fourteen
pages were rendered and inspected by their drawing workers and then individually
inspected during integration. Integration corrected a failed regular-file test's
wording, brought Git footers inside the safe margin, aligned chapter ordinals and
replaced a backup guarantee with a factual concept title. All 69 manifest pages
have been exported with thirteen bookmarks and contact sheets; minimum extracted
text margin is 10.47 mm.

| Complementary review lens | Status |
| :--- | :--- |
| Linux correctness | Complete; focused confirmation resolves both findings, no new material defect |
| Teaching quality | Complete; corrections applied |
| Julia Evans-inspired visual explanation | Complete; corrections applied |
| Tim Urban-inspired composition | Complete; focused confirmation resolves all findings; stylistic priority |
| Simulated beginner comprehension | Complete; corrections applied |

The 55-page review outcome above is historical evidence, not approval of new pages.

### Reconciled complementary findings

- Linux: define shell assignment, value expansion and quoted values locally on
  the exit-status/environment pages, before those examples depend on them.
- Linux: staging ends with the edit selected; the next commit page must show an
  empty unstaged diff and the added line in the staged diff if it promises a
  continuation. Preserve this chronology rather than quietly restarting it.
- Urban-inspired: confirms both variable-context gaps. Optional refinements
  clarify independent conditional examples, show where PATH lookup stops, label
  the original directory's before/after state, name the unstaging source, replace
  the child metaphor with child programs, and qualify the same-disk backup limit.
  All fourteen additions were assessed as useful concrete visual explanations.
- Evans-inspired: define regular files on the status page, remove the PATH page's
  dependency on an as-yet-unintroduced script, explain child-side expansion of
  the quoted variable, distinguish file contents from commit names, and decode
  the job selector. Confirms the same variable, lookup-stop and backup refinements.
- Teacher: move the existing signal data-loss warning beside the command; connect
  PATH to environment variables, distinguish a false test from a malfunction,
  define sleep on the jobs page and name git restore in its opening definition.
  Confirms the variable and same-disk backup corrections.
- Beginner: confirms variable and nested-quoting gaps; explain the job selector
  and launch numbers, mark unstaging as an independent example after the commit
  continuation, and explain that unreadable files can make disk-usage totals
  incomplete.

### Complementary corrections and integration

- Defined assignment, variable retrieval, quoted values, unset values and
  child-side expansion locally. Reflowed existing blocks without reducing the
  readable font sizes. The environment title identifies programs, not children
  as people.
- Defined regular files and distinguished false-test status from malfunction.
  Conditional examples are explicitly independent tests, with next-command gates.
- Connected PATH to variables and inheritance, showed the first usable match
  stopping lookup, and replaced the premature script example with an already
  illustrated executable path.
- Labelled recursive copying's original tree as before/after; explained unstaging's
  committed source and independent starting case. The preceding staging and
  commit pages now share an explicit last-commit state and a consistent staged
  edit; no unstaged difference is promised after staging.
- Named git restore in its definition, qualified the backup warning to the same
  disk, decoded job selectors and initial PID/job-number output, defined sleep
  locally, explained incomplete du totals and moved the signal loss warning beside
  the command.
- Regenerated the 69-page PDF, thirteen chapter sheets/bookmarks and the sample.
  Inspected all twelve modified full-page renders. Minimum text margin remains
  **10.47 mm**. Focused Linux confirmation resolves both original findings and
  reports no new material defect after inspecting ten affected full renders.
  Urban-inspired confirmation resolves both must-fixes and all six refinements,
  reporting no remaining material composition, context or collision defects after
  ten affected full renders. Its final minor handwritten export mention was
  converted to monospace, rendered again and inspected.

All eleven requested knowledge topics are included. The complementary edition's
editorial review is complete; actual-size reading and printer approval are still
pending. No example commands, installs, remote operations, commits or pushes were
performed, and no purchased artwork was loaded or reused.

## Indentation and centralized package management

The user's next feedback requested a whole-book code-indentation audit and a
single place for package management rather than repeating each tool's install.

- Inspected displayed code across all 69 preceding manifest sources. The Bash
  examples already contained two-space body indentation and four-space continuation
  indentation, but default SVG whitespace collapsing removed it in the renders.
  Added explicit whitespace preservation to decisions, both loops and the local
  server block. Applied it to disk-usage and address-lookup output too, where
  repeated spaces represent aligned columns. Closing keywords stay aligned with
  their opening keywords. The unit file's unindented directives remain correct.
- Created a three-page Package Management chapter immediately after Terminal and
  Commands: installation/repositories/dependencies/privilege; command-to-package
  lookup by distro; upgrades versus list refresh and package removal. Reused the
  existing installation and network-tool sources, replacing the latter's repeated
  installation with the centralized lookup. Only one additional page was needed.
- Removed repeated Git, Python and socket-tool installation commands. Their pages
  retain prerequisites and point to Package Management / 01–02; help and reading
  do the same. The lookup covers every previously distributed package example.
- Updated manifest and headers. The current edition has **70 pages, fourteen
  chapters and fourteen bookmarks**. All sources were exported again and all
  affected full renders inspected; minimum extracted text margin is **10.47 mm**.
- Added persistent rules for rendered indentation and centralized package
  management. Both focused reviews are complete: Linux approved package names,
  commands, warnings and indentation, and the teaching/Urban-inspired review
  confirmed the consolidation and rendered indentation.
- Applied their remaining clarifications: a visible repositories → manager →
  installed package flow; explicit replacement of nano with the chosen package
  name; centralized find guidance; and prerequisites/references at the ping and
  first runnable curl examples. Re-exported and inspected all five corrected
  pages. A whole-source search confirms distro installation/upgrade/removal
  commands occur only inside the three-page Package Management chapter.
- Final proof: **70 pages, fourteen chapters/bookmarks, 10.47 mm minimum text
  margin**. No lesson commands, installations, commits or pushes were performed.
