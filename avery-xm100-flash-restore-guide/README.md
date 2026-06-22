# Avery Berkel XM100 — Flash Firmware & Backup / Restore

Αναλυτικός οδηγός για backup, flash firmware (root/kernel) και app update στον ζυγό **Avery Berkel XM100**.

## Περιεχόμενα οδηγού

- **PINs πρόσβασης** — Manager Mode (4296) & Service Mode (1938)
- **Βήμα 1 — Backup** PLU/System Data & ετικετών πριν από κάθε flash
- **Βήμα 2 — Root/Kernel Flash** μέσω Service Mode (F+00+Power, USB με mtd images)
- **Βήμα 3 — App Update** μέσω φακέλου `xm_update` (αυτόματη ανίχνευση + Service Button)
- **Βήμα 4 — Restore** PLU/System Data & ετικετών
- **Βήμα 5 — Βαθμονόμηση (Calibration)**

⚠ Firmware αναφοράς: **2.3.0.11** — Κάνε πάντα backup πριν από οποιοδήποτε flash. Μην κλείσεις τον ζυγό κατά τη διάρκεια flash (κίνδυνος brick).

## Αρχεία

| Αρχείο | Περιγραφή |
|--------|-----------|
| [Avery_XM100_Flash_Restore_Guide_ICS.pdf](./Avery_XM100_Flash_Restore_Guide_ICS.pdf) | Πλήρης οδηγός σε μορφή PDF |
| [XM100_Update_Files.zip](./XM100_Update_Files.zip) | Φάκελος `xm_update` με τα .ipk αρχεία (mainapp 3.5.10.0, loadcell 1.4.1.0, printer firmware 3.6.1.0, touchscreen compensation 1.0.0.3) + update.log |
