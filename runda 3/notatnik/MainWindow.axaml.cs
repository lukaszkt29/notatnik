using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using Avalonia.Controls;
using Avalonia.Interactivity;

namespace notatnik;

public partial class MainWindow : Window
{
    private readonly string _notesFilePath;
    private readonly ObservableCollection<NoteItem> _notes = new();

    public MainWindow()
    {
        InitializeComponent();

        // Plik notatki.md obok exe / w katalogu projektu
        var baseDir = AppContext.BaseDirectory;
        _notesFilePath = Path.Combine(baseDir, "notatki.md");

        NotesList.ItemsSource = _notes;
        LoadNotes();
    }

    private void SaveButton_Click(object? sender, RoutedEventArgs e)
    {
        var title = TitleBox.Text?.Trim();
        var content = ContentBox.Text?.Trim();

        if (string.IsNullOrEmpty(title))
        {
            TitleBox.Focus();
            return;
        }

        if (string.IsNullOrEmpty(content))
        {
            ContentBox.Focus();
            return;
        }

        var now = DateTime.Now;
        var header = $"## {now:yyyy-MM-dd HH:mm} — {title}";

        // Budujemy nowy wpis
        var newEntry = header + "\n\n" + content;

        // Wczytaj istniejącą treść (jeśli jest)
        var existing = string.Empty;
        if (File.Exists(_notesFilePath))
        {
            existing = File.ReadAllText(_notesFilePath, Encoding.UTF8).TrimEnd();
        }

        // Najnowsza notatka na górze
        string final;
        if (string.IsNullOrEmpty(existing))
        {
            final = newEntry + "\n";
        }
        else
        {
            final = newEntry + "\n\n\n" + existing + "\n";
        }

        File.WriteAllText(_notesFilePath, final, new UTF8Encoding(false));

        // Wyczyść pola
        TitleBox.Text = string.Empty;
        ContentBox.Text = string.Empty;
        TitleBox.Focus();

        // Odśwież listę
        LoadNotes();
    }

    private void LoadNotes()
    {
        _notes.Clear();

        if (!File.Exists(_notesFilePath))
            return;

        var text = File.ReadAllText(_notesFilePath, Encoding.UTF8);

        // Dzielimy po nagłówkach ## (z zachowaniem nagłówka)
        var parts = Regex.Split(text, @"(?=^## )", RegexOptions.Multiline);

        foreach (var part in parts)
        {
            var trimmed = part.Trim();
            if (string.IsNullOrEmpty(trimmed))
                continue;

            // Pierwszy wiersz to nagłówek
            var lines = trimmed.Split('\n');
            var headerLine = lines[0].TrimStart('#', ' ');
            var bodyLines = lines.Skip(1).Select(l => l.Trim()).Where(l => !string.IsNullOrEmpty(l));
            var preview = string.Join(" ", bodyLines);

            if (preview.Length > 120)
                preview = preview[..120] + "…";

            _notes.Add(new NoteItem
            {
                Header = headerLine,
                Preview = preview
            });
        }
    }
}

public class NoteItem
{
    public string Header { get; set; } = string.Empty;
    public string Preview { get; set; } = string.Empty;
}
