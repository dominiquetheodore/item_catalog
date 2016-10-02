from sqlalchemy import func, Column, ForeignKey, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()

engine = create_engine('sqlite:///catalog.db')
DBSession = sessionmaker(bind=engine)
Session = DBSession()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    image = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @classmethod
    def count_items(self, cls):
        cnt = Session.query(SubCategory).filter_by(cat_id=cls.id).count()
        return cnt

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class SubCategory(Base):
    __tablename__ = 'subcategory'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    image = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    cat_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user = relationship(User)

    @classmethod
    def count_items(self, cls):
        cnt = Session.query(Item).filter_by(subcat_id=cls.id).count()
        return cnt


class Item(Base):
    __tablename__ = 'item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    price = Column(String(8))
    cat_id = Column(Integer, ForeignKey('category.id'))
    subcat_id = Column(Integer, ForeignKey('subcategory.id'))
    img = Column(String(250))
    category = relationship(Category)
    subcategory = relationship(SubCategory)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
        }

Base.metadata.create_all(engine)