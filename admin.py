from sqlalchemy.ext.asyncio import AsyncEngine
from starlette_admin.contrib.sqla import Admin, ModelView
from auth import MyAuthProvider
from models import Unit, Customer, Item, StockItem, Batch, BatchItem
from starlette_admin import CollectionField, IntegerField, TextAreaField, StringField
import json
from sqlalchemy.orm import joinedload
from sqlalchemy import update, delete, select
import qrcode
import io
from starlette.responses import StreamingResponse


class UnitView(ModelView):
    identity = "unit"
    label = "Единицы измерения"

class CustomerView(ModelView):
    identity = "customer"
    label = "Заказчики"

class ItemView(ModelView):
    identity = "item"
    label = "Номенклатура"

    async def find_all(self, request, skip=0, limit=100, where=None, order_by=None):
        return await super().find_all(request, skip, limit, where, order_by)


class StockItemView(ModelView):
    identity = "stock_item"
    label = "Остатки на складе"

    async def build_query(self, where, request):
        stmt = await super().build_query(where, request)
        return stmt.options(joinedload(StockItem.item))

class BatchView(ModelView):
    identity = "batch"
    label = "Партии"
    fields = [
        "id",
        StringField("public_id", read_only=True, label="UUID"),
        "customer",
        TextAreaField("items_data", label="Состав партии")
    ]

    exclude_fields_from_create = ["public_id", "status"]

    async def before_create(self, request, data, obj):
        raw_items = data.pop("items_data", "[]") or "[]"
        items_list = json.loads(raw_items) if isinstance(raw_items, str) else raw_items

        obj.items = [
            BatchItem(item_id=int(i['item_id']), quantity=float(i['quantity']))
            for i in items_list
        ]

        self._pending_items = items_list

    async def after_create(self, request, obj):
        if not hasattr(self, '_pending_items') or not self._pending_items:
            return

        session = request.state.session

        for item_data in self._pending_items:
            item_id = item_data['item_id']
            qty_to_deduct = item_data['quantity']

            stmt = update(StockItem).where(StockItem.item_id == item_id).values(quantity=StockItem.quantity - qty_to_deduct)
            await session.execute(stmt)

            delete_stmt = delete(StockItem).where(StockItem.item_id == item_id, StockItem.quantity <= 0)
            await session.execute(delete_stmt)

        await session.commit()
        del self._pending_items

class BatchItemView(ModelView):
    identity = "batch_item"
    label = "Содержимое партии"

def create_admin(engine: AsyncEngine) -> Admin:
    admin = Admin(engine, title="Панель администрирования", templates_dir="templates")

    admin.add_view(UnitView(Unit))
    admin.add_view(CustomerView(Customer))
    admin.add_view(ItemView(Item))
    admin.add_view(StockItemView(StockItem))
    admin.add_view(BatchView(Batch))
    admin.add_view(BatchItemView(BatchItem))

    ##provider = MyAuthProvider()
    ##provider.setup_admin(admin)

    return admin