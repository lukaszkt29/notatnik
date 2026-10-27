using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Text.Json;
using Avalonia.Controls;
using Avalonia.Interactivity;

namespace notatnik;

public partial class MainWindow : Window
{
    private static readonly string NotesFilePath =
        Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "notatki.json");

    private ObservableCollection<Note> _notes = new();

    public MainWindow()
    {
        InitializeComponent();
        LoadNotes();
        NotesList.ItemsSource = _notes;
    }

    private void OnSaveClick(object? sender, RoutedEventArgs e)
    {
        var title = TitleBox.Text?.Trim();
        var content = ContentBox.Text?.Trim();

        if (string.IsNullOrEmpty(title) && string.IsNullOrEmpty(content))
            return;

        var note = new Note
        {
            Title = string.IsNullOrEmpty(title) ? "(bez tytułu)" : title,
            Content = content ?? "",
            CreatedAt = DateTime.Now
        };

        _notes.Insert(0, note);
        SaveNotes();

        TitleBox.Text = "";
        ContentBox.Text = "";
    }

    private void OnDeleteClick(object? sender, RoutedEventArgs e)
    {
        if (NotesList.SelectedItem is Note selected)
        {
            _notes.Remove(selected);
            SaveNotes();
            TitleBox.Text = "";
            ContentBox.Text = "";
        }
    }

    private void OnNoteSelected(object? sender, SelectionChangedEventArgs e)
    {
        if (NotesList.SelectedItem is Note selected)
        {
            TitleBox.Text = selected.Title;
            ContentBox.Text = selected.Content;
        }
    }

    private void SaveNotes()
    {
        var options = new JsonSerializerOptions { WriteIndented = true };
        var json = JsonSerializer.Serialize(_notes.ToList(), options);
        File.WriteAllText(NotesFilePath, json);
    }

    private void LoadNotes()
    {
        if (!File.Exists(NotesFilePath))
            return;

        try
        {
            var json = File.ReadAllText(NotesFilePath);
            var notes = JsonSerializer.Deserialize<System.Collections.Generic.List<Note>>(json);
            if (notes != null)
            {
                _notes = new ObservableCollection<Note>(notes);
            }
        }
        catch
        {
            // Jeśli plik jest uszkodzony, zaczynamy od pustej listy
            _notes = new ObservableCollection<Note>();
        }
    }
}

public class Note
{
    public string Title { get; set; } = "";
    public string Content { get; set; } = "";
    public DateTime CreatedAt { get; set; }

    public string Preview =>
        Content.Length > 80 ? Content[..80] + "…" : Content;

    public string DateText =>
        CreatedAt.ToString("dd.MM.yyyy HH:mm");
}