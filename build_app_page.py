#!/usr/bin/env python3
"""Produit la page V2 : la page V1 plus le panneau de chat.

On ne duplique pas la V1. On charge son générateur, on récupère le HTML qu'il
produit, et on y injecte le CSS, le markup et le JS du chat. La V1 reste
livrable telle quelle, et une correction de copy faite dans build_page.py se
retrouve dans les deux.
"""

import importlib.util
import pathlib
import sys

V1 = pathlib.Path("/home/claude/work/front/build_page.py")
OUT = pathlib.Path(__file__).parent / "app" / "static" / "index.html"

spec = importlib.util.spec_from_file_location("build_page", V1)
v1 = importlib.util.module_from_spec(spec)
sys.modules["build_page"] = v1
spec.loader.exec_module(v1)          # écrit aussi la V1, c'est voulu

html = v1.OUT.read_text(encoding="utf-8")

CHAT_CSS = """
<style>
  /* ------------------------------------------------------- drawer de chat */
  .tg-tdr__drawer {
    position: fixed; inset: 0; z-index: 1000; pointer-events: none;
  }
  .tg-tdr__drawer-backdrop {
    position: absolute; inset: 0; background: rgba(10,2,26,.6);
    opacity: 0; transition: opacity .2s ease;
  }
  .tg-tdr__drawer-panel {
    position: absolute; top: 0; right: 0; height: 100%;
    width: min(480px, 100%); background: var(--tg-russian-violet);
    color: var(--tg-white); display: flex; flex-direction: column;
    box-shadow: -12px 0 40px rgba(0,0,0,.35);
    transform: translateX(100%); transition: transform .25s ease;
  }
  .tg-tdr__drawer--open { pointer-events: auto; }
  .tg-tdr__drawer--open .tg-tdr__drawer-backdrop { opacity: 1; }
  .tg-tdr__drawer--open .tg-tdr__drawer-panel { transform: translateX(0); }
  .tg-tdr__drawer-head {
    display: flex; align-items: center; justify-content: space-between;
    padding: var(--s-md); border-bottom: 1px solid rgba(230,222,250,.16);
    flex: none;
  }
  .tg-tdr__drawer-title {
    font-family: 'Kanit', sans-serif; font-weight: 800; font-size: 15px;
  }
  .tg-tdr__drawer-close {
    background: none; border: 0; color: var(--tg-white); font-size: 22px;
    line-height: 1; cursor: pointer; min-width: 44px; min-height: 44px;
  }
  .tg-tdr__drawer-close:focus-visible { outline: 3px solid var(--tg-violet-light); }
  .tg-tdr__log {
    flex: 1; padding: var(--s-md); overflow-y: auto;
    display: flex; flex-direction: column; gap: var(--s-sm);
    scroll-behavior: smooth; position: relative;
  }
  .tg-tdr__log--dragover::after {
    content: 'Drop to attach'; position: absolute; inset: var(--s-sm);
    border: 2px dashed var(--tg-violet-light); border-radius: var(--tg-r);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Kanit', sans-serif; font-weight: 700; letter-spacing: .04em;
    color: var(--tg-violet-light); background: rgba(27,4,66,.85);
    pointer-events: none;
  }
  .tg-tdr__attachment {
    align-self: flex-end; font-size: 13px; color: var(--tg-violet-light);
    display: flex; align-items: center; gap: 6px;
  }
  .tg-tdr__msg { max-width: 78ch; font-size: 15px; line-height: 1.6; }
  .tg-tdr__msg--me {
    align-self: flex-end; background: var(--tg-electric-indigo);
    padding: 11px 15px; border-radius: var(--tg-r); white-space: pre-wrap;
  }
  .tg-tdr__msg--claude { align-self: flex-start; color: var(--tg-lavender); white-space: pre-wrap; }
  .tg-tdr__msg--claude strong { color: var(--tg-white); }
  .tg-tdr__who {
    display: block; font-family: 'Kanit', sans-serif; font-weight: 800;
    font-size: 11px; letter-spacing: .12em; text-transform: uppercase;
    color: var(--tg-violet-light); margin-bottom: 4px;
  }
  .tg-tdr__hint {
    align-self: center; text-align: center; color: var(--tg-violet-light);
    font-size: 14px; max-width: 52ch; padding: var(--s-lg) 0;
  }
  .tg-tdr__busy {
    align-self: flex-start; font-size: 13px; color: var(--tg-violet-light);
    display: flex; align-items: center; gap: 8px;
  }
  .tg-tdr__busy span {
    width: 6px; height: 6px; border-radius: 50%; background: var(--tg-violet-light);
    animation: tgpulse 1.1s ease-in-out infinite;
  }
  .tg-tdr__busy span:nth-child(2) { animation-delay: .18s; }
  .tg-tdr__busy span:nth-child(3) { animation-delay: .36s; }
  @keyframes tgpulse { 0%,100% { opacity: .25; } 50% { opacity: 1; } }

  .tg-tdr__deck {
    align-self: flex-start; background: var(--tg-white);
    color: var(--tg-russian-violet); border-radius: var(--tg-r);
    padding: var(--s-md); max-width: 46ch;
  }
  .tg-tdr__deck-name {
    font-family: 'Kanit', sans-serif; font-weight: 800; font-size: 15px;
    display: block; word-break: break-word;
  }
  .tg-tdr__deck-todo { font-size: 13px; margin-top: 6px; }
  .tg-tdr__deck-acts { display: flex; flex-wrap: wrap; gap: var(--s-xs); margin-top: var(--s-sm); }
  .tg-tdr__mini {
    font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600;
    padding: 10px 15px; min-height: 44px; border-radius: var(--tg-r);
    border: 1px solid var(--tg-russian-violet); cursor: pointer;
    background: var(--tg-russian-violet); color: var(--tg-white);
    text-decoration: none; display: inline-flex; align-items: center;
  }
  .tg-tdr__mini--ghost { background: transparent; color: var(--tg-russian-violet); }
  .tg-tdr__mini:focus-visible { outline: 3px solid var(--tg-electric-indigo); outline-offset: 2px; }

  .tg-tdr__composer {
    border-top: 1px solid rgba(230,222,250,.16); padding: var(--s-md);
    display: flex; gap: var(--s-sm); align-items: flex-end;
  }
  .tg-tdr__composer textarea {
    flex: 1; resize: none; font-family: 'Inter', sans-serif; font-size: 15px;
    line-height: 1.5; color: var(--tg-white); background: rgba(27,4,66,.55);
    border: 1px solid rgba(230,222,250,.28); border-radius: var(--tg-r);
    padding: 12px 14px; min-height: 52px; max-height: 220px;
  }
  .tg-tdr__composer textarea::placeholder { color: rgba(230,222,250,.5); }
  .tg-tdr__composer textarea:focus-visible {
    outline: none; border-color: var(--tg-violet-light);
  }
  .tg-tdr__send {
    font-family: 'Inter', sans-serif; font-size: 15px; font-weight: 600;
    background: var(--tg-electric-indigo); color: var(--tg-white);
    border: 0; border-radius: var(--tg-r); padding: 14px 22px; min-height: 52px;
    cursor: pointer;
  }
  .tg-tdr__send[disabled] { opacity: .45; cursor: default; }
  .tg-tdr__send:focus-visible { outline: 3px solid var(--tg-violet-light); outline-offset: 3px; }
  .tg-tdr__attach {
    background: rgba(230,222,250,.1); border: 1px solid rgba(230,222,250,.28);
    color: var(--tg-white); border-radius: var(--tg-r); min-width: 44px;
    min-height: 52px; font-size: 17px; cursor: pointer;
  }
  .tg-tdr__attach[disabled] { opacity: .45; cursor: default; }
  .tg-tdr__attach:focus-visible { outline: 3px solid var(--tg-violet-light); outline-offset: 2px; }
  .tg-tdr__bar {
    display: flex; flex-wrap: wrap; gap: var(--s-xs); align-items: center;
    justify-content: space-between; flex: none;
    padding: var(--s-sm) var(--s-md) var(--s-md);
    font-size: 13px; color: var(--tg-violet-light);
  }
  .tg-tdr__bar button {
    background: none; border: 0; color: var(--tg-violet-light); cursor: pointer;
    font-family: 'Inter', sans-serif; font-size: 13px; text-decoration: underline;
    padding: 8px 0; min-height: 44px;
  }
  .tg-tdr__gate { padding: var(--s-2xl) var(--s-md); text-align: center; }
  .tg-tdr__gate p { color: var(--tg-lavender); max-width: 46ch; margin: 0 auto var(--s-md); }
  @media (prefers-reduced-motion: reduce) {
    .tg-tdr__log { scroll-behavior: auto; }
    .tg-tdr__busy span { animation: none; opacity: .7; }
  }
</style>
"""

