import requests
import psycopg2
import pandas as pd


def postgres_insert(data):
    try:
        conn = psycopg2.connect(
            host="host",
            dbname="dbname",
            user="user",
            password="password",
            port="port"
        )
        
        columns = list(data[0].keys())
        placeholders = ", ".join(["%s"] * len(columns))
        columns_str = ", ".join(columns)

        query = f"INSERT INTO opensky_api_states_all ({columns_str}) VALUES ({placeholders})"

        values = [tuple(d[col] for col in columns) for d in data]

        cursor = conn.cursor()
        cursor.executemany(query, values)
        conn.commit()
        print("Inserção bem-sucedida!")

    except Exception as e:
        print(f"Erro ao executar a inserção: {e}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()
    
url = "https://opensky-network.org/api/states/all"

response = requests.get(url)

position_source_map = {
    0:"ADS-B",
    1:"ASTERIX",
    2:"MLAT",
    3:"FLARM"
}

category_map = {
    0: "No information at all",
    1: "No ADS-B Emitter Category Information",
    2: "Light (< 15500 lbs)",
    3: "Small (15500 to 75000 lbs)",
    4: "Large (75000 to 300000 lbs)",
    5: "High Vortex Large (aircraft such as B-757)",
    6: "Heavy (> 300000 lbs)",
    7: "High Performance (> 5g acceleration and 400 kts)",
    8: "Rotorcraft",
    9: "Glider / sailplane",
    10: "Lighter-than-air",
    11: "Parachutist / Skydiver",
    12: "Ultralight / hang-glider / paraglider",
    13: "Reserved",
    14: "Unmanned Aerial Vehicle",
    15: "Space / Trans-atmospheric vehicle",
    16: "Surface Vehicle - Emergency Vehicle",
    17: "Surface Vehicle - Service Vehicle",
    18: "Point Obstacle (includes tethered balloons)",
    19: "Cluster Obstacle",
    20: "Line Obstacle"
}


if response.status_code == 200:
    data = response.json()

    columns = [
        "icao24", "callsign", "origin_country", "time_position", "last_contact",
        "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
        "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
        "spi", "position_source"
    ]
    
    time = data['time']
    df = pd.DataFrame(data["states"], columns=columns)

    df["category"] = df["category"].map(category_map)
    df["position_sourcey"] = df["position_source"].map(position_source_map)
    df["time"] = time

    df.to_csv(f"flights_data_{time}.csv", index=False, encoding="utf-8")
    
    print("Arquivo 'flights_data.csv' salvo com sucesso!")

    execute_insert(df)
else:
    print(f"Erro ao acessar API: {response.status_code}")
