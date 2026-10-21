"""Web-door version of the demo distributor MCP server.

Same tools as distributor_server.py, but speaks MCP over streamable HTTP
so it can run on a host like Render and answer requests from the internet.

Render sets an environment variable named PORT. This program reads it and
listens on that port, on all interfaces (0.0.0.0).

Run locally:
    pip install "mcp<2"
    python web_server.py
"""

import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "demo-distributor",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8000")),
    stateless_http=True,
    json_response=True,
)

INVENTORY = [
    {"sku": "BRG-6205-2RS", "desc": "Deep groove ball bearing 25x52x15", "stock": 4200, "price": 4.80},
    {"sku": "BRG-UCF205", "desc": "Flange bearing, 4-bolt, 25mm bore", "stock": 850, "price": 18.50},
    {"sku": "BRG-UCF206", "desc": "Flange bearing, 4-bolt, 30mm bore", "stock": 1200, "price": 21.75},
    {"sku": "BRG-UC205", "desc": "Insert bearing 25mm bore", "stock": 3000, "price": 9.20},
]


@mcp.tool()
def search_inventory(keyword: str) -> str:
    """Search distributor inventory by keyword, e.g. 'flange' or '6205'.
    Returns matching SKUs with stock on hand."""
    hits = [i for i in INVENTORY
            if keyword.lower() in i["sku"].lower() or keyword.lower() in i["desc"].lower()]
    if not hits:
        return "No matches."
    return "\n".join(f'{h["sku"]}: {h["desc"]} (stock: {h["stock"]})' for h in hits)


@mcp.tool()
def get_quote(sku: str, quantity: int) -> str:
    """Get a price quote for a SKU and quantity.
    Volume discounts: 5% over 500 units, 10% over 2000 units."""
    item = next((i for i in INVENTORY if i["sku"] == sku.upper()), None)
    if item is None:
        return f"Unknown SKU: {sku}"
    if quantity > item["stock"]:
        return f"Only {item['stock']} in stock; cannot quote {quantity}."
    discount = 0.10 if quantity >= 2000 else 0.05 if quantity >= 500 else 0.0
    total = item["price"] * quantity * (1 - discount)
    return (f"Quote {sku} x {quantity}: ${total:,.2f} "
            f"(${item['price']:.2f}/ea, {discount*100:.0f}% volume discount)")


@mcp.tool()
def check_lead_time(sku: str, state: str) -> str:
    """Check delivery lead time in business days for a SKU shipping to a US state."""
    item = next((i for i in INVENTORY if i["sku"] == sku.upper()), None)
    if item is None:
        return f"Unknown SKU: {sku}"
    if item["stock"] <= 0:
        return f"{sku}: out of stock, 21 business days (factory order)."
    days = 2 if state.upper() == "OH" else 4  # warehouse is in Ohio
    return f"{sku}: in stock, ships in {days} business days to {state.upper()}."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
