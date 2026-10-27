using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Text;
using Avalonia.Controls;
using Avalonia.Interactivity;

namespace notatnik;

public partial class MainWindow : Window
{
    private readonly string _filePath;
    private readonly ObservableCollection<NoteItem> _notes = new();

    public MainWindow()
    {
        InitializeComponent();

        // Plik notatki.md obok exe — ale lepiej obok projektu (CWD)
        _filePath = Path.Combine(AppContext.BaseDirectory, "notatki.md");

        NotesList.ItemsSource = _notes;
        LoadNotes();
    }

    private void SaveButton_Click(object? sender, RoutedEventArgs e)
    {
        var title = TitleBox.Text?.Trim();
        var body = ContentBox.Text?.TrimEnd();

        if (string.IsNullOrEmpty(title) && string.IsNullOrEmpty(body))
            return;

        if (string.IsNullOrEmpty(title))
            title = "Bez tytułu";

        var now = DateTime.Now;
        var header = $"## {now:yyyy-MM-dd HH:mm} — {title}";

        // Buduj nowy wpis
        var entry = new StringBuilder();
        entry.AppendLine(header);
        entry.AppendLine();
        if (!string.IsNullOrEmpty(body))
        {
            entry.AppendLine(body);
        }

        // Wczytaj istniejącą zawartość (jeśli jest)
        var existing = string.Empty;
        if (File.Exists(_filePath))
        {
            existing = File.ReadAllText(_filePath, Encoding.UTF8).TrimEnd();
        }

        // Złóż plik: nowy wpis na górze
        var sb = new StringBuilder();
        sb.Append(entry);
        if (!string.IsNullOrEmpty(existing))
        {
            sb.AppendLine();
            sb.AppendLine(existing);
        }

        File.WriteAllText(_filePath, sb.ToString(), new UTF8Encoding(false));

        // Wyczyść pola
        TitleBox.Text = string.Empty;
        ContentBox.Text = string.Empty;

        // Odśwież listę
        LoadNotes();
    }

    private void LoadNotes()
    {
        _notes.Clear();

        if (!File.Exists(_filePath))
            return;

        var lines = File.ReadAllLines(_filePath, Encoding.UTF8);
        var parsedNotes = ParseNotes(lines);

        foreach (var note in parsedNotes)
        {
            _notes.Add(note);
        }
    }

    private static List<NoteItem> ParseNotes(string[] lines)
    {
        var notes = new List<NoteItem>();
        string? currentHeader = null;
        var bodyLines = new List<string>();

        foreach (var line in lines)
        {
            if (line.StartsWith("## "))
            {
                // Zapisz poprzednią notatkę (jeśli była)
                if (currentHeader != null)
                {
                    notes.Add(BuildNoteItem(currentHeader, bodyLines));
                    bodyLines.Clear();
                }
                currentHeader = line;
            }
            else if (currentHeader != null)
            {
                bodyLines.Add(line);
            }
        }

        // Ostatnia notatka
        if (currentHeader != null)
        {
            notes.Add(BuildNoteItem(currentHeader, bodyLines));
        }

        return notes;
    }

    private static NoteItem BuildNoteItem(string header, List<string> bodyLines)
    {
        // Usuń puste linie na początku i końcu treści
        int start = 0;
        while (start < bodyLines.Count && string.IsNullOrWhiteSpace(bodyLines[start]))
            start++;

        int end = bodyLines.Count - 1;
        while (end >= start && string.IsNullOrWhiteSpace(bodyLines[end]))
            end--;

        var body = new StringBuilder();
        for (int i = start; i <= end; i++)
        {
            if (i > start) body.AppendLine();
            body.Append(bodyLines[i]);
        }

        // Wyciągnij datę i tytuł z nagłówka "## 2026-09-08 14:32 — Tytuł"
        var display = header;
        if (header.StartsWith("## "))
            display = header[3..];

        return new NoteItem { Header = display, Body = body.ToString() };
    }
}

public class NoteItem
{
    public string Header { get; set; } = string.Empty;
    public string Body { get; set; } = string.Empty;
}
