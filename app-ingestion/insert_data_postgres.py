import os
import requests
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Mapeamentos de valores codificados da API OpenSky
# ---------------------------------------------------------------------------

POSITION_SOURCE_MAP = {
    0: "ADS-B",
    1: "ASTERIX",
    2: "MLAT",
    3: "FLARM"
}

CATEGORY_MAP = {
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

# Colunas retornadas pela API OpenSky.
# A API anônima retorna 17 campos; com autenticação retorna 18 (inclui category).
OPENSKY_COLUMNS_17 = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
    "spi", "position_source"
]

OPENSKY_COLUMNS_18 = OPENSKY_COLUMNS_17 + ["category"]


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------

def get_connection():
    """Retorna uma conexão com o PostgreSQL usando variáveis de ambiente."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        dbname=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )


def create_table_if_not_exists(conn):
    """Cria a tabela de destino caso ela ainda não exista."""
    ddl = """
    CREATE TABLE IF NOT EXISTS opensky_api_states_all (
        icao24                TEXT,
        callsign              TEXT,
        origin_country        TEXT,
        time_position         DOUBLE PRECISION,
        last_contact          BIGINT,
        longitude             DOUBLE PRECISION,
        latitude              DOUBLE PRECISION,
        baro_altitude         DOUBLE PRECISION,
        on_ground             BOOLEAN,
        velocity              DOUBLE PRECISION,
        true_track            DOUBLE PRECISION,
        vertical_rate         DOUBLE PRECISION,
        sensors               DOUBLE PRECISION,
        geo_altitude          DOUBLE PRECISION,
        squawk                DOUBLE PRECISION,
        spi                   BOOLEAN,
        position_source       INTEGER,
        category              DOUBLE PRECISION,
        position_source_label TEXT,
        time                  BIGINT
    );
    """
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def postgres_insert(df):
    """Insere o DataFrame no PostgreSQL de forma eficiente via execute_values."""
    conn = None
    try:
        conn = get_connection()
        create_table_if_not_exists(conn)

        cols = list(df.columns)
        query = f"INSERT INTO opensky_api_states_all ({', '.join(cols)}) VALUES %s"
        values = [tuple(row) for row in df.itertuples(index=False, name=None)]

        with conn.cursor() as cursor:
            execute_values(cursor, query, values)

        conn.commit()
        print(f"Inserção bem-sucedida! {len(values)} registros inseridos.")

    except Exception as e:
        print(f"Erro ao executar a inserção: {e}")
        if conn:
            conn.rollback()

    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Coleta de dados da API OpenSky
# ---------------------------------------------------------------------------

def fetch_opensky_data():
    """Consulta a API da OpenSky Network e retorna o DataFrame normalizado."""
    url = "https://opensky-network.org/api/states/all"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Erro ao acessar API: {response.status_code}")
        return None

    data = response.json()
    snapshot_time = data["time"]

    # Detectar dinamicamente quantas colunas a API retornou (17 sem auth, 18 com auth)
    first_state = data["states"][0] if data["states"] else []
    columns = OPENSKY_COLUMNS_18 if len(first_state) == 18 else OPENSKY_COLUMNS_17

    df = pd.DataFrame(data["states"], columns=columns)

    # Normalização: mapear códigos numéricos para descrições legíveis
    if "category" in df.columns:
        df["category"] = df["category"].map(CATEGORY_MAP)
    else:
        df["category"] = None  # coluna ausente na API anônima

    df["position_source_label"] = df["position_source"].map(POSITION_SOURCE_MAP)

    # Adicionar o timestamp do snapshot
    df["time"] = snapshot_time

    return df, snapshot_time


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = fetch_opensky_data()

    if result is None:
        exit(1)

    df, snapshot_time = result

    # Salvar backup local em CSV
    csv_path = f"flights_data_{snapshot_time}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"Arquivo '{csv_path}' salvo com sucesso!")

    # Persistir no PostgreSQL
    postgres_insert(df)
