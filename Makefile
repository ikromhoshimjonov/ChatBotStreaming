migrate:
	alembic init migrations
mig:
	alembic revision --autogenerate -m "Create fruit table"
	alembic upgrade head
