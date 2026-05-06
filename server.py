from mcp.server.fastmcp import FastMCP
from client import MaczfitClient

mcp = FastMCP("maczfit")
_client = MaczfitClient()


@mcp.tool()
def list_diets() -> list[dict]:
    """List all active Maczfit diet subscriptions with their names and calorie counts."""
    return _client.list_diets()


@mcp.tool()
def get_schedule(transaction_id: int) -> dict:
    """
    Get the delivery schedule for a specific diet.

    Returns packages with dates, statuses, and whether each can be moved.
    Also returns available target dates and deadline info.

    Args:
        transaction_id: The diet's transaction ID (e.g. 8173549 or 8173576)
    """
    return _client.get_schedule(transaction_id)


@mcp.tool()
def move_day(transaction_id: int, package_id: int, new_date: str) -> dict:
    """
    Move a single delivery package to a new date.

    Args:
        transaction_id: The diet's transaction ID
        package_id: The specific package ID to move
        new_date: Target date in YYYY-MM-DD format
    """
    return _client.move_day(transaction_id, package_id, new_date)


@mcp.tool()
def move_day_by_date(
    from_date: str,
    to_date: str,
    transaction_ids: list[int] | None = None,
) -> list[dict]:
    """
    Move all diet deliveries from one date to another.

    Use this for natural language requests like "move both diets from Monday to Wednesday".
    If transaction_ids is not provided, moves all active diets.

    Args:
        from_date: Source date in YYYY-MM-DD format
        to_date: Target date in YYYY-MM-DD format
        transaction_ids: Optional list of specific diet IDs to move (default: all diets)
    """
    return _client.move_day_by_date(from_date, to_date, transaction_ids)


if __name__ == "__main__":
    mcp.run()
