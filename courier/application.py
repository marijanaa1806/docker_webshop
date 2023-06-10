import csv
import io

from flask import Flask, request, jsonify, Response, session;
from flask_jwt_extended import JWTManager

from authentication.models import User
from configuration import Configuration;
from models import database, Product, ProductCat, Category, Order;
from sqlalchemy import or_, and_;
from owner.adminDecorater import roleCheck;


application = Flask ( __name__ );
application.config.from_object ( Configuration )
jwt = JWTManager(application)



@application.route ( "/orders_to_deliver", methods = ["GET"] )
@roleCheck(role="courier")
def ordersToD():
    orders = [];
    result = Order.query.filter(Order.status == "CREATED").all()
    for res in result:
        orders.append({
            "id": res.id,
            "email": res.userEmail,
        })
    return jsonify({
        "orders":orders
    }),200




@application.route ( "/pick_up_order", methods = ["POST"] )
@roleCheck(role="courier")
def ordersTopickup():
    orderId = request.json.get("id", "");
    if not orderId:
        return jsonify({
            "message":"Missing order id."
        }),400
    if not int(orderId) > 0:
        return jsonify({
            "message": "Invalid order id."
        }), 400
    order = Order.query.filter(Order.id == orderId).first();
    if not order:
        return jsonify({
            "message": "Invalid order id."
        }), 400
    if (order.status=="PENDING" or order.status=="COMPLETE"):
        return jsonify({
            "message": "Invalid order id."
        }), 400
    order.status = "PENDING";
    database.session.commit();
    return Response(status=200);



if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, port=5003 );