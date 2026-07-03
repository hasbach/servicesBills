
# --- Reseller API Endpoints ---

@app.route('/api/resellers', methods=['GET'])
@jwt_required()
def get_resellers():
    resellers = Reseller.query.all()
    result = []
    for r in resellers:
        data = r.to_dict()
        data['customers'] = [c.id for c in r.customers]
        result.append(data)
    return jsonify(result), 200

@app.route('/api/resellers', methods=['POST'])
@jwt_required()
def create_reseller():
    data = request.json
    try:
        new_reseller = Reseller(
            name=data['name'],
            phone=data['phone'],
            type=data['type'], # 'type1' or 'type2'
            balance=float(data.get('balance', 0.0))
        )
        db.session.add(new_reseller)
        db.session.commit()
        return jsonify({'message': 'Reseller created successfully!', 'reseller': new_reseller.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/resellers/<int:reseller_id>', methods=['PUT'])
@jwt_required()
def update_reseller(reseller_id):
    data = request.json
    reseller = db.session.get(Reseller, reseller_id)
    if not reseller:
        return jsonify({'message': 'Reseller not found!'}), 404
    try:
        reseller.name = data.get('name', reseller.name)
        reseller.phone = data.get('phone', reseller.phone)
        reseller.type = data.get('type', reseller.type)
        if 'balance' in data:
            reseller.balance = float(data['balance'])
        db.session.commit()
        return jsonify({'message': 'Reseller updated successfully!', 'reseller': reseller.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/resellers/<int:reseller_id>/add_credit', methods=['POST'])
@jwt_required()
def add_reseller_credit(reseller_id):
    data = request.json
    reseller = db.session.get(Reseller, reseller_id)
    if not reseller:
        return jsonify({'message': 'Reseller not found!'}), 404
    
    amount = float(data.get('amount', 0))
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400

    try:
        reseller.balance += amount
        new_payment = ResellerPayment(
            reseller_id=reseller.id,
            amount=amount,
            type='credit_added',
            description=data.get('description', 'Manual credit addition')
        )
        db.session.add(new_payment)
        db.session.commit()

        # Send WhatsApp Notification
        class FakeCustomer:
            phone = reseller.phone
            whatsapp_notifications_enabled = True
            id = reseller.id
            name = reseller.name

        send_whatsapp_message(
            FakeCustomer(),
            event_type='reseller_credit_added',
            context={'amount': amount, 'balance': reseller.balance}
        )

        return jsonify({'message': 'Credit added successfully!', 'reseller': reseller.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/resellers/<int:reseller_id>/apply_discount', methods=['POST'])
@jwt_required()
def apply_reseller_discount(reseller_id):
    data = request.json
    reseller = db.session.get(Reseller, reseller_id)
    if not reseller:
        return jsonify({'message': 'Reseller not found!'}), 404
    
    amount = float(data.get('amount', 0))
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400

    try:
        reseller.balance -= amount
        new_payment = ResellerPayment(
            reseller_id=reseller.id,
            amount=amount,
            type='discount_applied',
            description=data.get('description', f'Discount applied')
        )
        db.session.add(new_payment)
        db.session.commit()

        # Send WhatsApp Notification
        class FakeCustomer:
            phone = reseller.phone
            whatsapp_notifications_enabled = True
            id = reseller.id
            name = reseller.name

        send_whatsapp_message(
            FakeCustomer(),
            event_type='reseller_discount_applied',
            context={'amount': amount, 'balance': reseller.balance}
        )

        return jsonify({'message': 'Discount applied successfully!', 'reseller': reseller.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/resellers/<int:reseller_id>/collect_payment', methods=['POST'])
@jwt_required()
def collect_reseller_payment(reseller_id):
    data = request.json
    reseller = db.session.get(Reseller, reseller_id)
    if not reseller:
        return jsonify({'message': 'Reseller not found!'}), 404
    
    amount = float(data.get('amount', 0))
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400

    try:
        reseller.balance -= amount
        new_payment = ResellerPayment(
            reseller_id=reseller.id,
            amount=amount,
            type='payment_received',
            description=data.get('description', 'Payment received')
        )
        db.session.add(new_payment)
        db.session.commit()

        return jsonify({'message': 'Payment collected successfully!', 'reseller': reseller.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

