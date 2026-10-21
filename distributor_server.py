"""MCP server backed by a REAL database (SQLite file: inventory.db).

Same menu as before -- same three tools, same two resources. The only
thing that changed is WHERE the truth lives: not a Python list anymore,
but a database file outside the code. Edit the database, answers change,
code untouched.
"""

import os
import sqlite3
from typing import Annotated

from pydantic import Field

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "demo-distributor",
    instructions="You are talking to Acme Bearings, a wholesale distributor. "
                 "Use search_inventory to find parts, get_quote for pricing "
                 "(volume discounts apply), check_lead_time for delivery estimates.",
)

# The database file sits next to this script. No server, no ports, no admin.
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")


def _db():
    """Open the door to the database. Returns a connection."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row  # rows behave like dicts: row["price"]
    return conn


@mcp.tool()
def search_inventory(keyword: str) -> str:
    """Search distributor inventory by keyword, e.g. 'flange' or '6205'.
    Returns matching SKUs with stock on hand."""
    conn = _db()
    rows = conn.execute(
        "SELECT sku, description, stock FROM inventory "
        "WHERE sku LIKE ? OR description LIKE ?",
        (f"%{keyword}%", f"%{keyword}%"),
    ).fetchall()
    conn.close()
    if not rows:
        return "No matches."
    return "\n".join(f'{r["sku"]}: {r["description"]} (stock: {r["stock"]})' for r in rows)


@mcp.tool()
def get_quote(
    sku: Annotated[str, Field(description="Product SKU, e.g. BRG-UCF205")],
    quantity: Annotated[int, Field(description="Number of units requested", gt=0)],
) -> str:
    """Get a price quote for a SKU and quantity.
    Volume discounts: 5% over 500 units, 10% over 2000 units."""
    conn = _db()
    row = conn.execute("SELECT * FROM inventory WHERE sku = ?", (sku.upper(),)).fetchone()
    conn.close()
    if row is None:
        return f"Unknown SKU: {sku}"
    if quantity > row["stock"]:
        return f"Only {row['stock']} in stock; cannot quote {quantity}."
    discount = 0.10 if quantity >= 2000 else 0.05 if quantity >= 500 else 0.0
    total = row["price"] * quantity * (1 - discount)
    return (f"Quote {sku} x {quantity}: ${total:,.2f} "
            f"(${row['price']:.2f}/ea, {discount*100:.0f}% volume discount)")


@mcp.tool()
def check_lead_time(sku: str, state: str) -> str:
    """Check delivery lead time in business days for a SKU shipping to a US state."""
    conn = _db()
    row = conn.execute("SELECT stock FROM inventory WHERE sku = ?", (sku.upper(),)).fetchone()
    conn.close()
    if row is None:
        return f"Unknown SKU: {sku}"
    if row["stock"] <= 0:
        return f"{sku}: out of stock, 21 business days (factory order)."
    days = 2 if state.upper() == "OH" else 4  # warehouse is in Ohio
    return f"{sku}: in stock, ships in {days} business days to {state.upper()}."


@mcp.resource("policy://discounts")
def discount_policy() -> str:
    """Volume discount policy. Agents should read this before quoting."""
    return """ACME BEARINGS - VOLUME DISCOUNT POLICY
Orders of 500+ units: 5% discount applied automatically.
Orders of 2000+ units: 10% discount applied automatically.
Discounts cannot be combined with contract pricing.
Net-30 terms available for accounts in good standing."""


@mcp.resource("policy://shipping")
def shipping_policy() -> str:
    """Shipping and lead-time policy."""
    return """ACME BEARINGS - SHIPPING POLICY
In-stock items ship within 2 business days to Ohio, 4 days elsewhere in the US.
Factory orders (out of stock): 21 business days.
Freight quotes available on request for orders over $10,000."""


if __name__ == "__main__":
    mcp.run()  # stdio transport: talks MCP over stdin/stdout
