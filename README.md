# Scraper Client

Gotowa paczka klienta do uruchamiania frameworka scrapującego produkty.

Framework służy do pobierania danych produktowych takich jak:

- SKU
- EAN
- nazwa produktu
- opis
- marka
- kategoria
- cena
- dostępność
- zdjęcia

Wyniki trafiają do folderu `outputs`.

## Struktura

Po rozpakowaniu najważniejsze są dwa foldery:

- `outputs` - pliki wynikowe oraz pobrane zdjęcia
- `data` - pliki techniczne frameworka i adapterów

Nie usuwaj `data/framework`, bo zawiera chroniony runtime frameworka.

## Instalacja

Wymagania:

- Windows 64-bit
- Python 3.12

W folderze projektu uruchom:

```bash
python -m pip install -r requirements.txt
```

## Konfiguracja Adaptera

Przed tworzeniem adaptera uzupełnij plik `ADAPTER_REQUEST.md`.

Przykład:

```md
# Adapter Request

URL: https://example-shop.pl
Domena zdjęć: https://mojadomena.pl/produkty/[sku].[rozszerzenie]
Marka: marka-produktu

Pola do pobrania:
- name
- description
- sku
- ean
- images

Uwagi:
- pobierz produkty z kategorii meble
- zapisz wszystkie zdjęcia produktu
```

Znaczenie pól:

- `URL` - adres strony/sklepu, dla którego ma powstać adapter
- `Domena zdjęć` - publiczna domena, która zostanie użyta do generowania linków do zdjęć
- `Marka` - segment URL w linkach do zdjęć; jeśli puste, framework użyje marki z danych produktu
- `Pola do pobrania` - lista danych, które adapter ma wyciągać
- `Uwagi` - dodatkowe zasady dla osoby lub AI tworzącej adapter

## Tworzenie Adaptera

Adapter tworzy się na bazie szablonu:

```bash
python create_adapter.py --name nazwa_sklepu --mode playwright
```

Dostępne tryby:

- `requests` - dla prostych stron HTML
- `playwright` - dla stron dynamicznych, JavaScript, paginacji i interakcji
- `api` - dla źródeł z API
- `xml` - dla feedów XML
- `csv` - dla danych z CSV

Po utworzeniu szkieletu adapter trzeba uzupełnić pod konkretną stronę. W Codexie można użyć promptu:

```text
Na podstawie ADAPTER_REQUEST.md uzupełnij adapter dla tej strony.
Pobieraj name, description, sku, ean i images.
```

## Uruchamianie Scrapera

Po przygotowaniu adaptera:

```bash
python run.py --adapter nazwa_sklepu --export csv,excel
```

Wyniki pojawią się w:

- `outputs/csv`
- `outputs/excel`
- `outputs/images`

## Linki Do Zdjęć

Zdjęcia są pobierane i nazywane na podstawie SKU:

```text
outputs/images/SKU.jpg
outputs/images/SKU_1.webp
outputs/images/SKU_2.png
```

Po zakończeniu scrapowania `run.py` automatycznie dopisuje do eksportów CSV/XLSX kolumny:

- `zdj`
- `zdj2`
- `zdj3`
- kolejne, jeśli produkt ma więcej zdjęć

Przykład dla:

```md
Domena zdjęć: https://mojadomena.pl
Marka: marka
```

oraz zdjęć:

```text
ABC123.jpg
ABC123_1.webp
ABC123_2.png
```

w eksporcie pojawi się:

```text
zdj  = https://mojadomena.pl/marka/ABC123.jpg
zdj2 = https://mojadomena.pl/marka/ABC123_1.webp
zdj3 = https://mojadomena.pl/marka/ABC123_2.png
```

Jeśli `Domena zdjęć` jest pusta, generowanie publicznych linków zostanie pominięte.

## Ważne Uwagi

- Ta paczka jest przygotowana pod Windows 64-bit i Python 3.12.
- Folder `outputs` jest miejscem na wygenerowane dane.
- Nie commituj realnych wyników scrapowania, zdjęć ani cache.

## Szybki Workflow

1. Uzupełnij `ADAPTER_REQUEST.md`.
2. Utwórz szkielet adaptera:

   ```bash
   python create_adapter.py --name sklep --mode playwright
   ```

3. Uzupełnij adapter ręcznie albo przez Codexa.
4. Uruchom:

   ```bash
   python run.py --adapter sklep --export csv,excel
   ```

5. Odbierz dane z `outputs/csv`, `outputs/excel` i `outputs/images`.
