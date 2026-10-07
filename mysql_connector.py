import pymysql
from pymysql.connections import Connection
from config import MYSQL_CONFIG
from typing import Any, Optional

# Raised when MySQL is unreachable or credentials are wrong
DatabaseAccessError = pymysql.OperationalError


def _get_connection() -> Connection:
    """
    Connect to Database and return a connection object.
    :return: Object  pymysql.connections.Connection
    """
    return pymysql.connect(**MYSQL_CONFIG)


def test_connection() -> None:
    """
    Check if MySQL database connection is working.
    """
    close_connection(_get_connection())


def get_genres() -> dict[str, list[int]]:
    """
    Get full list of genres and their years from database.
    :return: dict with genres as keys and list of years as values.
    """
    conn = _get_connection()
    query = """
    SELECT 
    c.name
    , MIN(f.release_year) AS min_year
    , MAX(f.release_year) AS max_year 
    FROM category c 
    JOIN film_category fc ON fc.category_id = c.category_id 
    JOIN film f ON fc.film_id = f.film_id 
    GROUP BY c.name;"""
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return {g[0]: [g[1], g[2]] for g in cursor.fetchall()}
    finally:
        close_connection(conn)


def get_rating() -> list[str]:
    """
    Get list of unique film ratings from the database.
    :return: list of rating strings.
    """
    conn = _get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT(rating) FROM film")
            return [row[0] for row in cursor.fetchall()]
    finally:
        close_connection(conn)


def get_years_range() -> tuple[int, int]:
    """
    Find years range in whole database
    :return: tuple whit min year and max year
    """
    conn = _get_connection()
    query = "SELECT MIN(release_year), MAX(release_year) FROM film"
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()[0]
    finally:
        close_connection(conn)


_FILM_LIST_SELECT = """
SELECT
    f.film_id
    , f.title
    , f.release_year
    , f.rating
FROM film f"""


def build_filters(params: dict[str, Any], query_params: list[Any]) -> str:
    """
    Build SQL query filters and append parameters dynamically.
    :return: SQL string containing filters.
    """
    query = ""
    if "genre" in params:
        query += " JOIN film_category fc ON fc.film_id = f.film_id"
        query += " JOIN category c ON fc.category_id = c.category_id"
        query += " WHERE c.name = %s"
        query_params.append(params["genre"])
    else:
        query += " WHERE 1 = 1"
    if "year_from" in params:
        query_params.append(params["year_from"])
        query_params.append(params["year_to"])
        query += " AND f.release_year BETWEEN %s AND %s"
    if "keyword" in params:
        query_params.append(f'%{params["keyword"]}%')
        query += " AND f.title LIKE %s"
    if "rating" in params:
        query_params.append(params["rating"])
        query += " AND f.rating = %s"
    return query


def get_first_films(params: dict[str, Any], limit: int) \
        -> tuple[tuple[Any,...], int]:
    """
    find firs part of films list and count of all films for this params
    :return: tuple with films list and total count
    """
    query_params = []
    query = build_filters(params, query_params)
    conn = _get_connection()
    try:
        with (conn.cursor() as cursor):
            count_q = "SELECT COUNT(f.film_id) as total FROM film f" + query
            cursor.execute(count_q, tuple(query_params))
            total_count = cursor.fetchone()[0]

            search_q = (_FILM_LIST_SELECT + query +
                        " ORDER BY f.film_id LIMIT %s;")
            cursor.execute(search_q, tuple(query_params+[limit]))
            films = cursor.fetchall()
            return films, total_count
    finally:
        close_connection(conn)


def get_next_films(params: dict[str, Any], limit: int, offset: int) \
        -> tuple[Any, ...]:
    """
    find limit films by params and offset
    :return: tuple of film records.
    """
    query_params = []
    query = build_filters(params, query_params)
    conn = _get_connection()
    try:
        with conn.cursor() as cursor:
            search_q = (_FILM_LIST_SELECT + query +
                        " ORDER BY f.film_id LIMIT %s OFFSET %s;")
            cursor.execute(search_q, tuple(query_params + [limit] + [offset]))
            films = cursor.fetchall()
            return films
    finally:
        close_connection(conn)


def get_film_by_id(film_id: int) -> Optional[tuple[Any, ...]]:
    """
    get full information about film by film_id
    :return: tuple with film info or None
    """
    conn = _get_connection()
    try:
        with (conn.cursor() as cursor):
            search_q = """
            SELECT 
                f.title
                , f.description 
                , f.release_year
                , f.length 
                , f.rating
                , GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') AS genres
                , GROUP_CONCAT(DISTINCT CONCAT(a.first_name, ' ', a.last_name) 
                SEPARATOR ', ') AS actors 
            FROM film f 
            LEFT JOIN film_category fc ON f.film_id = fc.film_id 
            LEFT JOIN category c ON fc.category_id = c.category_id 
            LEFT JOIN film_actor fa ON f.film_id = fa.film_id 
            LEFT JOIN actor a ON fa.actor_id = a.actor_id 
                WHERE f.film_id = %s
            GROUP BY f.film_id;
            """
            cursor.execute(search_q, (film_id,))
            film = cursor.fetchone()
            return film
    finally:
        close_connection(conn)


def close_connection(connection: Connection) -> None:
    """
    safely close connection
    """
    try:
        connection.close()
    except pymysql.err.MySQLError:
        pass
