import sys, re

def fix_app():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    renew_match = re.search(r'(def renew_subscription\(customer_id\):.*?)(?=^@app\.route|\Z)', content, re.DOTALL | re.MULTILINE)
    clean_renew = '''def renew_subscription(customer_id):
    try:
        customer = db.session.get(Customer, customer_id)
        if not customer:
            return jsonify({'message': 'Customer not found!'}), 404

        subscription_plan = db.session.get(SubscriptionPlan, customer.subscription_plan_id)
        if not subscription_plan:
            return jsonify({'message': 'Subscription plan not found for this customer!'}), 404
        today = datetime.utcnow()
        current_expiry_date = customer.subscription_expiry_date
        renewal_basis_date = current_expiry_date if current_expiry_date and current_expiry_date > today else today

        if subscription_plan.billing_cycle == 'monthly':
            if current_expiry_date:
                day = current_expiry_date.day
                next_month = renewal_basis_date + relativedelta(months=1)
                last_day_of_next_month = calendar.monthrange(next_month.year, next_month.month)[1]
                day = min(day, last_day_of_next_month)
                new_expiry_date = next_month.replace(day=day)
            else:
                new_expiry_date = renewal_basis_date + relativedelta(months=1)
        elif subscription_plan.billing_cycle == 'yearly':
            new_expiry_date = renewal_basis_date + relativedelta(years=1)
        else:
            return jsonify({'message': 'Unrecognized billing cycle for subscription plan.'}), 400

        customer.subscription_expiry_date = new_expiry_date
        customer.is_subscription_active = True

        renewal_amount = subscription_plan.price - customer.discount
        if renewal_amount < 0:
            renewal_amount = 0.0

        if renewal_amount > 0 and not has_pending_payment(customer.id, new_expiry_date):
            if customer.reseller_id:
                reseller = db.session.get(Reseller, customer.reseller_id)
                if reseller:
                    reseller.balance += renewal_amount
                    reseller_payment = ResellerPayment(
                        reseller_id=reseller.id,
                        amount=renewal_amount,
                        type='credit_added',
                        description=f'Renewal for customer {customer.name}'
                    )
                    db.session.add(reseller_payment)
                    db.session.commit()
                    
                    try:
                        class FakeCustomer:
                            phone = reseller.phone
                            whatsapp_notifications_enabled = True
                            id = reseller.id
                            name = reseller.name
                            
                        send_whatsapp_message(
                            FakeCustomer(),
                            event_type='reseller_customer_renewed',
                            context={'amount': renewal_amount, 'balance': reseller.balance, 'customer_name': customer.name}
                        )
                    except Exception as wa_error:
                        logging.error(f"Failed to send WA message on renew to reseller: {wa_error}")
            else:
                new_payment = Payment(
                    customer_id=customer.id,
                    amount=renewal_amount,
                    paid=False,
                    date=current_expiry_date,
                    pre_payment=False
                )
                db.session.add(new_payment)
                
                customer.balance -= renewal_amount
                db.session.commit()

                try:
                    send_whatsapp_message(
                        customer,
                        event_type='subscription_renewed',
                        context={'expiry_date': new_expiry_date.strftime('%Y-%m-%d')}
                    )
                except Exception as wa_error:
                    logging.error(f"Failed to send WA message on renew: {wa_error}")
        else:
            db.session.commit()

        return jsonify({
            'message': 'Subscription renewed successfully!',
            'customer_id': customer.id,
            'new_expiry_date': new_expiry_date.strftime('%Y-%m-%d'),
            'renewal_payment_amount': float(renewal_amount),
            'customer_new_balance': float(customer.balance),
            'reseller_billed': True if customer.reseller_id else False
        }), 200

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f"Error renewing subscription: {str(e)}"}), 500
'''
    content = content[:renew_match.start()] + clean_renew + '\n' + content[renew_match.end():]

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print('Fixed app.py successfully!')

if __name__ == '__main__':
    fix_app()
