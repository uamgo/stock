"""
An application with API endpoints to perform Create, Retrieve, Update, and Delete operations on the above data using a Flask server.
Your application should allow you to add a product, retrieve the products, retrieve a specific product with its id, update a specific product with its id, and delete a product with its id. 
All these operations will be achieved through the REST API endpoints in your Flask server.
"""


from flask import Flask # import the Flask class from the flask module
from flask import request # import the request class from the flask module for handling and making HTTP requests
from flask import jsonify # import the jsonify class from the flask module for converting a Python dictionary or list into JSON format
from flask_cors import CORS # import the CORS class from the flask_cors module, this allows cross origin resource sharing which allows for use of your api by other domains
import sort_qf as stock
import time
# CORS is a Flask extension for handling Cross Origin Resource Sharing (CORS), making cross-origin AJAX possible. It is a way to relax the same-origin policy, which is a set of restrictions imposed by browsers to prevent interactions between resources from different origins.
# you can configure CORS options to specify allowed origins, headers, and other settings according to your requirements.


app = Flask(__name__) # creates an instance of the Flask class called "app", this allows Flask to find the location and root path of the application's resources, such as templates and static files.
# __name__ is the name of the current Python module. The app needs to know where it's located to set up some paths, and __name__ is a convenient way to tell it that.
# you can also use the specific name of the file, but using __name__ is better because it's more reliable and just points to whatever module is currently being used as the entry point (so it won't break if you change the file name).
# The app variable is an instance of Flask, so you can use it like any other Python object. The Flask class has a constructor that takes the name of the current module (__name__) as argument.

CORS(app) # use the CORS class to pass in the app variable, this allows cross origin resource sharing which allows for use of your api by other domains

a_stock = stock.StockA()

products = [
    {'id': 143, 'name': 'Notebook', 'price': 5.49},
    {'id': 144, 'name': 'Black Marker', 'price': 1.99}
]

# REST API endpoints: (The REST API endpoints are the URLs that your application will expose to the outside world. These URLs will be used to perform CRUD operations on your data.)
# Create a product: POST /products
# Retrieve all products: GET /products
# Retrieve a specific product: GET /products/<id>
# Update a specific product: PUT /products/<id>
# Delete a product: DELETE /products/<id>

# Retrieve all products: GET /products. This endpoint should return a JSON representation of all the products in the products list. Example request - http://localhost:5000/products
@app.route('/products', methods=['GET'], strict_slashes=False) # strict_slashes=False allows for both '/products' and '/products/' to return the same thing and methods=['GET'] specifies that this endpoint will only accept GET requests
def get_stocks():
    start_ts = time.time()
    a_stock.args.concept_num = 1
    rs = a_stock.run()
    # print(f"rs type = {type(rs)}")
    rs.sort(reverse=True, key=lambda r: r['score'])
    code_set = set()
    rs_str = ''
    print("\n\n---------- Final result ------------\n")
    for idx, row in enumerate(rs):
        if not row['code'] in code_set:
            code_set.add(row['code'])
            code_link = a_stock.to_link(row['code'])
            # print(row)
            row['name'] = f'<a href="{code_link}">{row["name"]}</a>'
            rs_str += f'<p>{row}</p>'

    end_ts = time.time()
    back_test_msg = f"回测到: {a_stock.back_test_date} " if a_stock.args.back_test > 1 else ""

    return f'''
<div>{rs_str}</div>
<br/>
<p>Total: {len(code_set)} stocks<p>
<p>Elapse: {'%.2f'%(end_ts - start_ts)}, {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}</p>
<p>注意：交易日00:00 ~ 9:15之间的数据不准确，不要运行此脚本！</p>
<p>{back_test_msg}</p>
    '''

# Retrieve a specific product: GET /products/<id>. This endpoint should return a JSON representation of the product with the given id. Example request - http://localhost:5000/products/143
@app.route('/products/<int:id>', methods=['GET'], strict_slashes=False) # strict_slashes=False allows for both '/products/<int:id>' and '/products/<int:id>/' to return the same thing and methods=['GET'] specifies that this endpoint will only accept GET requests
def get_product(id):
    """returns a specific product"""
    for product in products:
        if product['id'] == id:     # if the product id matches the id passed in, return the product as JSON
            return jsonify(product) # return the product as JSON
    return jsonify({'error': 'Product not found'}), 404 # return an error if the product is not found

