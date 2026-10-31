#!/usr/bin/env node
/**
 * .claude/hooks/tripwire.js - PreToolUse: recognise the RECURRENCE of a known
 * mistake in the action about to run, and say so beside it (P336).
 *
 * WHY NOT RETRIEVAL. Measured 2026-10-31 on real actions: word search found
 * the right pattern for 3 of 7 known recurrences; per-file lookup listed up to
 * 20 patterns per action; one regex per lesson caught 7/7 and fired on 0 of 58
 * routine commands. A pattern says the lesson abstractly ("a key that
 * identifies nothing"); the action is concrete (`hadith_number=eq.6570`).
 * Recognising that takes a rule written for that lesson, not similarity.
 *
 * INPUT: the PreToolUse JSON on stdin. Every string value in `tool_input` is
 * scanned, whatever the field is called - the hook does not depend on field
 * names it was not able to verify (command, content, new_string, ...).
 *
 * OUTPUT (exit 0, JSON only - any other stdout breaks JSON parsing):
 *   nothing                 no tripwire matched; normal permission flow
 *   additionalContext       a "warn" tripwire matched; shown next to the result
 *   permissionDecision ask  an "ask" tripwire matched; escalated to the user
 * Text is written as facts, per the docs' note on prompt-injection defences.
 *
 *   node .claude/hooks/tripwire.js --check
 *       every tripwire must fire on its own sample and NOTHING may fire on the
 *       routine set; prints one line per result, exits 1 on any failure.
 *       audit-docs.py calls this rather than re-implementing the matcher (P270).
 */
const fs = require('fs');
const path = require('path');

const ROOT = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const TRIP = path.join(ROOT, '.claude', 'tripwires.json');
const ROUTINE = path.join(ROOT, '.claude', 'tripwire-routine.json');
const INDEX = path.join(ROOT, 'PATTERN_INDEX.md');

function load() {
  const t = JSON.parse(fs.readFileSync(TRIP, 'utf-8'));
  return t.tripwires.map((w) => ({
    ...w,
    rx: new RegExp(w.regex, w.flags || ''),
    guardRx: w.guard ? new RegExp(w.guard, w.flags || '') : null,
    alsoRx: w.also ? new RegExp(w.also, w.flags || '') : null,
  }));
}

function titles() {
  const out = {};
  try {
    for (const l of fs.readFileSync(INDEX, 'utf-8').split(/\r?\n/)) {
      const m = l.match(/^- \*\*P(\d+)\*\* - (.*)$/);
      if (m && !out[+m[1]]) out[+m[1]] = m[2];
    }
  } catch (e) { /* titles are a courtesy; matching does not need them */ }
  return out;
}

function strings(v, acc) {
  if (typeof v === 'string') acc.push(v);
  else if (Array.isArray(v)) v.forEach((x) => strings(x, acc));
  else if (v && typeof v === 'object') Object.values(v).forEach((x) => strings(x, acc));
  return acc;
}

function match(wires, text) {
  return wires.filter((w) => w.rx.test(text)
    && !(w.guardRx && w.guardRx.test(text))
    && (!w.alsoRx || w.alsoRx.test(text)));
}

function dedupe(hits) {
  // one line per pattern; an "ask" entry wins over a "warn" entry for the same one
  const by = {};
  for (const w of hits) {
    if (!by[w.pattern] || w.mode === 'ask') by[w.pattern] = w;
  }
  return Object.values(by);
}

// Prose is not an action. Docs quote these commands (fix_patterns.md, CLAUDE.md,
// CHANGELOG.md), and the tripwire files hold the samples by design.
const EXEMPT = /(\.md$)|((^|[\\/])\.claude[\\/](tripwires\.json|tripwire-routine\.json|hooks[\\/]tripwire\.js)$)/i;

function render(hits, names) {
  hits = dedupe(hits);
  const ask = hits.filter((w) => w.mode === 'ask');
  const lines = hits.map((w) => 'Tripwire P' + String(w.pattern).padStart(3, '0')
    + ' (' + (names[w.pattern] || 'see fix_patterns.md') + '): ' + w.why
    + ' Full text: `## PATTERN ' + w.pattern + '` in fix_patterns.md.');
  const out = { hookSpecificOutput: { hookEventName: 'PreToolUse',
    additionalContext: lines.join('\n') } };
  if (ask.length) {
    out.hookSpecificOutput.permissionDecision = 'ask';
    out.hookSpecificOutput.permissionDecisionReason = ask.map((w) =>
      'P' + w.pattern + ': ' + w.why).join(' | ');
  }
  return out;
}

function check() {
  const wires = load();
  let fails = 0;
  for (const w of wires) {
    const hits = match(wires, w.sample);
    const ok = hits.some((h) => h === w);
    console.log((ok ? 'ok   ' : 'FAIL ') + 'P' + w.pattern + ' [' + w.mode + '] fires on its sample');
    if (!ok) fails++;
  }
  const routine = JSON.parse(fs.readFileSync(ROUTINE, 'utf-8')).commands;
  let noisy = 0;
  routine.forEach((c, i) => {
    const hits = match(wires, c);
    if (hits.length) {
      noisy++;
      console.log('FAIL routine #' + i + ' fired ' + hits.map((h) => 'P' + h.pattern).join(','));
    }
  });
  console.log((noisy ? 'FAIL ' : 'ok   ') + 'silent on ' + (routine.length - noisy)
    + '/' + routine.length + ' routine commands');
  process.exit(fails || noisy ? 1 : 0);
}

if (process.argv[2] === '--check') check();

let input = '';
process.stdin.setEncoding('utf-8');
process.stdin.on('data', (d) => { input += d; });
process.stdin.on('end', () => {
  try {
    const ev = JSON.parse(input || '{}');
    const fp = (ev.tool_input && (ev.tool_input.file_path || ev.tool_input.notebook_path)) || '';
    if (fp && EXEMPT.test(fp)) process.exit(0);
    const text = strings(ev.tool_input || {}, []).join('\n');
    const hits = match(load(), text);
    if (hits.length) process.stdout.write(JSON.stringify(render(hits, titles())));
  } catch (e) {
    // A broken tripwire must never block work: say nothing, exit 0.
    process.stderr.write('tripwire.js: ' + e.message + '\n');
  }
  process.exit(0);
});
