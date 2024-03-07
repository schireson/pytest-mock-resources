from sqlalchemy import text


def test_one(pg):
    pg.execute(text("select 1"))


def test_two(pg):
    pg.execute(text("select 1"))