# Create a product: POST /products. This endpoint should create a new product in the products list. The request body should contain the name and price of the product. Example request - http://localhost:5000/products
@app.route('/products', methods=['POST'], strict_slashes=False) # strict_slashes=False allows for both '/products' and '/products/' to return the same thing and methods=['POST'] specifies that this endpoint will only accept POST requests
def create_product():
    """creates a new product"""
    product = request.get_json() # get the request body as JSON
    if not product:
        return jsonify({'error': 'Product not found'}), 400 # return an error if the request body is not JSON
    if 'name' not in product:
        return jsonify({'error': 'Missing name'}), 400 # return an error if the request body does not contain a name
    if 'price' not in product:
        return jsonify({'error': 'Missing price'}), 400 # return an error if the request body does not contain a price
    if 'id' not in product:
        product['id'] = len(products) + 1 # add an id to the new product if it is not already in the request body
    products.append(product) # add the new product to the products list
    return jsonify(product), 201 # return the new product as JSON with a 201 status code (201 = created)
    

# Update a specific product: PUT /products/<id>. This endpoint should update the product with the given id in the products list. The request body should contain the name and price of the product. Example request - http://localhost:5000/products/143
@app.route('/products/<int:id>', methods=['PUT'], strict_slashes=False) # strict_slashes=False allows for both '/products/<int:id>' and '/products/<int:id>/' to return the same thing and methods=['PUT'] specifies that this endpoint will only accept PUT requests
def update_product(id):
    id = int(id) # convert the id to an integer
    updated_product = request.get_json() # get the request body as JSON
    for product in products:
        if product['id'] == id:
            for key, value in updated_product.items():
                product[key] = value
            return jsonify(product), 200 # return the updated product as JSON with a 200 status code (200 = OK)
    return jsonify({'error': 'Product not found'}), 404 # return an error if the product is not found

# Delete a product: DELETE /products/<id>. This endpoint should delete the product with the given id from the products list. Example request - http://localhost:5000/products/143
@app.route('/products/<int:id>', methods=['DELETE'], strict_slashes=False) # strict_slashes=False allows for both '/products/<int:id>' and '/products/<int:id>/' to return the same thing and methods=['DELETE'] specifies that this endpoint will only accept DELETE requests
def delete_product(id):
    id = int(id) # convert the id to an integer
    for product in products:
        if product['id'] == id:
            products.remove(product)
            return jsonify({'message': 'Product deleted'}), 200 # return a message that the product was deleted with a 200 status code (200 = OK)
    return jsonify({'error': 'Product not found'}), 404 # return an error if the product is not found

if __name__ == '__main__': # if the script is executed directly, the code block is executed, if the script is imported, the code block is not executed.
    app.run(host='0.0.0.0', port='5070', debug = True) #specify the url and port, and debug = True allows for the server to automatically reload when changes are made to the code
    
# on terminal enter = 'export FLASK_APP=0-hello_route.py' to set the file to be run as the flask app
# on terminal enter = 'flask run' to run the flask app
# or enter = 'python3 <filename>' to run the file directly
# The method should be restarted manually for any change in the code. To overcome this, the debug support is enabled so as to track any error.


# To test the endpoints, you can use Postman, a popular tool for testing REST APIs. You can also use curl, a command line tool for making HTTP requests.

# To test the GET /products endpoint, you can use the following curl command: curl http://localhost:5070/products
# To test the GET /products/<id> endpoint, you can use the following curl command: curl http://localhost:5070/products/143
# To test the POST /products endpoint, you can use the following curl command: 
    # curl -X POST -H "Content-Type: application/json" -d '{"name": "Pencil", "price": 1.99}' http://localhost:5070/products (x = specify the request method, H = specify the request header, d = specify the request body)
# To test the PUT /products/<id> endpoint, you can use the following curl command:
    # curl -X PUT -H "Content-Type: application/json" -d '{"name": "Pencil", "price": 1.99}' http://localhost:5070/products/143 (x = specify the request method, H = specify the request header, d = specify the request body)
# To test the DELETE /products/<id> endpoint, you can use the following curl command: curl -X DELETE http://localhost:5070/products/143 (x = specify the request method)


"""

While the GET endpoints are easy to test with curl using a command line interface, the POST, PUT and DELETE commands can be cumbersome. 
To circumvent this problem, you can use Postman, which is a software that is available as a service.

Postman is a software that allows you to test your APIs. It is available as a service, and also as a desktop application. 
You can download the desktop application from https://www.getpostman.com/downloads/.

"""