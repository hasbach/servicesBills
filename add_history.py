import sys

def add_reseller_history_endpoint():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    endpoint = """
@app.route('/api/resellers/<int:reseller_id>/history', methods=['GET'])
@jwt_required()
def get_reseller_history(reseller_id):
    reseller = db.session.get(Reseller, reseller_id)
    if not reseller:
        return jsonify({'message': 'Reseller not found'}), 404

    payments = ResellerPayment.query.filter_by(reseller_id=reseller_id).order_by(ResellerPayment.date.desc()).all()
    result = [p.to_dict() for p in payments]
    return jsonify(result), 200
"""

    if "def get_reseller_history" not in content:
        # Insert it before get_resellers()
        t_target = "@app.route('/api/resellers', methods=['GET'])"
        if t_target in content:
            content = content.replace(t_target, endpoint + "\n" + t_target)
            with open('app.py', 'w', encoding='utf-8') as f:
                f.write(content)
            print("Added GET /api/resellers/<id>/history")
        else:
            print("Error: Could not find @app.route('/api/resellers', methods=['GET'])")
    else:
        print("Endpoint already exists")

if __name__ == '__main__':
    add_reseller_history_endpoint()
