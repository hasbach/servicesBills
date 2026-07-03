import sys

def fix_app():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the start of activate_subscription
    act_idx = content.find('def activate_subscription(customer_id):')
    if act_idx == -1:
        print("Could not find activate_subscription")
        sys.exit(1)

    # Find the next function after activate_subscription to know where to end
    cancel_idx = content.find('def cancel_subscription(customer_id):')
    if cancel_idx == -1:
        print("Could not find cancel_subscription")
        sys.exit(1)

    # Extract the pre-activate and post-activate parts
    # Look for the @app.route decorator right before cancel_subscription
    route_cancel_idx = content.rfind('@app.route', act_idx, cancel_idx)
    if route_cancel_idx == -1:
        route_cancel_idx = cancel_idx - 100 # Rough estimate if we can't find it

    clean_activate = """def activate_subscription(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'message': 'Customer not found!'}), 404

    # Check if the subscription is already active
    if customer.is_subscription_active:
        return jsonify({'message': 'Subscription is already active!'}), 400

    try:
        # Reactivate the subscription
        customer.is_subscription_active = True

        # Set a new subscription expiry date based on the billing cycle from today
        subscription_plan = db.session.get(SubscriptionPlan, customer.subscription_plan_id)
        if not subscription_plan:
            db.session.rollback()
            return jsonify({'message': 'Subscription plan not found for customer!'}), 404

        if subscription_plan.billing_cycle == 'monthly':
            customer.subscription_expiry_date = datetime.utcnow() + relativedelta(months=1)
        elif subscription_plan.billing_cycle == 'yearly':
            customer.subscription_expiry_date = datetime.utcnow() + relativedelta(years=1)
        else:
            # Default to monthly if billing cycle is unrecognized
            customer.subscription_expiry_date = datetime.utcnow() + relativedelta(months=1)

        db.session.commit()

        # ── Send WhatsApp notification (API mode) ──────────────────────────────
        try:
            send_whatsapp_message(
                customer,
                event_type='subscription_renewed',
                context={'expiry_date': customer.subscription_expiry_date.strftime('%Y-%m-%d')}
            )
        except Exception as wa_error:
            logging.error(f"Failed to send WA message on activate: {wa_error}")
        # ──────────────────────────────────────────────────────────────────────

        return jsonify({
            'message': 'Subscription activated successfully!',
            'subscription_expiry_date': customer.subscription_expiry_date.strftime('%Y-%m-%d')
        }), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

"""

    content = content[:act_idx] + clean_activate + content[route_cancel_idx:]


    # Now find renew_subscription
    renew_idx = content.find('def renew_subscription(customer_id):')
    if renew_idx == -1:
        print("Could not find renew_subscription")
        sys.exit(1)

    exp_idx = content.find('def get_expense_categories():')
    if exp_idx == -1:
        print("Could not find get_expense_categories")
        sys.exit(1)

    route_exp_idx = content.rfind('@app.route', renew_idx, exp_idx)
    
    clean_renew = """def renew_subscription(customer_id):
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

"""
    content = content[:renew_idx] + clean_renew + content[route_exp_idx:]

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Fixed app.py successfully!")

if __name__ == '__main__':
    fix_app()
