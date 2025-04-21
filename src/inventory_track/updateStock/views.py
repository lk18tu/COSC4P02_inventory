import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection, ProgrammingError as DBProgrammingError
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from history.models import InventoryHistory
from notifications.models import Notification
from django.contrib.auth.models import User
from inventoryApp.models import InvTable_Metadata
from .models          import StockTransaction, StockUnit


# helper – make sure “<base>_items” exists
def _ensure_items_table(base: str):
    ddl = f"""
    CREATE TABLE IF NOT EXISTS `{base}_items` (
        id                      INT AUTO_INCREMENT PRIMARY KEY,
        class_id                INT          NOT NULL,
        tracking_number         VARCHAR(255) NOT NULL,
        status                  VARCHAR(50)  NOT NULL DEFAULT 'In Stock',
        location                VARCHAR(100) NOT NULL DEFAULT 'Warehouse',
        destination_percentage  DOUBLE(5,2)  NOT NULL DEFAULT 0.0,
        date_added              TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP,
        last_updated            TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP
                                              ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uq_tracking (tracking_number)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    with connection.cursor() as c:
        c.execute(ddl)


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCT LIST
# ─────────────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────────────
# ITEM DETAIL
# ─────────────────────────────────────────────────────────────────────────────
def item_detail(request, table_name, item_id, tenant_url=None):
    tenant_url = (hasattr(request, "tenant") and request.tenant.domain_url) or tenant_url or ""
    meta       = get_object_or_404(InvTable_Metadata, table_name=table_name)
    base_name  = table_name.rsplit("_classes", 1)[0]   # ← for *_items table

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
            unit.status, unit.location = "Removed", ""
            unit.save()
        except StockUnit.DoesNotExist:
            pass

        # 4) mirror the change into <base>_items
        with connection.cursor() as c:
            try:
                c.execute(
                    f"""
                    UPDATE `{base_name}_items`
                       SET status='Removed',
                           location='',
                           last_updated = NOW()
                     WHERE tracking_number = %s
                       AND class_id        = %s
                    """,
                    [remove_tid, item_id],
                )
            except DBProgrammingError:
                pass

        

        messages.success(request, f"Unit {remove_tid} removed.")


        print("removin stock")
        # grab the item title
        with connection.cursor() as c:
            c.execute(f"SELECT title FROM `{table_name}` WHERE id = %s", [item_id])
            row = c.fetchone()
        item_title = row[0] if row else f"ID_{item_id}"

        print(item_title)

        #CHECK IF STOCK NOTIFICATIONS NEED TO BE SENT
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT quantity_stock, reorder_level 
                FROM `{table_name}` 
                WHERE id = %s
            """, [item_id])
            row = cursor.fetchone()

            if row:
                quantity_stock, reorder_level = row
                user = User.objects.get(username=request.user.username)
                if quantity_stock < reorder_level:
                    Notification.objects.create(
                        user=user,
                        message="⚠️ You just updated stock for " + item_title + ". It is below stock level!"
                    )
                        
                else:
                    Notification.objects.create(
                        user=user,
                        message="You just updated stock for " + item_title + ". Item is above stock level."
                    )
            else:
                print("❌ Item not found.")

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
    units     = StockUnit.objects.filter(
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

    # ←──── UNITS PAGINATION ──────────
    units_paginator = Paginator(instances, 10)  # 10 units per page
    units_page_number = request.GET.get("units_page")
    instances_page = units_paginator.get_page(units_page_number)

    # ←──── HISTORY PAGINATION ─────────
    history_paginator = Paginator(history, 10)  # 10 tx per page
    history_page_number = request.GET.get("page")
    history_page = history_paginator.get_page(history_page_number)

    return render(request, "updateStock/item_detail.html", {
        "tenant_url": tenant_url,
        "table_name": table_name,
        "item_id": item_id,
        "item_title": item_title,
        # pass the paginated pages, drop the old `instances` & `history` if you like
        "instances_page": instances_page,
        "history_page": history_page,
    })


# ─────────────────────────────────────────────────────────────────────────────
# ADD STOCK
# ─────────────────────────────────────────────────────────────────────────────
def add_stock(request, table_name, item_id, tenant_url=None):
    tenant_url = (hasattr(request, "tenant") and request.tenant.domain_url) or tenant_url or ""
    meta       = get_object_or_404(InvTable_Metadata, table_name=table_name)

    # grab the item title
    with connection.cursor() as c:
        c.execute(f"SELECT title FROM `{table_name}` WHERE id = %s", [item_id])
        row = c.fetchone()
    item_title = row[0] if row else f"ID_{item_id}"

    base_name = table_name.rsplit("_classes", 1)[0]      # → for *_items table

    if request.method == "POST":
        amt      = int(request.POST["amount"])
        status   = request.POST.get("status",   "In Stock")
        location = request.POST.get("location", "Warehouse")

        # 1) bump master stock count
        with connection.cursor() as c:
            c.execute(
                f"UPDATE `{table_name}` "
                "SET quantity_stock = quantity_stock + %s "
                "WHERE id = %s",
                [amt, item_id],
            )

        # make sure <base>_items exists
        _ensure_items_table(base_name)
        target_tbl = f"{base_name}_items"

        # 2) create StockTransaction rows + StockUnit rows + raw‑SQL rows
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
            # c) mirror into <base>_items
            with connection.cursor() as c:
                try:
                    c.execute(
                        f"""
                        INSERT IGNORE INTO `{target_tbl}`
                            (class_id, tracking_number, status, location, destination_percentage)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        [item_id, tid, status, location, 0],
                    )
                except DBProgrammingError:
                    pass

        # 3) summary row
        StockTransaction.objects.create(
            table_meta     = meta,
            item_id        = item_id,
            change         = amt,
            tracking_id    = "",
            transaction_id = batch_id,
        )

        messages.success(request, f"Added {amt} unit(s).")

        #CHECK IF STOCK NOTIFICATIONS NEED TO BE SENT
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT quantity_stock, reorder_level 
                FROM `{table_name}` 
                WHERE id = %s
            """, [item_id])
            row = cursor.fetchone()

            if row:
                quantity_stock, reorder_level = row
                user = User.objects.get(username=request.user.username)
                if quantity_stock < reorder_level:
                    
                    Notification.objects.create(
                        user=user,
                        message="⚠️ You just updated stock for " + item_title + ". It is below stock level!"
                    )
                else:
                    Notification.objects.create(
                        user=user,
                        message="You just updated stock for " + item_title + ". Item is above stock level."
                    )
            else:
                print("❌ Item not found.")

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


# ─────────────────────────────────────────────────────────────────────────────
# REMOVE STOCK (stub)
# ─────────────────────────────────────────────────────────────────────────────
def remove_stock(request, table_name, item_id, tenant_url=None):

    
    return redirect("updateStock:item_detail",
                    tenant_url=tenant_url,
                    table_name=table_name,
                    item_id=item_id)
