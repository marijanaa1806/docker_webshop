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
    cat = request.args["category"];
    pr = request.args["name"];
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

    json_category = []
    for cat in categories:
        json_category.append(cat[0])
    json_product = []
    for product in products:
        product_categories = []
        for product_cat in product.category:
            product_categories.append(product_cat.name)
        json_product.append({
            "category": product_categories,
            "id": product.id,
            "name": product.name,
            "price": product.price,
        })

    final_json = {
        "categories": json_category,
        "products": json_product
    }
    return jsonify(final_json)


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
    #user = User.query.filter(User.email==identity).first();
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
        product = Product.query.get(pid);
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
@roleCheck(role="customer")
def status():
    query = database.session.query(
        Order.price,
        Order.status,
        Order.timestamp,
        Product.name,
        Product.price,
        ProductOrd.received,
        Category.name
    ).join(ProductOrd).join(Product).join(ProductCat).join(Category).all()

    # Generate the response structure
    response = {"orders": []}
    order_dict = {}

    for result in query:
        order_price = result[0]
        order_status = result[1]
        order_timestamp = result[2].isoformat()
        product_name = result[3]
        product_price = result[4]
        product_quantity = result[5]
        category_name = result[6]

        product_dict = {
            "name": product_name,
            "price": product_price,
            "quantity": product_quantity,
            "categories": [category_name]
            #appending categories???????

        }

        # Check if the order already exists in the order_dict
        if order_timestamp not in order_dict:
            order_dict[order_timestamp] = {
                "products": [product_dict],
                "price": order_price,
                "status": order_status,
                "timestamp": order_timestamp
            }
        else:
            # Append the product to the existing order
            order_dict[order_timestamp]["products"].append(product_dict)

    # Append the orders to the response
    response["orders"] = list(order_dict.values())

    return jsonify(response),200

@application.route ( "/delivered", methods = ["POST"] )
@roleCheck(role="customer")
def confirm():
    orderId = request.json.get("id", "");
    if not orderId:
        return jsonify({
            "message":"Missing order id."
        }),400
    if int(orderId)<=0:
        return jsonify({
            "message": "Invalid order id."
        }), 400
    order = Order.query.filter(Order.id==orderId).first();
    if not order:
        return jsonify({
            "message": "Invalid order id."
        }), 400
    if (order.status!="PENDING"):
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