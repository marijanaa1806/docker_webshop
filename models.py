from flask_sqlalchemy import SQLAlchemy;

database = SQLAlchemy ( );

class ProductCat ( database.Model ):
    __tablename__ = "productcat";
    id = database.Column ( database.Integer, primary_key = True );
    productId = database.Column ( database.Integer, database.ForeignKey ( "products.id" ), nullable = False );
    catId = database.Column ( database.Integer, database.ForeignKey ( "category.id" ), nullable = False );


class ProductOrd ( database.Model ):
    __tablename__ = "productord";
    id = database.Column ( database.Integer, primary_key = True );
    productId = database.Column ( database.Integer, database.ForeignKey ( "products.id" ), nullable = False );
    ordId = database.Column ( database.Integer, database.ForeignKey ( "orders.id" ), nullable = False );
    price = database.Column(database.Float, nullable=False)
    received = database.Column(database.Integer, nullable=False)
    requested = database.Column(database.Integer, nullable=False)


class Product( database.Model ):
    __tablename__="products";
    id = database.Column( database.Integer,  primary_key = True);
    name = database.Column(database.String(256), nullable=False);
    price = database.Column(database.Float, nullable=False);

    category = database.relationship("Category", secondary=ProductCat.__table__, back_populates="products");
    orders = database.relationship("Order", secondary=ProductOrd.__table__, back_populates="products");

    def __repr__(self):
        return "({}, {}, {})".format(self.id, self.name, self.price);


class Category ( database.Model ):
    __tablename__ = "category";
    id = database.Column ( database.Integer, primary_key = True );
    name = database.Column ( database.String ( 256 ), nullable = False );

    products = database.relationship ( "Product", secondary = ProductCat.__table__, back_populates = "category" );

    def __repr__ ( self ):
        return "({}, {})".format ( self.id, self.name );


class Order(database.Model):
    __tablename__ = "orders"
    id = database.Column(database.Integer, primary_key = True)
    price = database.Column(database.Float, nullable = False)
    status = database.Column(database.String(256), nullable = False)
    timeStamp = database.Column(database.DateTime, nullable = False)
    userEmail = database.Column(database.String(256), nullable = False)

    products = database.relationship("Product", secondary=ProductOrd.__table__, back_populates="orders")

    def __repr__(self):
        return "({}, {}, {}, {})".format(self.id, self.cost, self.status, self.date)
