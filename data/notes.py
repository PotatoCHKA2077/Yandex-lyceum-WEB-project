import datetime
import sqlalchemy
from sqlalchemy import orm, Integer, String
from .db_session import SqlAlchemyBase


class Notes(SqlAlchemyBase):
    __tablename__ = 'notes'

    id = sqlalchemy.Column(Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(String, nullable=True)
    content = sqlalchemy.Column(String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    user_id = sqlalchemy.Column(Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('User')