CHAT_SECTION = """
  <div class="tg-tdr__drawer" id="tg-chat-drawer" aria-hidden="true">
    <div class="tg-tdr__drawer-backdrop" id="tg-chat-backdrop"></div>
    <div class="tg-tdr__drawer-panel" role="dialog" aria-modal="true"
         aria-label="Conversation with Claude">
      <div class="tg-tdr__drawer-head">
        <span class="tg-tdr__drawer-title" id="tg-chat-title">Talk to Claude</span>
        <button type="button" class="tg-tdr__drawer-close" id="tg-chat-close"
                aria-label="Close">&times;</button>
      </div>

      <div class="tg-tdr__log" id="tg-chat-log" role="log" aria-live="polite"
           aria-label="Conversation with Claude">
        <p class="tg-tdr__hint" id="tg-chat-hint">Tell Claude which ritual you
          signed up for and roughly what you want to talk about. Three words a
          line is enough, and you can drag a brief or a screenshot straight in
          here.</p>
      </div>

      <div id="tg-chat-gate" class="tg-tdr__gate" hidden>
        <p>You're not signed in. Reload the page and enter the shared Tribe
          Design password when your browser asks for it. Your notes stay in
          this session and are never shared with the rest of the tribe.</p>
        <button type="button" class="tg-tdr__btn tg-tdr__btn--primary"
                id="tg-chat-gate-reload">Reload</button>
      </div>

      <form class="tg-tdr__composer" id="tg-chat-form" hidden>
        <label class="tg-tdr__sr" for="tg-chat-input" style="position:absolute;left:-9999px">Your message</label>
        <textarea id="tg-chat-input" rows="2"
                  placeholder="Three words a line is plenty, or drag a file in..."></textarea>
        <input type="file" id="tg-chat-file" multiple hidden>
        <button type="button" class="tg-tdr__attach" id="tg-chat-attach"
                aria-label="Attach a file" title="Attach a file">&#128206;</button>
        <button class="tg-tdr__send" type="submit" id="tg-chat-send">Send</button>
      </form>

      <div class="tg-tdr__bar">
        <span id="tg-chat-who"></span>
        <button type="button" id="tg-chat-reset">Start a new conversation</button>
      </div>
    </div>
  </div>
"""

