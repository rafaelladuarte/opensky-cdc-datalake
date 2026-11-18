import logging
import os
import time

import pandas as pd
import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("opensky-ingestion")

OPENSKY_URL = "https://opensky-network.org/api/states/all"
REQUEST_TIMEOUT_SEC = float(os.getenv("REQUEST_TIMEOUT_SEC", "20"))
REQUEST_RETRIES = int(os.getenv("REQUEST_RETRIES", "5"))
# Intervalo entre coletas. A API anônima limita ~1 requisição a cada 10 s
# (e uma cota diária), então o padrão é conservador.
POLL_INTERVAL_SEC = int(os.getenv("POLL_INTERVAL_SEC", "60"))
SAVE_CSV_BACKUP = os.getenv("SAVE_CSV_BACKUP", "false").lower() == "true"


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
        icao24                TEXT PRIMARY KEY,
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
        squawk                TEXT,
        spi                   BOOLEAN,
        position_source       INTEGER,
        category              TEXT,
        position_source_label TEXT,
        time                  BIGINT
    );
    """
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def postgres_upsert(df):
    """
    Faz UPSERT por icao24. Aeronaves já conhecidas geram UPDATE (e não um novo
    INSERT), de modo que o Debezium capture eventos de alteração reais.
    Só atualiza quando o registro recebido é mais recente (last_contact).
    """
    # ON CONFLICT não pode afetar a mesma linha duas vezes no mesmo comando
    df = df.dropna(subset=["icao24"]).drop_duplicates(subset="icao24", keep="last")
    # NaN/NaT -> None para virar NULL no PostgreSQL
    df = df.astype(object).where(df.notna(), None)

    cols = list(df.columns)
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "icao24")
    query = (
        f"INSERT INTO opensky_api_states_all ({', '.join(cols)}) VALUES %s "
        f"ON CONFLICT (icao24) DO UPDATE SET {updates} "
        f"WHERE opensky_api_states_all.last_contact IS NULL "
        f"OR EXCLUDED.last_contact > opensky_api_states_all.last_contact"
    )
    values = [tuple(row) for row in df.itertuples(index=False, name=None)]

    conn = get_connection()
    try:
        create_table_if_not_exists(conn)
        with conn.cursor() as cursor:
            execute_values(cursor, query, values, page_size=1000)
        conn.commit()
        logger.info("Upsert concluído: %d registros processados.", len(values))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Coleta de dados da API OpenSky
# ---------------------------------------------------------------------------

def build_session():
    """Sessão HTTP com retry e backoff exponencial para erros transitórios."""
    retry = Retry(
        total=REQUEST_RETRIES,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def fetch_opensky_data(session=None):
    """Consulta a API da OpenSky Network e retorna (DataFrame, snapshot_time) ou None."""
    session = session or build_session()
    try:
        response = session.get(OPENSKY_URL, timeout=REQUEST_TIMEOUT_SEC)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Erro ao acessar a API OpenSky: %s", e)
        return None

    data = response.json()
    snapshot_time = data["time"]
    if not data.get("states"):
        logger.warning("API retornou nenhum estado.")
        return None

    # Detectar dinamicamente quantas colunas a API retornou (17 sem auth, 18 com auth)
    first_state = data["states"][0]
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

def run_once(session):
    result = fetch_opensky_data(session)
    if result is None:
        return
    df, snapshot_time = result

    if SAVE_CSV_BACKUP:
        csv_path = f"flights_data_{snapshot_time}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info("Backup '%s' salvo.", csv_path)

    postgres_upsert(df)


if __name__ == "__main__":
    session = build_session()
    logger.info("Iniciando ingestão (intervalo: %ds).", POLL_INTERVAL_SEC)
    try:
        while True:
            started = time.monotonic()
            try:
                run_once(session)
            except Exception:
                logger.exception("Falha no ciclo de ingestão; tentando no próximo ciclo.")
            elapsed = time.monotonic() - started
            time.sleep(max(0, POLL_INTERVAL_SEC - elapsed))
    except KeyboardInterrupt:
        logger.info("Encerrado pelo usuário.")
