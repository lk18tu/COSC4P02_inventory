import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection, ProgrammingError as DBProgrammingError
from django.contrib import messages
from django.db.models import Q

from inventoryApp.models import InvTable_Metadata
from .models          import StockTransaction, StockUnit


<<<<<<< Updated upstream
# ---------------------------------------------------------------------
#  Make sure per‑unit tables exist (both legacy and new)
# ---------------------------------------------------------------------
def _ensure_items_tables(base_name: str):
    ddl_body = """
        id                      INT AUTO_INCREMENT PRIMARY KEY,
        class_id                INT          NOT NULL,
        tracking_number         VARCHAR(255) NOT NULL,
        status                  VARCHAR(50)  NOT NULL DEFAULT 'In Stock',
        location                VARCHAR(100) NOT NULL DEFAULT 'Warehouse',
        destination_percentage  INT          NULL,
        date_added              TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP,
        last_updated            TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP
                                           ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uq_tracking (tracking_number)
    """
    with connection.cursor() as c:
        for suf in ("_items", "_classes_items"):
            c.execute(
                f"CREATE TABLE IF NOT EXISTS `{base_name}{suf}` ({ddl_body}) "
                "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
            )


# ─────────────────────────────────────────────────────────────────────────────
#                               PRODUCT  LIST
=======
# helper: ensure “<base>_items” exists ― runs once per base name
def _ensure_items_table(base: str):
    ddl = f"""
    CREATE TABLE IF NOT EXISTS `{base}_items` (
        id   INT AUTO_INCREMENT PRIMARY KEY,
        class_id        INT          NOT NULL,
        tracking_number VARCHAR(255) NOT NULL,
        status   VARCHAR(50)  NOT NULL DEFAULT 'In Stock',
        location VARCHAR(100) NOT NULL DEFAULT 'Warehouse',
        destination_percentage INT NULL,
        date_added   TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
                                   ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uq_tracking (tracking_number)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    with connection.cursor() as c:
        c.execute(ddl)

# ─────────────────────────────────────────────────────────────────────────────
# PRODUCT LIST
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
=======
        txs = StockTransaction.objects.filter(table_meta=meta).order_by("item_id", "-created_at")
>>>>>>> Stashed changes
        latest = {}
        for tx in StockTransaction.objects.filter(table_meta=meta).order_by("item_id", "-created_at"):
            latest.setdefault(tx.item_id, tx.transaction_id)

        table_data = {
            "table_name":    table_name,
            "friendly_name": meta.table_friendly_name,
            "columns":       cols + ["transaction_id"],
            "rows":          [row + (latest.get(row[0], ""),) for row in rows],
        }

    return render(request, "updateStock/product_list.html", {
        "tenant_url":       tenant_url,
        "inventory_tables": tables,
        "table_data":       table_data,
    })


# ─────────────────────────────────────────────────────────────────────────────
<<<<<<< Updated upstream
#                                ITEM DETAIL
=======
# ITEM DETAIL
>>>>>>> Stashed changes
# ─────────────────────────────────────────────────────────────────────────────
def item_detail(request, table_name, item_id, tenant_url=None):
    tenant_url = (hasattr(request, "tenant") and request.tenant.domain_url) or tenant_url or ""
    meta       = get_object_or_404(InvTable_Metadata, table_name=table_name)
    base_name  = table_name.rsplit("_classes", 1)[0]          # ← NEW

<<<<<<< Updated upstream
    # ---------- remove one unit ----------
=======
>>>>>>> Stashed changes
    if request.method == "POST" and request.POST.get("remove_unit"):
        tid = request.POST["remove_unit"]

        with connection.cursor() as c:
            c.execute(
                f"UPDATE `{table_name}` SET quantity_stock = quantity_stock - 1 WHERE id = %s",
                [item_id],
            )

<<<<<<< Updated upstream
        batch = uuid.uuid4().hex
        StockTransaction.objects.create(
            table_meta=meta, item_id=item_id,
            change=-1, tracking_id=tid, transaction_id=batch,
        )

        try:
            u = StockUnit.objects.get(table_meta=meta, item_id=item_id, tracking_id=tid)
            u.status, u.location = "Removed", ""
            u.save()
=======
        batch_id = uuid.uuid4().hex
        StockTransaction.objects.create(
            table_meta=meta, item_id=item_id, change=-1,
            tracking_id=remove_tid, transaction_id=batch_id,
        )

        try:
            unit = StockUnit.objects.get(table_meta=meta, item_id=item_id, tracking_id=remove_tid)
            unit.status, unit.location = "Removed", ""
            unit.save()
>>>>>>> Stashed changes
        except StockUnit.DoesNotExist:
            pass

        with connection.cursor() as c:
<<<<<<< Updated upstream
            for suf in ("_items", "_classes_items"):
                try:
                    c.execute(
                        f"""
                        UPDATE `{table_name}{suf}`
                           SET status='Removed', location='', last_updated=NOW()
                         WHERE tracking_number=%s AND class_id=%s
                        """,
                        [tid, item_id],
                    )
                except DBProgrammingError:
                    pass

        messages.success(request, f"Unit {tid} removed.")
        return redirect("updateStock:item_detail",
                        tenant_url=tenant_url, table_name=table_name, item_id=item_id)

    # ---------- display ----------
=======
            try:
                c.execute(
                    f"UPDATE `{base_name}_items` "             # ← CHANGED
                    "SET status='Removed', location='', last_updated=NOW() "
                    "WHERE tracking_number=%s AND class_id=%s",
                    [remove_tid, item_id],
                )
            except DBProgrammingError:
                pass

        messages.success(request, f"Unit {remove_tid} removed.")
        return redirect("updateStock:item_detail",
                        tenant_url=tenant_url, table_name=table_name, item_id=item_id)

>>>>>>> Stashed changes
    with connection.cursor() as c:
        c.execute(f"SELECT * FROM `{table_name}` WHERE id = %s", [item_id])
        cols, row = [col[0] for col in c.description], c.fetchone()
    if not row:
        messages.error(request, "Item not found.")
        return redirect("updateStock:product_list", tenant_url=tenant_url)

    item_title = row[cols.index("title")] if "title" in cols else f"ID {item_id}"

<<<<<<< Updated upstream
    live = []
    for tx in StockTransaction.objects.filter(table_meta=meta, item_id=item_id).order_by("created_at"):
=======
    all_txs = StockTransaction.objects.filter(table_meta=meta, item_id=item_id).order_by("created_at")
    live_units = []
    for tx in all_txs:
>>>>>>> Stashed changes
        if tx.change > 0:
            live.append(tx.tracking_id)
        elif tx.tracking_id in live:
            live.remove(tx.tracking_id)

<<<<<<< Updated upstream
    num_map = {}
    for t in live:
=======
    unit_map = {}
    for tid in live_units:
>>>>>>> Stashed changes
        try:
            num_map[int(t.rsplit("_", 1)[1])] = t
        except Exception:
            pass

<<<<<<< Updated upstream
    instances = [{"unit_number": n, "tracking_id": t} for n, t in sorted(num_map.items())]

    u_map = {u.tracking_id: u for u in StockUnit.objects.filter(
        table_meta=meta, item_id=item_id,
        tracking_id__in=[i["tracking_id"] for i in instances])}

    for i in instances:
        u = u_map.get(i["tracking_id"])
        i["status"]   = u.status   if u else ""
        i["location"] = u.location if u else ""
=======
    instances = [{"unit_number": slot, "tracking_id": tid} for slot, tid in sorted(unit_map.items())]

    units = StockUnit.objects.filter(
        table_meta=meta, item_id=item_id,
        tracking_id__in=[inst["tracking_id"] for inst in instances]
    )
    unit_map2 = {u.tracking_id: u for u in units}
    for inst in instances:
        u = unit_map2.get(inst["tracking_id"])
        inst["status"]   = u.status   if u else ""
        inst["location"] = u.location if u else ""
>>>>>>> Stashed changes

    history = StockTransaction.objects.filter(
        table_meta=meta, item_id=item_id
    ).filter(Q(change__lt=0) | Q(tracking_id="")).order_by("-created_at")

    return render(request, "updateStock/item_detail.html", {
        "tenant_url": tenant_url, "table_name": table_name, "item_id": item_id,
        "item_title": item_title, "instances": instances, "history": history,
    })


# ─────────────────────────────────────────────────────────────────────────────
<<<<<<< Updated upstream
#                                  ADD STOCK
=======
# ADD STOCK
>>>>>>> Stashed changes
# ─────────────────────────────────────────────────────────────────────────────
def add_stock(request, table_name, item_id, tenant_url=None):
    tenant_url = (hasattr(request, "tenant") and request.tenant.domain_url) or tenant_url or ""
    meta       = get_object_or_404(InvTable_Metadata, table_name=table_name)

    with connection.cursor() as c:
        c.execute(f"SELECT title FROM `{table_name}` WHERE id = %s", [item_id])
        row = c.fetchone()
    item_title = row[0] if row else f"ID_{item_id}"

    base_name = table_name.rsplit("_classes", 1)[0]           # ← NEW

    if request.method == "POST":
        amt      = int(request.POST["amount"])
        status   = request.POST.get("status",   "In Stock")
        location = request.POST.get("location", "Warehouse")

        with connection.cursor() as c:
            c.execute(
                f"UPDATE `{table_name}` SET quantity_stock = quantity_stock + %s WHERE id = %s",
                [amt, item_id],
            )

<<<<<<< Updated upstream
        _ensure_items_tables(table_name)               # <── NEW

        batch = uuid.uuid4().hex
        slug  = item_title.replace(" ", "_")
=======
        _ensure_items_table(base_name)                        # ← CHANGED
        target_tbl = f"{base_name}_items"                     # ← NEW

        batch_id = uuid.uuid4().hex
        slug     = item_title.replace(" ", "_")
>>>>>>> Stashed changes

        existing = StockTransaction.objects.filter(
            table_meta=meta, item_id=item_id, change__gt=0
        ).values_list("tracking_id", flat=True)
<<<<<<< Updated upstream

        start = max([int(t.rsplit("_", 1)[-1]) for t in existing
                     if t.startswith(f"{slug}_{item_id}_")] or [0]) + 1
=======
        nums = [int(t.rsplit("_", 1)[-1])
                for t in existing if t.startswith(f"{slug}_{item_id}_")]
        start = max(nums, default=0) + 1
>>>>>>> Stashed changes

        for i in range(start, start + amt):
            tid = f"{slug}_{item_id}_{i}"

            StockTransaction.objects.create(
                table_meta=meta, item_id=item_id, change=1,
<<<<<<< Updated upstream
                tracking_id=tid, transaction_id=batch,
            )

            StockUnit.objects.create(
                table_meta=meta, item_id=item_id, tracking_id=tid,
                status=status, location=location,
            )

            with connection.cursor() as c:
                for suf in ("_items", "_classes_items"):
                    c.execute(
                        f"""
                        INSERT IGNORE INTO `{table_name}{suf}`
                            (class_id, tracking_number, status, location)
                        VALUES (%s, %s, %s, %s)
                        """,
                        [item_id, tid, status, location],
                    )

        StockTransaction.objects.create(
            table_meta=meta, item_id=item_id, change=amt,
            tracking_id="", transaction_id=batch,
=======
                tracking_id=tid, transaction_id=batch_id,
            )

            StockUnit.objects.create(
                table_meta=meta, item_id=item_id,
                tracking_id=tid, status=status, location=location,
            )

            with connection.cursor() as c:
                try:
                    c.execute(
                        f"INSERT IGNORE INTO `{target_tbl}` "  # ← CHANGED
                        "(class_id, tracking_number, status, location) "
                        "VALUES (%s, %s, %s, %s)",
                        [item_id, tid, status, location],
                    )
                except DBProgrammingError:
                    pass

        StockTransaction.objects.create(
            table_meta=meta, item_id=item_id, change=amt,
            tracking_id="", transaction_id=batch_id,
>>>>>>> Stashed changes
        )

        messages.success(request, f"Added {amt} unit(s).")
        return redirect("updateStock:item_detail",
                        tenant_url=tenant_url, table_name=table_name, item_id=item_id)

    return render(request, "updateStock/add_stock.html", {
        "tenant_url": tenant_url, "table_name": table_name,
        "item_id": item_id, "item_title": item_title,
    })


# ─────────────────────────────────────────────────────────────────────────────
<<<<<<< Updated upstream
#                               REMOVE STOCK (stub)
=======
# REMOVE STOCK (stub)
>>>>>>> Stashed changes
# ─────────────────────────────────────────────────────────────────────────────
def remove_stock(request, table_name, item_id, tenant_url=None):
    return redirect("updateStock:item_detail",
                    tenant_url=tenant_url, table_name=table_name, item_id=item_id)