CHAT_JS = """
<script>
(function () {
  var log = document.getElementById('tg-chat-log');
  var form = document.getElementById('tg-chat-form');
  var gate = document.getElementById('tg-chat-gate');
  var input = document.getElementById('tg-chat-input');
  var send = document.getElementById('tg-chat-send');
  var hint = document.getElementById('tg-chat-hint');
  var who = document.getElementById('tg-chat-who');
  var resetBtn = document.getElementById('tg-chat-reset');
  var drawer = document.getElementById('tg-chat-drawer');
  var backdrop = document.getElementById('tg-chat-backdrop');
  var closeBtn = document.getElementById('tg-chat-close');
  var title = document.getElementById('tg-chat-title');
  var attachBtn = document.getElementById('tg-chat-attach');
  var fileInput = document.getElementById('tg-chat-file');
  if (!log || !form) return;

  var driveEnabled = false;
  var busyEl = null;
  var streamEl = null;
  var lastFocused = null;

  function openDrawer(label) {
    lastFocused = document.activeElement;
    if (label) title.textContent = label;
    drawer.classList.add('tg-tdr__drawer--open');
    drawer.setAttribute('aria-hidden', 'false');
    (form.hidden ? gate.querySelector('button, a') : input).focus();
  }

  function closeDrawer() {
    drawer.classList.remove('tg-tdr__drawer--open');
    drawer.setAttribute('aria-hidden', 'true');
    if (lastFocused && lastFocused.focus) lastFocused.focus();
  }

  closeBtn.addEventListener('click', closeDrawer);
  backdrop.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && drawer.classList.contains('tg-tdr__drawer--open')) closeDrawer();
  });

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function scroll() { log.scrollTop = log.scrollHeight; }

  function addMine(text) {
    if (hint) { hint.remove(); hint = null; }
    var w = el('div', 'tg-tdr__msg tg-tdr__msg--me');
    w.appendChild(el('span', 'tg-tdr__who', 'You'));
    w.appendChild(document.createTextNode(text));
    log.appendChild(w); scroll();
  }

  function startClaude() {
    var w = el('div', 'tg-tdr__msg tg-tdr__msg--claude');
    w.appendChild(el('span', 'tg-tdr__who', 'Claude'));
    var body = el('span');
    w.appendChild(body);
    log.appendChild(w); scroll();
    return body;
  }

  function setBusy(label) {
    clearBusy();
    busyEl = el('div', 'tg-tdr__busy');
    busyEl.appendChild(el('span')); busyEl.appendChild(el('span')); busyEl.appendChild(el('span'));
    busyEl.appendChild(el('em', null, label));
    log.appendChild(busyEl); scroll();
  }
  function clearBusy() { if (busyEl) { busyEl.remove(); busyEl = null; } }

  var TOOL_LABEL = {
    Bash: 'building the deck', Write: 'writing', Read: 'reading your notes',
    Edit: 'editing', Glob: 'looking around', Grep: 'searching',
    Skill: 'opening the ritual playbook'
  };

  function addDeck(name) {
    var card = el('div', 'tg-tdr__deck');
    card.appendChild(el('span', 'tg-tdr__deck-name', name));
    card.appendChild(el('p', 'tg-tdr__deck-todo',
      'Left for you: drop your visuals in the dashed zones, fill any [brackets], blur screenshots, and read it through.'));
    var acts = el('div', 'tg-tdr__deck-acts');

    var dl = el('a', 'tg-tdr__mini', 'Download');
    dl.href = '/api/deck/' + encodeURIComponent(name);
    dl.setAttribute('download', name);
    acts.appendChild(dl);

    if (driveEnabled) {
      var toDrive = el('button', 'tg-tdr__mini tg-tdr__mini--ghost', 'Send to the tribe Drive');
      toDrive.type = 'button';
      toDrive.addEventListener('click', function () {
        toDrive.disabled = true;
        toDrive.textContent = 'Sending...';
        fetch('/api/drive/' + encodeURIComponent(name), { method: 'POST' })
          .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
          .then(function (res) {
            if (!res.ok) throw new Error(res.j.detail || 'failed');
            toDrive.textContent = 'In the Drive';
            if (res.j.link) {
              var open = el('a', 'tg-tdr__mini tg-tdr__mini--ghost', 'Open in Drive');
              open.href = res.j.link; open.target = '_blank'; open.rel = 'noopener';
              acts.appendChild(open);
            }
          })
          .catch(function (e) {
            toDrive.disabled = false;
            toDrive.textContent = 'Drive failed, retry';
            console.error('[prep-kit] drive upload failed', e);
          });
      });
      acts.appendChild(toDrive);
    }
    card.appendChild(acts);
    log.appendChild(card); scroll();
  }

  function addError(text) {
    var w = el('div', 'tg-tdr__msg tg-tdr__msg--claude');
    w.appendChild(el('span', 'tg-tdr__who', 'Something broke'));
    w.appendChild(document.createTextNode(text));
    log.appendChild(w); scroll();
  }

  function addAttachment(name) {
    if (hint) { hint.remove(); hint = null; }
    log.appendChild(el('div', 'tg-tdr__attachment', '📎 ' + name));
    scroll();
  }

  async function uploadFile(file) {
    var body = new FormData();
    body.append('file', file);
    var res = await fetch('/api/upload', { method: 'POST', body: body });
    if (res.status === 401) { location.reload(); throw new Error('not signed in'); }
    if (!res.ok) throw new Error('upload failed (' + res.status + ')');
    return (await res.json()).name;
  }

  async function attachFiles(files) {
    for (var i = 0; i < files.length; i++) {
      try {
        var name = await uploadFile(files[i]);
        addAttachment(name);
        await ask("I've attached: " + name);
      } catch (e) {
        addError('Could not attach ' + files[i].name + ': ' + String(e.message || e));
      }
    }
  }

  function lock(on) {
    send.disabled = on;
    input.disabled = on;
    if (attachBtn) attachBtn.disabled = on;
    send.textContent = on ? 'Working' : 'Send';
  }

  function handle(ev) {
    if (ev.type === 'text') {
      clearBusy();
      if (!streamEl) streamEl = startClaude();
      streamEl.textContent += ev.text;
      scroll();
    } else if (ev.type === 'tool') {
      setBusy('Claude is ' + (TOOL_LABEL[ev.name] || 'working') + '...');
    } else if (ev.type === 'deck') {
      clearBusy(); addDeck(ev.name);
    } else if (ev.type === 'session' && ev.session) {
      fetch('/api/session', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session: ev.session })
      });
    } else if (ev.type === 'error') {
      clearBusy(); addError(ev.message);
    }
  }

  async function ask(text) {
    addMine(text);
    streamEl = null;
    lock(true);
    setBusy('Claude is reading');
    try {
      var res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      if (res.status === 401) { location.reload(); return; }
      if (!res.ok || !res.body) throw new Error('HTTP ' + res.status);

      var reader = res.body.getReader();
      var decoder = new TextDecoder();
      var buffer = '';
      while (true) {
        var chunk = await reader.read();
        if (chunk.done) break;
        buffer += decoder.decode(chunk.value, { stream: true });
        var parts = buffer.split('\\n\\n');
        buffer = parts.pop();
        parts.forEach(function (part) {
          var line = part.replace(/^data: /, '').trim();
          if (!line) return;
          try { handle(JSON.parse(line)); } catch (e) { console.warn('[prep-kit] bad event', line); }
        });
      }
    } catch (e) {
      addError(String(e.message || e));
    } finally {
      clearBusy();
      lock(false);
      input.focus();
    }
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    input.value = '';
    input.style.height = '';
    ask(text);
  });

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault(); form.requestSubmit();
    }
  });
  input.addEventListener('input', function () {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 220) + 'px';
  });

  resetBtn.addEventListener('click', function () {
    fetch('/api/reset', { method: 'POST' }).then(function () { location.reload(); });
  });

  if (attachBtn && fileInput) {
    attachBtn.addEventListener('click', function () { fileInput.click(); });
    fileInput.addEventListener('change', function () {
      if (fileInput.files.length) attachFiles(fileInput.files);
      fileInput.value = '';
    });
  }

  var dragDepth = 0;
  log.addEventListener('dragover', function (e) {
    if (form.hidden) return;
    e.preventDefault();
  });
  log.addEventListener('dragenter', function (e) {
    if (form.hidden) return;
    e.preventDefault();
    dragDepth++;
    log.classList.add('tg-tdr__log--dragover');
  });
  log.addEventListener('dragleave', function () {
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) log.classList.remove('tg-tdr__log--dragover');
  });
  log.addEventListener('drop', function (e) {
    e.preventDefault();
    dragDepth = 0;
    log.classList.remove('tg-tdr__log--dragover');
    if (form.hidden || !e.dataTransfer.files.length) return;
    attachFiles(e.dataTransfer.files);
  });

  /* Les boutons de la V1 pilotent le drawer en V2 plutôt que de copier un
     prompt dans le presse-papiers. */
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    var label = btn.querySelector('.tg-tdr__copy-label') || btn;
    var isHero = !!btn.closest('header');
    if (/^Copy the /.test(label.textContent)) {
      label.textContent = label.textContent.replace(/^Copy the /, 'Prepare my ').replace(/ prompt$/, '');
    } else if (/starter prompt|this prompt/.test(label.textContent)) {
      label.textContent = 'Start in the chat';
    }

    if (isHero) {
      // "Prepare my starter" : pas de chat direct, on va choisir un rituel.
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopImmediatePropagation();
        var rituals = document.getElementById('tg-tdr-rituals');
        if (rituals) rituals.scrollIntoView({ block: 'start' });
      }, true);
      return;
    }

    var key = btn.getAttribute('data-copy');
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopImmediatePropagation();
      if (key !== 'generic') {
        // Un rituel précis : Claude pose ses questions directement, pas de
        // prompt à trous à compléter avant d'envoyer.
        var ritualLabel = label.textContent.replace(/^Prepare my /, '');
        openDrawer(ritualLabel);
        if (!form.hidden) ask("I'm preparing my " + ritualLabel + " for the Tribe Design ritual.");
        return;
      }
      var prompt = (window.__TG_PROMPTS || {})[key];
      if (!prompt) return;
      openDrawer('Talk to Claude');
      input.value = prompt;
      input.dispatchEvent(new Event('input'));
    }, true);
  });

  var gateReload = document.getElementById('tg-chat-gate-reload');
  if (gateReload) gateReload.addEventListener('click', function () { location.reload(); });

  fetch('/api/config').then(function (r) { return r.json(); }).then(function (cfg) {
    driveEnabled = !!cfg.drive_enabled;
    if (cfg.user) {
      form.hidden = false; gate.hidden = true;
      who.textContent = 'Signed in as ' + cfg.user.name;
    } else {
      form.hidden = true; gate.hidden = false;
    }
  }).catch(function () { form.hidden = true; gate.hidden = false; });
})();
</script>
"""

# Les prompts de la V1 vivent dans une IIFE : on les réexpose pour le chat.
PROMPT_BRIDGE = (
    "<script>window.__TG_PROMPTS = "
    + v1.prompts_js
    + ";</script>\n"
)

html = html.replace("</head>", CHAT_CSS + "</head>")
anchor = '<section class="tg-tdr__section tg-tdr__section--pale" id="tg-tdr-how">'
assert anchor in html, "ancre de la section 'how' introuvable dans la V1"
html = html.replace(anchor, CHAT_SECTION + "\n  " + anchor)
html = html.replace("</body>", PROMPT_BRIDGE + CHAT_JS + "</body>")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print(f"écrit {OUT} — {len(html)/1024:.1f} KB")
