import re

from flask import Flask, request, Response, jsonify;
from configuration import Configuration;
from models import database, User, UserRole;
from email.utils import parseaddr;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity;
from sqlalchemy import and_;
from owner.adminDecorater import roleCheck;

application = Flask ( __name__ );
application.config.from_object ( Configuration );

@application.route ( "/register_customer", methods = ["POST"] )
def registerCust ( ):
    email = request.json.get ( "email", "" );
    password = request.json.get ( "password", "" );
    forename = request.json.get ( "forename", "" );
    surname = request.json.get ( "surname", "" );

    emailEmpty = len ( email ) == 0;
    passwordEmpty = len ( password ) == 0;
    forenameEmpty = len ( forename ) == 0;
    surnameEmpty = len ( surname ) == 0;

    if ( emailEmpty ):
        return jsonify({
            "message": "Field email is missing!"
        }), 400
    if ( passwordEmpty ):
        return jsonify({
            "message": "Field password is missing!"
        }), 400
    if ( forenameEmpty ):
        return jsonify({
            "message": "Field forename is missing!"
        }), 400
    if ( surnameEmpty ):
        return jsonify({
            "message": "Field surname is missing!"
        }), 400

    result = parseaddr ( email );
    if ( len ( result[1] ) == 0 ):
        return jsonify({
            "message": "Invalid email!"
        }), 400

    result = parseaddr(password);
    if (len(result[1]) == 0):
        return jsonify({
            "message": "Invalid password!"
        }), 400
    if User.query.filter(User.email==email).all():
       return jsonify({
            "message": "Email already exists."
        }), 400
    user = User ( email = email, password = password, forename = forename, surename = surname );
    database.session.add ( user );
    database.session.commit ( );

    userRole = UserRole ( userId = user.id, roleId = 2 );
    database.session.add ( userRole );
    database.session.commit ( );

    return Response ( "Registration successful!", status = 200 );


@application.route ( "/register_courier", methods = ["POST"] )
def registerCour ( ):
    email = request.json.get ( "email", "" );
    password = request.json.get ( "password", "" );
    forename = request.json.get ( "forename", "" );
    surname = request.json.get ( "surname", "" );

    emailEmpty = len ( email ) == 0;
    passwordEmpty = len ( password ) == 0;
    forenameEmpty = len ( forename ) == 0;
    surnameEmpty = len ( surname ) == 0;

    if (emailEmpty):
        return jsonify({
            "message": "Field email is missing!"
        }), 400
    if (passwordEmpty):
        return jsonify({
            "message": "Field password is missing!"
        }), 400
    if (forenameEmpty):
        return jsonify({
            "message": "Field forename is missing!"
        }), 400
    if (surnameEmpty):
        return jsonify({
            "message": "Field surname is missing!"
        }), 400

    result = parseaddr(email);
    if (len(result[1]) == 0):
        return jsonify({
            "message": "Invalid email!"
        }), 400

    result = parseaddr(password);
    if (len(result[1]) == 0):
        return jsonify({
            "message": "Invalid password!"
        }), 400
    if User.query.filter(User.email == email).all():
        return jsonify({
            "message": "Email already exists."
        }), 400

    user = User ( email = email, password = password, forename = forename, surename = surname );
    database.session.add ( user );
    database.session.commit ( );

    userRole = UserRole ( userId = user.id, roleId = 3 );
    database.session.add ( userRole );
    database.session.commit ( );

    return Response ( "Registration successful!", status = 200 );

jwt = JWTManager ( application );

@application.route ( "/login", methods = ["POST"] )
def login ( ):
    email = request.json.get ( "email", "" );
    password = request.json.get ( "password", "" );

    emailEmpty = len ( email ) == 0;
    passwordEmpty = len ( password ) == 0;

    if (emailEmpty):
        return jsonify({
            "message": "Field email is missing!"
        }), 400
    if (passwordEmpty):
        return jsonify({
            "message": "Field password is missing!"
        }), 400
    result = parseaddr(email);
    if (len(result[1]) == 0):
        return jsonify({
            "message": "Invalid email!"
        }), 400

    user = User.query.filter ( and_ ( User.email == email, User.password == password ) ).first ( );

    if ( not user ):
        return jsonify({
            "message": "Invalid credentials!"
        }), 400

    additionalClaims = {
            "forename": user.forename,
            "surname": user.surename,
            "roles": [ str ( role ) for role in user.roles ]
    }

    accessToken = create_access_token ( identity = user.email, additional_claims = additionalClaims );

    # return Response ( accessToken, status = 200 );
    return jsonify ( accessToken = accessToken, status = 200 );

@application.route ( "/check", methods = ["POST"] )
@jwt_required ( )
def check ( ):
    return "Token is valid!";



@application.route("/delete", methods=["POST"])
@jwt_required ( )
def delete():

    identity = get_jwt_identity();
    user = User.query.filter(User.email == identity).first();
    if not user:
        return jsonify({
            "message": "Unknown user."
        }), 400
    if user:
        User.query.filter(User.email == identity).delete()
        database.session.commit()
        return Response(status=200)



if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, port = 5000 );