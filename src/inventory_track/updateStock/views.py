import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection
from django.db import ProgrammingError as DBProgrammingError
from django.contrib import messages
from django.db.models import Q

from inventoryApp.models import InvTable_Metadata
from .models import StockTransaction, StockUnit


def product_list(request, tenant_url=None):
    tenant_url = (hasattr(request, "tenant") and request.tenant.domain_url) or tenant_url or ""
    table_name = request.GET.get("table")
    tables     = InvTable_Metadata.objects.filter(table_type="inventory").order_by("table_name")

    if not table_name and tables:
        table_name = tables.first().table_name

    table_data = {"table_name": None, "friendly_name": "", "columns": [], "rows": []}
    if table_name:
        meta = get_object_or_404(InvTable_Metadata, table_name=table_name)
        with connection.cursor() as c:
            c.execute(f"SELECT * FROM `{table_name}`")
            cols = [col[0] for col in c.description]
            rows = c.fetchall()

        # most‑recent per‑item batch transaction_id
        txs = StockTransaction.objects.filter(
            table_meta=meta
        ).order_by("item_id", "-created_at")

        latest = {}
        for tx in txs:
            if tx.item_id not in latest:
                latest[tx.item_id] = tx.transaction_id

        augmented = []
        for row in rows:
            item_id = row[0]
            augmented.append(row + (latest.get(item_id, ""),))

        table_data = {
            "table_name":    table_name,
            "friendly_name": meta.table_friendly_name,
            "columns":       cols + ["transaction_id"],
            "rows":          augmented,
        }

    return render(request, "updateStock/product_list.html", {
        "tenant_url":       tenant_url,
        "inventory_tables": tables,
        "table_data":       table_data,
    })


def item_detail(request, table_name, item_id, tenant_url=None):
    tenant_url = (hasattr(request, "tenant") and request.tenant.domain_url) or tenant_url or ""
    meta       = get_object_or_404(InvTable_Metadata, table_name=table_name)

    # — remove a specific unit? —
    if request.method == "POST" and request.POST.get("remove_unit"):
        remove_tid = request.POST["remove_unit"]

        # 1) decrement the master stock count
        with connection.cursor() as c:
            c.execute(
                f"UPDATE `{table_name}` "
                "SET quantity_stock = quantity_stock - 1 "
                "WHERE id = %s",
                [item_id],
            )

        # 2) log the removal
        batch_id = uuid.uuid4().hex
        StockTransaction.objects.create(
            table_meta     = meta,
            item_id        = item_id,
            change         = -1,
            tracking_id    = remove_tid,
            transaction_id = batch_id,
        )

        # 3) update the StockUnit row
        try:
            unit = StockUnit.objects.get(
                table_meta=meta,
                item_id=item_id,
                tracking_id=remove_tid
            )
            unit.status   = "Removed"
            unit.location = ""
            unit.save()
        except StockUnit.DoesNotExist:
            pass

        messages.success(request, f"Unit {remove_tid} removed.")
        return redirect("updateStock:item_detail",
                        tenant_url=tenant_url,
                        table_name=table_name,
                        item_id=item_id)

    # — fetch the “master” row —
    with connection.cursor() as c:
        c.execute(f"SELECT * FROM `{table_name}` WHERE id = %s", [item_id])
        cols = [col[0] for col in c.description]
        row  = c.fetchone()
    if not row:
        messages.error(request, "Item not found.")
        return redirect("updateStock:product_list", tenant_url=tenant_url)

    # — determine a display title —
    item_title = row[cols.index("title")] if "title" in cols else f"ID {item_id}"

    # — build the live unit list from all +1/−1 ops —
    all_txs = StockTransaction.objects.filter(
        table_meta=meta,
        item_id=item_id
    ).order_by("created_at")

    live_units = []
    for tx in all_txs:
        if tx.change > 0:
            live_units.append(tx.tracking_id)
        elif tx.change < 0 and tx.tracking_id in live_units:
            live_units.remove(tx.tracking_id)

    # — map slot numbers to tracking IDs —
    unit_map = {}
    for tid in live_units:
        try:
            slot = int(tid.rsplit("_", 1)[1])
        except (IndexError, ValueError):
            continue
        unit_map[slot] = tid

    instances = [
        {"unit_number": slot, "tracking_id": tid}
        for slot, tid in sorted(unit_map.items())
    ]

    # — fetch status + location from StockUnit —
    units   = StockUnit.objects.filter(
        table_meta=meta,
        item_id=item_id,
        tracking_id__in=[inst["tracking_id"] for inst in instances]
    )
    unit_map2 = {u.tracking_id: u for u in units}
    for inst in instances:
        u = unit_map2.get(inst["tracking_id"])
        inst["status"]   = u.status   if u else ""
        inst["location"] = u.location if u else ""

    # — history: bulk adds (change > 1) and all removals (change < 0) —
    history = StockTransaction.objects.filter(
        table_meta=meta,
        item_id=item_id
    ).filter(
        Q(change__gt=1) | Q(change__lt=0)
    ).order_by("-created_at")

    return render(request, "updateStock/item_detail.html", {
        "tenant_url": tenant_url,
        "table_name": table_name,
        "item_id":    item_id,
        "item_title": item_title,
        "instances":  instances,
        "history":    history,
    })


