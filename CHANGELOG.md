# Changelog

## Scraper Client 2.0 - 2026-08-30

### Poprawione

- Uporządkowano strukturę wyników po scrapowaniu.
- Zdjęcia są trzymane w `outputs/images/<segment-z-linku>/`, a nie luzem ani w folderach obok `csv`, `excel` i `images`.
- Nazwa folderu ze zdjęciami zawsze zgadza się z segmentem po `/produkty/` w publicznym linku.
- Eksport CSV i Excel dostaje kolumny `zdj1`, `zdj2`, `zdj3` itd. z publicznymi linkami do zdjęć.
- Linki do zdjęć są generowane na podstawie pola `Domena zdjęć` z `ADAPTER_REQUEST.md`, np. `https://mojadomena.pl/produkty/[marka albo kategoria]/[sku].[rozszerzenie]`.
- Linki w Excelu są zapisywane jako klikalne hiperłącza.
- Dodano obsługę polskich znaków w nazwach folderów, np. `Łóżka dziecięce` -> `lozka-dzieciece`.
- Wyczyściliśmy paczkę klienta z adaptera konkretnej strony, żeby repozytorium było surowym starterem.
- `outputs/` zawiera tylko puste katalogi startowe z `.gitkeep`.
- Dodano testy regresyjne dla porządkowania zdjęć i generowania linków.

### Dla klienta

Po pobraniu repozytorium klient uzupełnia `ADAPTER_REQUEST.md`, tworzy adapter i uruchamia scraper. Wyniki trafiają do:

```text
outputs/
|-- csv/
|-- excel/
`-- images/
    `-- segment-z-linku-po-produkty/
```
