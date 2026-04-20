from flask import Flask, jsonify, request
from neo4j import GraphDatabase

app = Flask(__name__)

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "Tina2014!")
)

@app.route("/graph-summary", methods=["GET"])
def graph_summary():
    with driver.session() as session:
        driver_count = session.run("MATCH (d:Driver) RETURN count(d) AS c").single()["c"]
        company_count = session.run("MATCH (c:Company) RETURN count(c) AS c").single()["c"]
        area_count = session.run("MATCH (a:Area) RETURN count(a) AS c").single()["c"]
        trip_count = session.run("MATCH ()-[t:TRIP]->() RETURN count(t) AS c").single()["c"]

        return jsonify({
            "driver_count": driver_count,
            "company_count": company_count,
            "area_count": area_count,
            "trip_count": trip_count
        })
    
@app.route("/top-companies", methods=["GET"])
def top_companies():
    n = int(request.args.get("n"))
    with driver.session() as session:
        top_companies = session.run("""
            MATCH (d:Driver)-[:TRIP]->() 
            MATCH (d)-[:WORKS_FOR]->(c:Company)
            RETURN c.name AS name, count(*) AS trip_count 
            ORDER BY trip_count DESC 
            LIMIT $n
            """,n=n
        ).data()
    return jsonify({"companies": top_companies})

@app.route("/high-fare-trips", methods=["GET"])
def high_fare_trips():
    area = int(request.args.get("area_id"))
    min_fare = float(request.args.get("min_fare"))
    with driver.session() as session:
        high_fare_trips = session.run("""
            MATCH (d:Driver)-[t:TRIP]->(a:Area {area_id: $area_id})
            WHERE t.fare > $min_fare
            RETURN t.trip_id as trip_id, t.fare AS fare, t.driver_id AS driv>
            ORDER BY t.fare DESC 
            """, area_id=area, min_fare=min_fare
        ).data()
    return jsonify({"trips": high_fare_trips})

@app.route("/co-area-drivers", methods=["GET"])
def co_area_drivers():
    area = int(request.args.get("area_id"))
    with driver.session() as session:
        co_area_drivers = session.run("""
            (d1:Driver)-[:TRIP]->(a:Area)<-[:TRIP]-(d2:Driver)
            RETURN d.driver_id AS driver_id, count(*) AS shared_areas
            ORDER BY shared_areas DESC
            """, area_id=area
        ).data()
    return jsonify({"co_area_drivers": co_area_drivers})

@app.route("/avg-fare-by-company", methods=["GET"])
def avg_fare_by_company():
    with driver.session() as session:
        avg_fare_by_company = session.run("""
            MATCH (d:Driver)-[t:TRIP]->()
            MATCH (d)-[WORKS_FOR]->(c:Company)
            RETURN c.name AS name, avg(t.fare) AS round(avg_fare, 2)
            ORDER BY avg_fare DESC
            """).data()
    return jsonify({"companies": avg_fare_by_company})

app.run(host="0.0.0.0", port=5000)
