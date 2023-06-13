import csv
import io
import json

from flask import Flask, request, jsonify, Response;
from flask_jwt_extended import JWTManager

from configuration import Configuration;
from models import database, Product, ProductCat, Category, ProductOrd;
from sqlalchemy import or_, and_, func;
from adminDecorater import roleCheck;


application = Flask ( __name__ );
application.config.from_object ( Configuration )
jwt = JWTManager ( application );


@application.route("/category_statistics", methods=["GET"])
@roleCheck(role="admin")
def cats():
    statistics = []
    categories = Category.query.outerjoin(ProductCat).outerjoin(Product) \
        .outerjoin(ProductOrd).group_by(Category.id) \
        .order_by(func.sum(ProductOrd.requested).desc()).order_by(Category.name)
    for category in categories:
        statistics.append(category.name)
    return jsonify({
        "statistics": statistics
    }),200


@application.route("/product_statistics", methods=["GET"])
@roleCheck(role="admin")
def prods():
    statistics = []
    prod2 = database.session.query(
        Product.name,
        func.sum(ProductOrd.received),
        func.sum(ProductOrd.requested-ProductOrd.received)
    ).join(
        ProductOrd
    ).group_by(Product.id, Product.name).all();
    statistics = []
    for pp in prod2:
        statistics.append({
            "name": pp[0],
            "sold": int(pp[1]),
            "waiting": int(pp[2])
        })
    return jsonify({
        "statistics": statistics
    }), 200


@application.route("/update", methods=["POST"])
@roleCheck(role="admin")
def update():
    content = request.files["file"].stream.read().decode("utf-8");
    stream = io.StringIO(content);
    reader = csv.reader(stream);
    if not request.files.get("file", None):
        return jsonify({
            "message": "Field file is missing."
        }), 400
    categories = [];
    products = [];
    i = 0
    for row in reader:
        if len(row) != 3:
            return jsonify({
                "message": "Incorrect number of values on line {}.".format(i)
            }), 400
        if not float(row[2]) > 0:
            return jsonify({
                "message": "Incorrect price on line {}.".format(i)
            }), 400
        p = Product.query.filter(Product.name==row[1]).first();
        if p:
            return jsonify({
                "message": "Product {} already exists.".format(row[1])
            }), 400
        categories = [item.strip ( ) for item in row[0].split ( "|" )];
        product = Product(name=(row[1]), price=float(row[2]));
        database.session.add(product);
        database.session.commit();
        for cat in categories:
            categ = Category.query.filter(Category.name == cat).first();
            idc = 0;
            if not categ:
                newCategory = Category(name=cat);
                database.session.add(newCategory);
                database.session.commit();
                idc = newCategory.id;
            else:
                idc = categ.id;
            pc = ProductCat(productId=product.id,catId = idc);
            database.session.add(pc);
            database.session.commit();
        i = i + 1;
        #products.append(product);
    return Response(status=200);




if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, port=5001 );
