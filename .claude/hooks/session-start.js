#!/usr/bin/env node
/**
 * .claude/hooks/session-start.js
 *
 * Injects PATTERN_INDEX.md into the session's opening context.
 *
 * WHY A HOOK AND NOT A RULE IN CLAUDE.md
 * CLAUDE.md has said "read the repo at session start" since 2026-10-01. It was
 * followed three times out of five. P119, P126, P185 and P332 are all the same
 * shape: a check with no caller. fix_patterns.md is 817 KB, so nobody reads it
 * at session start, and P326, P329 and P332 were each a repeat of a pattern
 * already written down in it.
 *
 * SessionStart stdout is added to Claude's context by Claude Code itself - this
 * does not depend on anyone, including Claude, choosing to read a file.
 * (code.claude.com/docs/en/hooks: "the exceptions are UserPromptSubmit,
 * UserPromptExpansion, SessionStart, and PostModelSwitch, where Claude Code
 * adds plain-text stdout as context that Claude can see and act on.")
 *
 * Output must not begin with '{' or it is parsed as JSON. It begins with text.
 * Node, not `cat`/`head`: this machine is Windows and has no `head` (P334).
 */
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const INDEX = path.join(ROOT, 'PATTERN_INDEX.md');
const UPSKILL = path.join(ROOT, 'self_upskilling.md');
const MAX_BYTES = 80000;

const lines = [];
const say = (s) => lines.push(s);

say('=== hadith-reels: session start ===');
say('');

// ---- 1. the pattern index ---------------------------------------------------
try {
  const raw = fs.readFileSync(INDEX, 'utf-8');
  if (Buffer.byteLength(raw, 'utf-8') > MAX_BYTES) {
    say('PATTERN_INDEX.md is over ' + MAX_BYTES + ' bytes. Printing the file');
    say('cross-reference only; read the rest with `Read PATTERN_INDEX.md`.');
    say('');
    const cut = raw.indexOf('## By number');
    say(cut > 0 ? raw.slice(0, cut) : raw.slice(0, MAX_BYTES));
  } else {
    say(raw.replace(/\r\n/g, '\n').trimEnd());
  }
  say('');
  say('That index is a list of POINTERS. Before changing a script, read the');
  say('patterns listed for it under "By file" - the full text lives at');
  say('`## PATTERN <n>` in fix_patterns.md. A title is not the lesson.');
} catch (e) {
  say('!! PATTERN_INDEX.md could not be read: ' + e.message);
  say('!! Run: python scripts/build-pattern-index.py');
}

// ---- 2. the weekly tool check ----------------------------------------------
try {
  const su = fs.readFileSync(UPSKILL, 'utf-8');
  const m = su.match(/\*\*Next due:\*\*\s*(\d{4}-\d{2}-\d{2})/);
  if (m) {
    const due = new Date(m[1] + 'T00:00:00Z');
    const today = new Date(new Date().toISOString().slice(0, 10) + 'T00:00:00Z');
    const days = Math.round((due - today) / 86400000);
    say('');
    if (days < 0) {
      say('!! self_upskilling.md tool review is ' + (-days) + ' DAY(S) OVERDUE (due '
          + m[1] + '). audit-docs.py fails the push until it is run and the date');
      say('!! moved. Run it now, do not move the date (P198, P332).');
    } else {
      say('Weekly tool review due ' + m[1] + ' (' + days + ' day(s)). '
          + 'The date CHECKED is the value.');
    }
  }
} catch (e) {
  say('');
  say('!! self_upskilling.md could not be read: ' + e.message);
}

process.stdout.write(lines.join('\n') + '\n');
