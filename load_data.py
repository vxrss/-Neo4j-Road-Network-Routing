import arcpy
import math
import csv
import os
import time
import argparse
from neo4j import GraphDatabase

arcpy.env.overwriteOutput = True



parser = argparse.ArgumentParser(
    description="Import danych BDOT10k do Neo4j i inicjalizacja GDS"
)

parser.add_argument(
    "shp_path",
    help="Ścieżka do pliku SHP (BDOT10k)"
)

parser.add_argument(
    "--uri",
    default="bolt://127.0.0.1:7687",
    help="URI Neo4j (domyślnie bolt://127.0.0.1:7687)"
)

parser.add_argument(
    "--user",
    default="neo4j",
    help="Użytkownik Neo4j (domyślnie neo4j)"
)

parser.add_argument(
    "--password",
    default="adminadmin",
    help="Hasło Neo4j"
)

args = parser.parse_args()

PATH = args.shp_path
NEO4J_URI = args.uri
NEO4J_AUTH = (args.user, args.password)

OUT_DIR = "wyniki"
TOLERANCJA = 0.5
MAX_SPEED_KMH = 140

SPEED_MAP = {
    "A": 140, "S": 120, "GP": 100,
    "G": 90, "Z": 50, "L": 50,
    "D": 50, "I": 50
}



def load_data(path):
    fields = ["Shape@", "klasaDrogi"]
    data = []
    with arcpy.da.SearchCursor(path, fields) as cur:
        for geom, klasa in cur:
            if not geom:
                continue
            data.append({
                "start": (geom.firstPoint.X, geom.firstPoint.Y),
                "end": (geom.lastPoint.X, geom.lastPoint.Y),
                "length": geom.length,
                "klasa": klasa
            })
    return data


def find_or_create(point, vertices):
    for vid, (x, y) in vertices.items():
        if math.hypot(x - point[0], y - point[1]) <= TOLERANCJA:
            return vid
    vid = len(vertices) + 1
    vertices[vid] = point
    return vid





data = load_data(PATH)

vertices = {}
edges = []

for rec in data:
    v1 = find_or_create(rec["start"], vertices)
    v2 = find_or_create(rec["end"], vertices)

    speed = SPEED_MAP.get(rec["klasa"], 50) / 3.6
    time_s = rec["length"] / speed

    edges.append((v1, v2, rec["length"], time_s, rec["klasa"]))



os.makedirs(OUT_DIR, exist_ok=True)

vertices_csv = os.path.join(OUT_DIR, "vertices.csv")
edges_csv = os.path.join(OUT_DIR, "edges.csv")

with open(vertices_csv, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "x", "y", "x_astar", "y_astar"])
    for vid, (x, y) in vertices.items():
        w.writerow([
            vid, x, y,
            x / MAX_SPEED_KMH,
            y / MAX_SPEED_KMH
        ])

with open(edges_csv, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["from", "to", "length", "time", "class"])
    for e in edges:
        w.writerow(e)



driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

def run(q, p=None):
    with driver.session() as s:
        s.run(q, p or {})


run("MATCH (n) DETACH DELETE n")


with open(vertices_csv) as f:
    r = csv.DictReader(f)
    for row in r:
        run("""
        CREATE (:Node {
            id:$id, x:$x, y:$y,
            x_astar:$xa, y_astar:$ya
        })
        """, {
            "id": int(row["id"]),
            "x": float(row["x"]),
            "y": float(row["y"]),
            "xa": float(row["x_astar"]),
            "ya": float(row["y_astar"])
        })

run("""
CREATE CONSTRAINT node_id IF NOT EXISTS
FOR (n:Node) REQUIRE n.id IS UNIQUE
""")


with open(edges_csv) as f:
    r = csv.DictReader(f)
    for row in r:
        run("""
        MATCH (a:Node {id:$f}), (b:Node {id:$t})
        CREATE (a)-[:ROAD {length:$l, time:$ti, class:$c}]->(b)
        CREATE (b)-[:ROAD {length:$l, time:$ti, class:$c}]->(a)
        """, {
            "f": int(row["from"]),
            "t": int(row["to"]),
            "l": float(row["length"]),
            "ti": float(row["time"]),
            "c": row["class"]
        })



run("CALL gds.graph.drop('roads_length', false)")
run("CALL gds.graph.drop('roads_time', false)")

run("""
CALL gds.graph.project(
  'roads_length',
  'Node',
  { ROAD:{orientation:'UNDIRECTED', properties:'length'} }
)
""")

run("""
CALL gds.graph.project(
  'roads_time',
  'Node',
  { ROAD:{orientation:'UNDIRECTED', properties:'time'} },
  { nodeProperties:['x_astar','y_astar'] }
)
""")

driver.close()