def add_stock(request, table_name, item_id, tenant_url=None):
    tenant_url = (hasattr(request, "tenant") and request.tenant.domain_url) or tenant_url or ""
    meta       = get_object_or_404(InvTable_Metadata, table_name=table_name)

    # grab the item title
    with connection.cursor() as c:
        c.execute(f"SELECT title FROM `{table_name}` WHERE id = %s", [item_id])
        row = c.fetchone()
    item_title = row[0] if row else f"ID_{item_id}"

    if request.method == "POST":
        amt      = int(request.POST["amount"])
        status   = request.POST.get("status",   "In Stock")
        location = request.POST.get("location", "Warehouse")

        # 1) bump the master stock count
        with connection.cursor() as c:
            c.execute(
                f"UPDATE `{table_name}` "
                "SET quantity_stock = quantity_stock + %s "
                "WHERE id = %s",
                [amt, item_id],
            )

        # 2) create StockTransaction rows + StockUnit rows
        batch_id = uuid.uuid4().hex
        slug     = item_title.replace(" ", "_")

        existing = StockTransaction.objects.filter(
            table_meta=meta, item_id=item_id, change__gt=0
        ).values_list("tracking_id", flat=True)
        nums = [
            int(t.rsplit("_", 1)[-1])
            for t in existing
            if t.startswith(f"{slug}_{item_id}_")
        ]
        start = max(nums, default=0) + 1

        for i in range(start, start + amt):
            tid = f"{slug}_{item_id}_{i}"
            # a) log transaction
            StockTransaction.objects.create(
                table_meta     = meta,
                item_id        = item_id,
                change         = 1,
                tracking_id    = tid,
                transaction_id = batch_id,
            )
            # b) create the unit with chosen status & location
            StockUnit.objects.create(
                table_meta   = meta,
                item_id      = item_id,
                tracking_id  = tid,
                status       = status,
                location     = location,
            )

        # 3) summary row
        StockTransaction.objects.create(
            table_meta     = meta,
            item_id        = item_id,
            change         = amt,
            tracking_id    = "",
            transaction_id = batch_id,
        )

        messages.success(request, f"Added {amt} unit(s).")
        return redirect("updateStock:item_detail",
                        tenant_url=tenant_url,
                        table_name=table_name,
                        item_id=item_id)

    return render(request, "updateStock/add_stock.html", {
        "tenant_url": tenant_url,
        "table_name": table_name,
        "item_id":    item_id,
        "item_title": item_title,
    })


def remove_stock(request, table_name, item_id, tenant_url=None):
    return redirect("updateStock:item_detail",
                    tenant_url=tenant_url,
                    table_name=table_name,
                    item_id=item_id)
