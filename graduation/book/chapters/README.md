# At the Prompt: original Linux reference

An illustrated reference for beginners using their own Linux computer. Fourteen
topic chapters follow knowledge and prerequisites. S01–S08 are a coverage
checklist, not the reading order or a dependency on the classroom machine.
No purchased material is loaded or reused. The separate anthology is unchanged.

[Local proof: 70 A5 landscape pages](../local/at-the-prompt-original-knowledge-A5.pdf).
The complementary edition's five reviews are complete. The latest indentation
and centralized package-management changes received focused technical and
composition reviews; their remaining clarifications are applied and inspected.

| Chapter | Pages | Scope | Deliberate adaptations |
| :--- | ---: | :--- | :--- |
| Terminal and Commands | 4 | Command structure, bearings, recovery, help | Begin locally, not with an assumed SSH account. |
| Package Management | 3 | Packages, repositories, dependencies, install, command-to-package lookup, upgrades and removal | Teach once; Debian/Ubuntu and Fedora commands stay here. Missing-tool references elsewhere point here. |
| Files and Paths | 15 | Root/home, navigation, hidden names, quotes/globs, reading/search, creation/editing, file/directory copying, links, removal, disk space | Quote filenames before modifying files; distinguish disk capacity from directory usage. |
| Ownership and Permissions | 4 | Owner, access groups, directory rules, chmod | Explain ownership before permissions; no blanket access fixes. |
| Streams and Pipes | 6 | Streams, redirection, pipes, grep, separate errors, tee | Concrete matching lines; literal-text search before regular expressions. |
| Shell Execution and Environment | 3 | Exit status, conditional commands, export, PATH | Separate results from status; child inheritance and command lookup are distinct ideas. |
| Git History | 8 | Repository, staging, commits, recovery, ignore, remotes, backups | Unstage does not discard; explicit last-commit restore warns about lost edits; independent backups are not local Git history. |
| Bash Scripts | 6 | Scripts, quoting, arguments, decisions, loops, debugging | Small standalone examples, no report/build scripts. |
| Processes and Signals | 3 | Running instances, foreground/background jobs, PIDs, stopping | Job numbers are not PIDs; background execution is not service supervision. |
| Network Basics | 2 | Layers, lookup and ping | Tool installation is covered centrally; no course URL or fabricated expected latency. |
| Remote Terminals with SSH | 1 | Local terminal versus remote shell | Optional remote access with explicit prerequisites. |
| HTTP Requests and Responses | 5 | Client/server, response, request shape, statuses, exit status | Protocol before local hosting; no configured proxy. |
| A Local Web Server | 3 | Loopback demo, ports, process/port/page evidence | Python standard library; install Python; no firewall assumptions. |
| Services and Troubleshooting | 7 | systemd, user units, actions, logs, logout, repair | Explicit systemd/user-manager prerequisites; no pre-enabled lingering or instructor repair service. |

## Sources and chapter order

Curriculum grounding: the recap/slides topics in `sessions/S01` through `S08`
under `maker-guide/src/maker_guide/curriculum/content/lf2607/`. S07/S08 operational
details were intentionally replaced, not copied: a fresh, dedicated home demo
directory, loopback-only port 8000, Python's HTTP server and an optional user unit.
This is for learning locally, not a public-hosting or production-hardening guide.

[`contents.toml`](contents.toml) is the authoritative reading order, including
the three reused sample illustrations. The `s01/`–`s08/` paths are legacy source
locations, not chapter membership. All sources appear exactly once; directory
creation and empty-file creation now have separate pages.
New complementary sources live in `complements/`; their folder is not a chapter.
The eleven additional topics use fourteen pages: quoted filenames and wildcards,
environment variables and command lookup, and unstaging and discarding each get
separate explanations. This preserves one central question per page.
Ownership moves beside permissions; output redirection moves beside streams;
processes get their own chapter; SSH follows network basics; HTTP brings together
client/server, requests and responses before the local-server example.

