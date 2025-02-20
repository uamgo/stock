from flask import Flask, request, jsonify
from flask_cors import CORS
import sort_qf as stock
import time

app = Flask(__name__)
CORS(app)

a_stock = stock.StockA()

products = [
    {'id': 143, 'name': 'Notebook', 'price': 5.49},
    {'id': 144, 'name': 'Black Marker', 'price': 1.99}
]

@app.route('/products', methods=['GET'], strict_slashes=False)
def get_stocks():
    start_ts = time.time()
    if request.args.get('n'):
        a_stock.args.concept_num = int(request.args.get('n'))
    rs = a_stock.run()
    rs.sort(reverse=True, key=lambda r: r['score'])
    code_set = set()
    rs_str = ''.join(
        f'<h1>{row}</h1>' for row in rs if row['code'] not in code_set and not code_set.add(row['code'])
    )

    end_ts = time.time()
    back_test_msg = f"Backtest to: {a_stock.back_test_date} " if a_stock.args.back_test > 1 else ""

    return f'''
<div>{rs_str}</div>
<br/>
<p>Total: {len(code_set)} stocks<p>
<p>Elapsed: {'%.2f' % (end_ts - start_ts)}, {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}</p>
<p>Note: Data between 00:00 and 9:15 on trading days is inaccurate, do not run this script!</p>
<p>{back_test_msg}</p>
    '''

@app.route('/products/<int:id>', methods=['GET'], strict_slashes=False)
def get_product(id):
    product = next((p for p in products if p['id'] == id), None)
    if product:
        return jsonify(product)
    return jsonify({'error': 'Product not found'}), 404

@app.route('/products', methods=['POST'], strict_slashes=False)
def create_product():
    product = request.get_json()
    if not product or 'name' not in product or 'price' not in product:
        return jsonify({'error': 'Invalid input'}), 400
    product['id'] = product.get('id', len(products) + 1)
    products.append(product)
    return jsonify(product), 201

@app.route('/products/<int:id>', methods=['PUT'], strict_slashes=False)
def update_product(id):
    updated_product = request.get_json()
    product = next((p for p in products if p['id'] == id), None)
    if product:
        product.update(updated_product)
        return jsonify(product), 200
    return jsonify({'error': 'Product not found'}), 404

@app.route('/products/<int:id>', methods=['DELETE'], strict_slashes=False)
def delete_product(id):
    product = next((p for p in products if p['id'] == id), None)
    if product:
        products.remove(product)
        return jsonify({'message': 'Product deleted'}), 200
    return jsonify({'error': 'Product not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5070, debug=True)