# CP737 → UTF-8 Auto Converter

Αυτόματη μετατροπή αρχείων από DOS Greek (CP737) σε UTF-8 για Windows.

## Τι κάνει

Παρακολουθεί έναν φάκελο. Όταν το ERP/POS εξάγει αρχείο, το μετατρέπει αυτόματα σε UTF-8 ώστε να ανοίγει σωστά σε Excel, Notepad++, κ.λπ.

- Κρατά αντίγραφο ασφαλείας στον υποφάκελο `backup_cp737/`
- Δεν μετατρέπει δύο φορές το ίδιο αρχείο
- Αποθηκεύει με **UTF-8 BOM** (ανοίγει σωστά στο Excel χωρίς ρυθμίσεις)

## Εγκατάσταση

1. Βεβαιωθείτε ότι η **Python 3** είναι εγκατεστημένη ([python.org](https://www.python.org))
2. Ανοίξτε το `start_watcher.bat` με Notepad και αλλάξτε τη γραμμή:
   ```
   set WATCH_FOLDER=C:\ERP_Export
   ```
   με τον φάκελο που εξάγει το ERP σας.

3. Εκτελέστε `start_watcher.bat` — θα ξεκινήσει να παρακολουθεί.

## Αυτόματη εκκίνηση με τα Windows

Εκτελέστε `install_autostart.bat` — προσθέτει το πρόγραμμα στα Windows Startup.

## Εφάπαξ μετατροπή ενός αρχείου

```
python convert_once.py "C:\path\to\file.txt"
```

## Ρυθμίσεις (cp737_watcher.py)

| Μεταβλητή | Προεπιλογή | Περιγραφή |
|-----------|-----------|-----------|
| `WATCH_FOLDER` | `C:\ERP_Export` | Φάκελος εξαγωγής ERP |
| `BACKUP_FOLDER` | `...\backup_cp737` | Φάκελος αντιγράφων |
| `FILE_EXTENSIONS` | `.txt .csv .dat .asc` | Τύποι αρχείων |
| `CHECK_INTERVAL` | `3` δευτερόλεπτα | Συχνότητα ελέγχου |
