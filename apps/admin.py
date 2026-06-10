from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin
from apps.database import engine



app = Starlette()

admin = Admin(engine, title="Example: SQLAlchemy")

admin.mount_to(app)