Do not merge every PDF in `local/`: it retains earlier superseded proofs. Export
and merge only the explicit manifest order. The current PDF bookmarks use topic
titles, not session numbers.

## Characters

No single default protagonist. Rounded bob, curls, tied-back hair, glasses and
bald heads distinguish people; silhouettes and posture vary too. Hair must not
use paired pointed tufts resembling horns. Keep black outlines and white paper,
not colour-dependent distinctions. The character choices are original artwork.

## Composition and review

Titles identify the concept before a joke: relative paths with `cd`, pipes and
Git's staging area are explicit. Illustrated commands are prominent and every
inline command uses Liberation Mono; prose stays handwritten. Files have factual
labels, not dialogue. Commands changing state get a visible before/after, including
owner execution permission with `chmod`. Installation teaches package managers,
using nano as an example rather than treating nano as the general concept.

Pages remain 210 × 148 mm. The SVG viewBox adds a white safety frame around the
artwork; the 70-page PDF's extracted text bounds have a minimum margin of
10.47 mm. This does not
establish printer binding/bleed specifications or replace
actual-size reading approval. Highlights follow padded content groups rather
than floating behind unrelated labels. The complete editorial rules are in
`../AGENTS.md`.

Five independent agent reviews are complete: Linux technical correctness,
teaching quality, Julia Evans-inspired visual explanation, Tim Urban-inspired
composition, and simulated beginner comprehension. These are not participation
or endorsement by either author, nor a real user study. Urban-inspired composition
feedback takes priority in stylistic conflicts; correctness and comprehension
cannot be waived.

Their reconciled findings and correction outcome are recorded in
[`REVIEW.md`](REVIEW.md). The 70-page proof and fourteen contact sheets are
exported. The complementary pages' five reviews and corrections are complete;
the centralized package chapter and whitespace correction are also rendered,
reviewed and inspected. All installation commands now live in Package Management.

## Portability within Linux

No tool is promised on every Linux installation. Debian/Ubuntu and Fedora
package commands are labelled separately; administrative access and a network
connection to package repositories are prerequisites for installation. Common
core utilities, Bash and the procps process tools are assumed on ordinary full
installations; minimal systems may need packages. The central Package Management
lookup gives the distro-specific names, including the process and socket tools.

Git starts locally. Remote hosting and authentication depend on the provider
chosen by the reader; no provider or configured remote is assumed. Reserved
`example.com` is a public HTTP illustration, not an endpoint controlled by us;
responses depend on the network and site. No book export contacts it.

Python's demo explicitly binds to `127.0.0.1`; other local users can still connect.
The directory must contain only public-intended demo data, with no links to
private files. Port 8000 is an example, not a reserved classroom allocation. If
another process owns it, inspect rather than stopping it; use the same chosen
port in the server, client and optional service definition.

The systemd chapter applies only if systemd and a usable user manager are present.
It does not install an init system. Lingering is an optional account-policy change,
not a setting enabled by the book or a promise of availability during sleep.

## Reproduce local illustrations

Inkscape, Chilanka and Liberation fonts are needed to export editable SVGs. From
`graduation/book`:

```bash
for chapter in s01 s02 s03 s04 s05 s06 s07 s08; do
  mkdir -p "local/$chapter"
  for source in "chapters/$chapter/"*.svg; do
    name=$(basename "$source" .svg)
    inkscape "$source" --export-type=pdf --export-filename="local/$chapter/$name.pdf"
    inkscape "$source" --export-width=1260 --export-filename="local/$chapter/$name.png"
  done
done
```

Export the three reused samples too. Assemble according to `contents.toml`, not
the loop's directory order; that loop only exports individual source pages.
Generated PDFs and previews stay Git-ignored; no paid source files are needed.
Static editorial sources add no dependency or independent CI component. CI must
not assemble the purchased anthology or upload its artwork. The local proof is
an editorial review export, not a printer-approved file with bleed or binding margins.

Editorial requirements are persisted in [AGENTS.md](../AGENTS.md): define before
qualifying, supply context, keep the drawings clear, use sparse pastel accents,
and review every page from a beginner's perspective.
