import csv
import io
from datetime import datetime

from flask import Flask, request, jsonify, Response;
from flask_jwt_extended import jwt_required, get_jwt_identity, JWTManager

from authentication.models import User
from configuration import Configuration;
from models import database, Product, ProductCat, Category, Order, ProductOrd;
from sqlalchemy import or_, and_;
from owner.adminDecorater import roleCheck;


application = Flask ( __name__ );
application.config.from_object ( Configuration )

jwt = JWTManager(application)


@application.route ( "/search", methods = ["GET"] )
@roleCheck(role="customer")
def getProducts ( ):
    pr = request.args.get("name", None)
    cat = request.args.get("category", None)
    categories = []
    products = []
    if(cat and pr):
        products = Product.query.join(ProductCat).join(Category).filter(
            and_(
                *[
                    Category.name.like(f"%{cat}%"),
                    Product.name.like(f"%{pr}%")
                ]
            )
        ).group_by(Product.id).all()
        categories = Category.query.join(ProductCat).join(Product).filter(
            and_(
                *[
                    Category.name.like(f"%{cat}%"),
                    Product.name.like(f"%{pr}%")
                ]
            )
        ).group_by(Category.id).all()
    elif pr:
        products = Product.query.join(ProductCat).join(Category).filter(
            and_(
                *[
                    Product.name.like(f"%{pr}%")
                ]
            )
        ).group_by(Product.id).all()
        categories = Category.query.join(ProductCat).join(Product).filter(
            and_(
                *[
                    Product.name.like(f"%{pr}%")
                ]
            )
        ).group_by(Category.id).all()
    elif cat:
        products = Product.query.join(ProductCat).join(Category).filter(
            and_(
                *[
                    Category.name.like(f"%{cat}%"),
                ]
            )
        ).group_by(Product.id).all()
        categories = Category.query.join(ProductCat).join(Product).filter(
            and_(
                *[
                    Category.name.like(f"%{cat}%"),
                ]
            )
        ).group_by(Category.id).all()
    else:
        categories = Category.query.with_entities(Category.name).all()
        products = Product.query.all()

    catResult = []
    prResult = []
    for catg in categories:
        catResult.append(catg.name)
    for product in products:
        categs = []
        for product_cat in product.category:
            categs.append(product_cat.name)
        prResult.append({
            "category": categs,
            "id": product.id,
            "name": product.name,
            "price": product.price,
        })

    final_json = {
        "categories": catResult,
        "products": prResult
    }
    return jsonify(final_json),200


@application.route ( "/order", methods = ["POST"] )
@jwt_required ( )
@roleCheck(role="customer")
def order():
    requests = request.json.get("requests","");
    if not requests:
        return jsonify({
            "message":"Field requests is missing."
        }),400
    orderprice = 0;
    identity = get_jwt_identity();
    order = Order(price=0, status="CREATED", timeStamp=datetime.now(), userEmail=identity)
    database.session.add(order);
    database.session.commit();
    i = 0;
    for req in requests:
        pid = req.get("id", "");
        if not pid:
            return jsonify({
                "message": "Product id is missing for request number {}.".format(i)
            }), 400
        quantity = req.get("quantity", "");
        if not quantity:
            return jsonify({
                "message": "Product quantity is missing for request number {}.".format(i)
            }), 400
        if not int(pid) > 0:
            return jsonify({
                "message": "Invalid product id for request number {}.".format(i)
            }), 400
        if not int(quantity) > 0:
            return jsonify({
                "message": "Invalid product quantity for request number {}.".format(i)
            }), 400
        product =  Product.query.filter(Product.id==pid).first();
        if not product:
            return jsonify({
                "message": "Invalid product for request number {}.".format(i)
            }), 400
        orderprice+= product.price * quantity;
        prodord = ProductOrd(productId = pid,ordId=order.id,price=product.price * quantity,received=0,requested=quantity)
        database.session.add(prodord)
        database.session.commit()
        i = i + 1;
    order.price=orderprice;
    database.session.commit();
    return jsonify({
        "id":order.id
    }),200



@application.route ( "/pay", methods = ["POST"] )
@roleCheck(role="customer")
def pay():
    return ""

@application.route ( "/status", methods = ["GET"] )
@jwt_required ( )
@roleCheck(role="customer")
def status():
    identity = get_jwt_identity();
    query = database.session.query(
        Order.price,
        Order.status,
        Order.timeStamp,
        Product.name,
        Product.price,
        ProductOrd.requested,
        Category.name
    ).filter (
        and_ (
            Order.id == ProductOrd.ordId,
            ProductOrd.productId == Product.id,
            Product.id == ProductCat.productId,
            Category.id == ProductCat.catId,
            Order.userEmail == identity
        )
    ).all ( )

    orders = []

    for result in query:
        order_price = result[0]
        order_status = result[1]
        order_timestamp = result[2].isoformat()
        product_name = result[3]
        product_price = result[4]
        product_quantity = result[5]
        category_name = result[6]

        order_exists = False
        for order in orders:
            if order["timestamp"] == order_timestamp:
                order_exists = True
                product_exists = False
                for product in order["products"]:
                    if product["name"] == product_name and product["price"] == product_price:
                        product_exists = True
                        product["categories"].append(category_name)
                        break
                if not product_exists:
                    newProduct = {
                        "name": product_name,
                        "price": product_price,
                        "quantity": product_quantity,
                        "categories": [category_name]
                    }
                    order["products"].append(newProduct)
                break
        if not order_exists:
            newOrder = {
                "products": [
                    {
                        "name": product_name,
                        "price": product_price,
                        "quantity": product_quantity,
                        "categories": [category_name]
                    }
                ],
                "price": order_price,
                "status": order_status,
                "timestamp": order_timestamp
            }
            orders.append(newOrder)
    database.session.close()
    return jsonify({
        "orders":orders
    }),200

@application.route ( "/delivered", methods = ["POST"] )
@roleCheck(role="customer")
def confirm():
    orderId = request.json.get("id", "");
    if not orderId:
        return jsonify({
            "message":"Missing order id."
        }),400
    if int(orderId) <= 0:
        return jsonify({
            "message": "Invalid order id."
        }), 400
    order = Order.query.filter(Order.id == orderId).first();
    if not order:
        return jsonify({
            "message": "Invalid order id."
        }), 400
    if (order.status != "PENDING"):
        return jsonify({
            "message": "Invalid order id."
        }), 400
    order.status = "COMPLETED";
    prord = ProductOrd.query.filter(ProductOrd.ordId==orderId).all();
    for p in prord:
        p.received = p.requested;
    database.session.commit();
    return Response(status=200);



if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True ,port=5002);
