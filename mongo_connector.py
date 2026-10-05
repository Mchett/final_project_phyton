from pymongo import MongoClient
from pymongo.errors import PyMongoError as MongoError
from config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NAME
from datetime import datetime
from typing import Any, Optional


def _get_connection() -> MongoClient:
    """
    Connect to MongoDB and return a Client object
    :raises pymongo.errors.PyMongoError: if the client can't be created.
    :return: MongoClient instance.
    """
    return MongoClient(MONGO_URI)


def test_connection() -> None:
    """
    Check if MongoDB database connection is working.
    """
    close_connection(_get_connection())


def save_query(params: dict[str, Any], count: int, search_type: str,
               client_type: str) -> None:
    """
    Save search query details to the MongoDB database.
    """
    client = _get_connection()
    try:
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        clean_params = {k: v for k, v in params.items() if k != "exception"}
        query_doc = {
            "timestamp": datetime.now(),
            "client": client_type,
            "search_type": search_type,
            "count": count,
            "params": clean_params
        }
        if "exception" in params:
            query_doc["exception"] = params["exception"]
        collection.insert_one(query_doc)
    finally:
        close_connection(client)


def _run_aggregation(pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Run an aggregation pipeline against the queries collection.
    :return: list of aggregation result documents.
    """
    client = _get_connection()
    try:
        collection = client[MONGO_DB_NAME][MONGO_COLLECTION_NAME]
        return list(collection.aggregate(pipeline))
    finally:
        close_connection(client)


def top_in_type(query_type: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Get top popular queries for a specific search type based on
    normalized parameters.
    :return: list of aggregation result documents.
    """
    pipeline = [{'$match': {'search_type': query_type}},
                {'$addFields': {'normalized_params': {'$mergeObjects': [
                    '$params', {'keyword': {'$toLower': {
                                '$ifNull': ['$params.keyword', '']}}}]}}},
                {'$group': {'_id': {
                    'search_type': '$search_type',
                    'params': '$normalized_params',
                    'count_res': '$count'},
                    'count_query': {'$sum': 1}}},
                {'$sort': {'count_query': -1}},
                {'$limit': limit},]
    return _run_aggregation(pipeline)


def stat_by_type() -> list[dict[str, Any]]:
    """
    Get query statistics grouped by search type.
    :return: list of documents containing search types and their counts.
    """
    pipeline = [
        {'$group': {'_id': '$search_type', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    return _run_aggregation(pipeline)


def stat_by_client() -> list[dict[str, Any]]:
    """
    Get query statistics grouped by client type.
    :return: list of documents containing client types and their counts.
    """
    pipeline = [
        {'$group': {'_id': '$client', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    return _run_aggregation(pipeline)


def get_recent_queries(limit: int = 5) -> list[dict[str, Any]]:
    """
    Get recent queries ordered by timestamp in descending order.
    :return: list of recent query documents.
    """
    client = _get_connection()
    try:
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        r = collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
        result = list(r)
        return result
    finally:
        close_connection(client)


def close_connection(client: MongoClient) -> Optional[bool]:
    try:
        client.close()
        return True
    except MongoError:
        pass
