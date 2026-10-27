# -*- coding: utf-8 -*-
"""
Notatnik — prosty serwer webowy z notatkami zapisywanymi do pliku notatki.md
Uruchom: python notatnik.py
Otwórz w przeglądarce: http://localhost:8080
"""

import http.server
import json
import os
import re
from datetime import datetime
from urllib.parse import unquote

PORT = 8080
NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notatki.md")

HTML_PAGE = r'''<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Notatnik</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: #f0f2f5;
      color: #1a1a2e;
      min-height: 100vh;
    }

    .container {
      max-width: 720px;
      margin: 0 auto;
      padding: 32px 20px;
    }

    h1 {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 24px;
      color: #1a1a2e;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    h1::before {
      content: '📝';
      font-size: 32px;
    }

    /* ---- Formularz ---- */
    .form-card {
      background: #fff;
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,.08);
      margin-bottom: 32px;
    }

    .form-card label {
      display: block;
      font-size: 13px;
      font-weight: 600;
      color: #555;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: .5px;
    }

    .form-card input[type="text"] {
      width: 100%;
      padding: 10px 14px;
      font-size: 16px;
      border: 2px solid #e0e0e0;
      border-radius: 8px;
      outline: none;
      transition: border-color .2s;
      margin-bottom: 16px;
    }

    .form-card input[type="text"]:focus {
      border-color: #4a6cf7;
    }

    .form-card textarea {
      width: 100%;
      padding: 10px 14px;
      font-size: 15px;
      border: 2px solid #e0e0e0;
      border-radius: 8px;
      outline: none;
      resize: vertical;
      min-height: 120px;
      transition: border-color .2s;
      margin-bottom: 16px;
      font-family: inherit;
      line-height: 1.5;
    }

    .form-card textarea:focus {
      border-color: #4a6cf7;
    }

    .btn-save {
      background: #4a6cf7;
      color: #fff;
      border: none;
      padding: 12px 28px;
      font-size: 15px;
      font-weight: 600;
      border-radius: 8px;
      cursor: pointer;
      transition: background .2s, transform .1s;
    }

    .btn-save:hover {
      background: #3b5de7;
    }

    .btn-save:active {
      transform: scale(.97);
    }

    .btn-save:disabled {
      background: #a0b0f0;
      cursor: not-allowed;
    }

    /* ---- Toast ---- */
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #2ecc71;
      color: #fff;
      padding: 12px 24px;
      border-radius: 8px;
      font-weight: 600;
      box-shadow: 0 4px 12px rgba(0,0,0,.15);
      opacity: 0;
      transform: translateY(16px);
      transition: opacity .3s, transform .3s;
      z-index: 100;
    }

    .toast.show {
      opacity: 1;
      transform: translateY(0);
    }

    /* ---- Lista notatek ---- */
    .notes-header {
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 16px;
      color: #1a1a2e;
    }

    .note-card {
      background: #fff;
      border-radius: 12px;
      padding: 20px 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,.06);
      margin-bottom: 12px;
      border-left: 4px solid #4a6cf7;
      animation: fadeIn .3s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .note-card .note-date {
      font-size: 13px;
      color: #888;
      margin-bottom: 4px;
    }

    .note-card .note-title {
      font-size: 17px;
      font-weight: 700;
      color: #1a1a2e;
      margin-bottom: 8px;
    }

    .note-card .note-body {
      font-size: 14px;
      color: #444;
      line-height: 1.6;
      white-space: pre-wrap;
    }

    .empty-state {
      text-align: center;
      color: #aaa;
      padding: 40px;
      font-size: 15px;
    }

    .empty-state::before {
      content: '📋';
      display: block;
      font-size: 48px;
      margin-bottom: 12px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Notatnik</h1>

    <div class="form-card">
      <label for="title">Tytuł</label>
      <input type="text" id="title" placeholder="Wpisz tytuł notatki…" autocomplete="off">

      <label for="content">Treść</label>
      <textarea id="content" placeholder="Wpisz treść notatki…"></textarea>

      <button class="btn-save" id="saveBtn" onclick="saveNote()">💾 Zapisz notatkę</button>
    </div>

    <h2 class="notes-header">Zapisane notatki</h2>
    <div id="notesList"></div>
  </div>

  <div class="toast" id="toast">✓ Notatka zapisana!</div>

  <script>
    async function loadNotes() {
      try {
        const resp = await fetch('/api/notes');
        const data = await resp.json();
        renderNotes(data.notes);
      } catch (e) {
        console.error('Błąd ładowania notatek:', e);
      }
    }

    function renderNotes(notes) {
      const list = document.getElementById('notesList');
      if (!notes || notes.length === 0) {
        list.innerHTML = '<div class="empty-state">Brak notatek — dodaj pierwszą!</div>';
        return;
      }
      list.innerHTML = notes.map(n => `
        <div class="note-card">
          <div class="note-date">${escHtml(n.date)}</div>
          <div class="note-title">${escHtml(n.title)}</div>
          <div class="note-body">${escHtml(n.body)}</div>
        </div>
      `).join('');
    }

    function escHtml(s) {
      const d = document.createElement('div');
      d.textContent = s;
      return d.innerHTML;
    }

    async function saveNote() {
      const titleEl = document.getElementById('title');
      const contentEl = document.getElementById('content');
      const title = titleEl.value.trim();
      const content = contentEl.value.trim();

      if (!title) { titleEl.focus(); return; }
      if (!content) { contentEl.focus(); return; }

      const btn = document.getElementById('saveBtn');
      btn.disabled = true;

      try {
        const resp = await fetch('/api/notes', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, content })
        });

        if (resp.ok) {
          titleEl.value = '';
          contentEl.value = '';
          showToast();
          await loadNotes();
        }
      } catch (e) {
        console.error('Błąd zapisu:', e);
      } finally {
        btn.disabled = false;
      }
    }

    function showToast() {
      const t = document.getElementById('toast');
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 2000);
    }

    // Enter w polu tytułu → przenieś do treści
    document.getElementById('title').addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); document.getElementById('content').focus(); }
    });

    // Ctrl+Enter w treści → zapisz
    document.getElementById('content').addEventListener('keydown', e => {
      if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); saveNote(); }
    });

    loadNotes();
  </script>
</body>
</html>'''


