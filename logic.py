import mysql_connector
import mongo_connector
from mongo_connector import MongoError
from typing import Any, Optional


def init_app() -> bool:
    """
    Initialize the application: MySQL must be reachable, MongoDB is
    optional (only used for query statistics).
    :return: True if MongoDB is also available, False if only MySQL is
        available (query statistics won't be saved this session).
    """
    mysql_connector.test_connection()
    try:
        mongo_connector.test_connection()
        return True
    except MongoError:
        return False


def next_film(params: dict[str, Any], limit: int, offset: int)\
        -> tuple[Any, ...]:
    """
    Retrieve the next portion of films based on filters, limit, and offset.
    :return: tuple of film records.
    """
    return mysql_connector.get_next_films(params, limit, offset)


def search(params: dict[str, Any], limit: int, search_type: str,
           client: str = "console") -> tuple[tuple[Any, ...], int, bool]:
    """
    Perform a film search in MySQL and log the query statistics into MongoDB.
    :return: tuple containing the list of films, total count of found films,
    and a boolean status of query logging.
    """
    films, count = mysql_connector.get_first_films(params, limit)
    is_saved = True
    try:
        mongo_connector.save_query(params, count, search_type, client)
    except MongoError:
        is_saved = False
    return films, count, is_saved


def get_years() -> tuple[int, int]:
    """
    Get the range of release years (min and max) for all films.
    :return: tuple with minimum and maximum release years.
    """
    return mysql_connector.get_years_range()


def get_rating() -> list[str]:
    """
    Get the list of unique film age ratings.
    :return: list of rating strings.
    """
    return mysql_connector.get_rating()


def get_genres() -> dict[str, list[int]]:
    """
    Get all genres alongside their corresponding year ranges.
    :return: dictionary with genre names as keys and year lists as values.
    """
    return mysql_connector.get_genres()


def get_film(film_id: int) -> Optional[tuple[Any, ...]]:
    """
    Get detailed information about a specific film by its ID.
    :return: tuple of film details or None if not found.
    """
    return mysql_connector.get_film_by_id(film_id)


def get_popular() -> list[dict[str, Any]]:
    """
    Get overall query statistics grouped by search type from MongoDB.
    :return: list of aggregated statistics documents.
    """
    return mongo_connector.stat_by_type()


def top_in_type(q_type: str, limit: int) -> list[dict[str, Any]]:
    """
    Get top popular queries for a specific search type.
    :return: list of top query documents.
    """
    return mongo_connector.top_in_type(q_type, limit)


def stat_by_client() -> list[dict[str, Any]]:
    """
    Get query statistics grouped by client type from MongoDB.
    :return: list of aggregated client statistics documents.
    """
    return mongo_connector.stat_by_client()


def get_recent_queries(limit: int) -> list[dict[str, Any]]:
    """
    Get a list of recent queries logged in MongoDB.
    :return: list of recent query documents.
    """
    return mongo_connector.get_recent_queries(limit)
