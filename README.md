# Neo4j Road Network Routing

Aplikacja geoinformacyjna służąca do modelowania sieci drogowej na podstawie danych BDOT10k oraz wyznaczania tras przy użyciu grafowej bazy danych Neo4j i modułu Graph Data Science (GDS).

Projekt umożliwia wyznaczanie:

-  trasy najkrótszej (algorytm Dijkstry)
- trasy najszybszej (algorytm A*)

---

##  Opis projektu

W projekcie wykorzystano dane BDOT10k do budowy grafowego modelu sieci drogowej.  
Odcinki dróg zostały odwzorowane jako relacje grafu, a ich punkty początkowe i końcowe jako węzły.

Aplikacja umożliwia interaktywne wskazywanie punktów startu i końca na mapie oraz porównanie dwóch kryteriów optymalizacji:

- minimalna długość trasy,
- minimalny czas przejazdu.

Przykładowe dane wykorzystane w projekcie dotyczą obszaru miasta **Toruń**.

---

## Model danych

### Węzły (`:Node`)
- `id` – identyfikator węzła
- `x`, `y` – współrzędne PUWG 1992
- `x_astar`, `y_astar` – przeskalowane współrzędne wykorzystywane jako heurystyka A*

### Relacje (`:ROAD`)
- `length` – długość odcinka [m]
- `time` – czas przejazdu [s]
- `class` – klasa drogi (BDOT10k)

Graf jest modelowany jako nieskierowany.

---

## Wymagania

- Python 3.10+
- Neo4j 
- Neo4j Graph Data Science (GDS)
- ArcGIS (ArcPy)
- Zainstalowane biblioteki Python (patrz `requirements.txt`)

---

##  Instalacja zależności

Zainstaluj wymagane biblioteki:

```
pip install -r requirements.txt
```


> ⚠️ Uwaga: `arcpy` nie jest instalowany przez pip — jest dostępny w środowisku ArcGIS.

---

## Konfiguracja Neo4j

Przed uruchomieniem projektu upewnij się, że:

1. Neo4j jest uruchomione lokalnie:
```
bolt://localhost:7687
```

2. Dane logowania są poprawne.

Podczas importu danych możesz podać użytkownika i hasło:

```
python load_data.py <ścieżka_do_shp> --user neo4j --password haslo
```

 **Uwaga:**  
W pliku `neo.py` również znajdują się dane logowania do bazy Neo4j.  
Jeżeli używasz innych danych niż domyślne, należy zmienić login i hasło również w tym pliku.

---

## Struktura projektu

```
Projekt2/
├── dane/              
│   └── L4_1_BDOT10k__OT_SKJZ_L.shp
│       # Przykładowe dane BDOT10k dla miasta Toruń
│
├── wyniki/            
│   └── vertices.csv, edges.csv
│       # Pliki generowane podczas importu danych
│
├── load_data.py       
│   # Import danych BDOT10k do Neo4j
│   # Budowa grafu topologicznego
│   # Wyliczanie długości i czasu przejazdu
│   # Tworzenie heurystyki A*
│   # Inicjalizacja grafów projekcyjnych GDS
│
├── neo.py             
│   # Obsługa połączenia z Neo4j
│   # Transformacja współrzędnych (WGS84 → PUWG 1992)
│   # Implementacja zapytań Dijkstra i A*
│   # Pobieranie współrzędnych trasy
│
├── gui.py             
│   # Interfejs użytkownika (PyQt5)
│   # Obsługa komunikacji z mapą (Leaflet)
│   # Wyświetlanie tras i statystyk
│
├── map.html           
│   # Wizualizacja mapy (Leaflet + OpenStreetMap)
│   # Obsługa kliknięć i rysowanie tras
│
├── requirements.txt   
│   # Lista wymaganych bibliotek Python
│
└── README.md
```

---

##  Uruchomienie projektu

###  Import danych do Neo4j

```
python load_data.py dane/L4_1_BDOT10k__OT_SKJZ_L.shp
```

Możliwe parametry opcjonalne:

```
python load_data.py <ścieżka_do_shp> --uri bolt://localhost:7687 --user neo4j --password haslo
```

Skrypt:
- wczytuje dane BDOT10k,
- buduje graf topologiczny,
- wylicza długość i czas przejazdu,
- tworzy właściwości heurystyczne dla A* (`x_astar`, `y_astar`),
- inicjalizuje grafy projekcyjne GDS (`roads_length`, `roads_time`).

---

### Uruchom aplikację

```
python gui.py
```

Następnie kliknij dwa punkty na mapie, aby wyznaczyć trasę.

---

##  Algorytmy

### Dijkstra
- Waga: `length`
- Wynik: trasa najkrótsza

### A*
- Waga: `time`
- Heurystyka: przeskalowane współrzędne (`x_astar`, `y_astar`)
- Wynik: trasa najszybsza