def parse_notes(content):
    """Parsuj plik notatki.md na listę słowników {date, title, body}."""
    notes = []
    if not content.strip():
        return notes

    # Dzielimy po nagłówkach ## — każdy wpis zaczyna się od ## DATA — Tytuł
    parts = re.split(r'^(?=## )', content, flags=re.MULTILINE)

    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Pierwsza linia to nagłówek
        lines = part.split('\n', 1)
        header = lines[0]
        body = lines[1].strip() if len(lines) > 1 else ''

        # ## 2026-09-08 14:32 — Tytuł notatki
        m = re.match(r'^##\s+(.+?)\s+[—–-]\s+(.+)$', header)
        if m:
            date_str = m.group(1)
            title = m.group(2)
            notes.append({'date': date_str, 'title': title, 'body': body})
        else:
            # Fallback: cały nagłówek jako tytuł
            notes.append({'date': '', 'title': header.lstrip('# '), 'body': body})

    return notes


def read_notes_file():
    """Odczytaj zawartość pliku notatki.md."""
    if not os.path.exists(NOTES_FILE):
        return ''
    with open(NOTES_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def save_note(title, content):
    """Dodaj nową notatkę na początek pliku notatki.md."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    entry = f"## {now} — {title}\n\n{content}\n"

    existing = read_notes_file().strip()

    if existing:
        new_content = entry + '\n' + existing + '\n'
    else:
        new_content = entry + '\n'

    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)


class NotesHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Cichy log — tylko istotne informacje
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))

        elif self.path == '/api/notes':
            raw = read_notes_file()
            notes = parse_notes(raw)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'notes': notes}, ensure_ascii=False).encode('utf-8'))

        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/api/notes':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)

            title = data.get('title', '').strip()
            content = data.get('content', '').strip()

            if not title or not content:
                self.send_error(400, 'Tytuł i treść są wymagane')
                return

            save_note(title, content)

            self.send_response(201)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}, ensure_ascii=False).encode('utf-8'))

        else:
            self.send_error(404)


if __name__ == '__main__':
    print(f"🗒️  Notatnik działa na http://localhost:{PORT}")
    print(f"📁 Notatki zapisywane do: {NOTES_FILE}")
    print("   Ctrl+C aby zakończyć\n")
    server = http.server.HTTPServer(('127.0.0.1', PORT), NotesHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Notatnik zamknięty.")
        server.server_close()
