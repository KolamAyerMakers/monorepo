# S7 Recap: HTTP On The Wire

Session: S7

## Core Idea

The web is not magic. It is requests, responses, headers, status codes, and bytes.

## Remember

- `curl -I` shows headers.
- `curl -v` shows the conversation.
- `diff` can prove that network output matches a local file.
- The second URL fails because no user-managed service is listening yet.

## Live Core

If you attended live, you have the core milestone when you can explain source Markdown versus generated HTML, inspect headers, and explain why the service URL fails until your user service exists.

## Optional Reinforcement

Use the S7 quests if you want more site and HTTP practice. The endpoint is a multi-page site plus a correct explanation of reverse-proxy failure. Run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practical work. A passing check records your progress.

## Can You Explain This?

- What is the difference between source Markdown and generated HTML?
- What does `curl -I` omit?
- Why can a proxy return an error when the HTML files are fine?

## Keep

Keep `setup.md` if you created it live. `art.md` and troubleshooting notes are optional demo polish.

## Full Autonomy

Use [S7 Self-Study Guide: HTTP And Multi-Page Sites](self-study.md) for exact URL shapes, `curl` checks, disk-versus-network comparison, and HTTP status recovery.
