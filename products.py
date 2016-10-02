from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item, User, SubCategory

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(id=1, name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# main categories
cat1 = Category(user_id=1, name="Home, Office", id=1, user=User1)
cat2 = Category(user_id=1, name="Clothes", id=2, user=User1)
cat3 = Category(user_id=1, name="Vehicles", id=3, user=User1)
cat4 = Category(user_id=1, name="Property", id=4, user=User1)
cat5 = Category(user_id=1, name="Electronics", id=5, user=User1)
cat6 = Category(user_id=1, name="Services", id=6, user=User1)
cat7 = Category(user_id=1, name="Dating", id=7, user=User1)

session.add(cat1)
session.add(cat2)
session.add(cat3)
session.add(cat4)
session.add(cat5)
session.add(cat6)
session.add(cat7)
session.commit()

# main subcategories
subcat1 = SubCategory(user_id=1, name="Building Supplies", cat_id=1, id=1, user=User1)
subcat2 = SubCategory(user_id=1, name="Home Furniture", cat_id=1, id=2, user=User1)
subcat3 = SubCategory(user_id=1, name="Security Products", cat_id=1, id=3, user=User1)
subcat4 = SubCategory(user_id=1, name="Energy", cat_id=1, id=4, user=User1)
subcat5 = SubCategory(user_id=1, name="Cell Phones", image="cellphones.jpg", cat_id=5, id=5, user=User1)
subcat6 = SubCategory(user_id=1, name="Laptops", cat_id=5, id=6, user=User1)
subcat7 = SubCategory(user_id=1, name="Consumables", cat_id=5, id=7, user=User1)
subcat8 = SubCategory(user_id=1, name="Printers", cat_id=5, id=8, user=User1)
subcat9 = SubCategory(user_id=1, name="House for sale", cat_id=4, id=9, user=User1)
subcat10 = SubCategory(user_id=1, name="House for rent", cat_id=4, id=10, user=User1)
subcat11 = SubCategory(user_id=1, name="Land for sale", cat_id=4, id=11, user=User1)
subcat12 = SubCategory(user_id=1, name="Construction and renovation", cat_id=6, id=12, user=User1)
subcat13 = SubCategory(user_id=1, name="Plumbing and electrical", cat_id=6, id=13, user=User1)
subcat14 = SubCategory(user_id=1, name="Events and entertainment", cat_id=6, id=14, user=User1)
subcat15 = SubCategory(user_id=1, name="Classes", cat_id=6, id=15, user=User1)
subcat16 = SubCategory(user_id=1, name="Cars", image="cars.png", cat_id=3, id=16, user=User1)
subcat17 = SubCategory(user_id=1, name="Lorries", image="lorries.jpg", cat_id=3, id=17, user=User1)
subcat18 = SubCategory(user_id=1, name="Vans", cat_id=3, id=18, user=User1)
subcat19 = SubCategory(user_id=1, name="SUVs", image="SUV.jpg", cat_id=3, id=19, user=User1)
subcat20 = SubCategory(user_id=1, name="Men clothing", image="mensclothing.jpg", cat_id=2, id=20, user=User1)
subcat21 = SubCategory(user_id=1, name="Girls clothing", image="womensclothing.jpg", cat_id=2, id=21, user=User1)
subcat22 = SubCategory(user_id=1, name="Accessories", image="accessories.jpg", cat_id=2, id=22, user=User1)
subcat23 = SubCategory(user_id=1, name="Guys seeking girls", cat_id=7, id=23, user=User1)
subcat24 = SubCategory(user_id=1, name="Boys seeking girls", cat_id=7, id=24, user=User1)
session.add(subcat1)
session.add(subcat2)
session.add(subcat3)
session.add(subcat4)
session.add(subcat5)
session.add(subcat6)
session.add(subcat7)
session.add(subcat8)
session.add(subcat9)
session.add(subcat10)
session.add(subcat11)
session.add(subcat12)
session.add(subcat13)
session.add(subcat14)
session.add(subcat15)
session.add(subcat16)
session.add(subcat17)
session.add(subcat18)
session.add(subcat19)
session.add(subcat20)
session.add(subcat21)
session.add(subcat22)
session.add(subcat23)
session.add(subcat24)

Item1 = Item(user_id=1, name="Nissan GT-R", description="The Nissan GT-R is a handbuilt 2-door 2+2 \
	high performance vehicle produced by Nissan unveiled in 2007.", 
	img="Nissan_GT-R_GT3.jpg", price="$150,000", cat_id=3, subcat_id=16, category=cat1, user=User1)
session.add(Item1)
session.commit()
print "added categories!"