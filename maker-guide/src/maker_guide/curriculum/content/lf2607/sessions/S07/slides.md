# Linux Foundations S7

Session: S7

Your first page, on the wire

<!-- end_slide -->

# Today's Story

Your site is no longer just files. It is bytes crossing a network.

Teacher shows one request on the projector, then learners inspect their own URL.

<!-- end_slide -->

# Hands-On Spine

Hands-on now: run these against your own site and compare the three views.

```bash
curl -I
curl -v
diff
nc
```

<!-- end_slide -->

# Exit Goal

Learners can compare markdown source, rendered HTML, and network response.
<!-- end_slide -->

# Between-Session Practice Route

Highly recommended after class or for catch-up:

Use the guide throughout class and between sessions: run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practical work. A passing check records your progress.

1. Add `setup.md` and rebuild.
2. Inspect first URL headers.
3. Diagnose why the second URL fails before a service exists.
4. Publish ASCII art with fenced code.
5. Explain `200`, `404`, and `502`.

<!-- end_slide -->

# Three Views

Markdown source.

Generated HTML on disk.

Bytes returned over HTTP.
