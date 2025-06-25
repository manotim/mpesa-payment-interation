from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from mpesa_service import MpesaService
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # Needed for flashing

mpesa = MpesaService()

# 🔴 Temporary in-memory payment tracker
payment_statuses = {}

@app.route('/', methods=['GET', 'POST'])
def pay():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        amount = int(request.form['amount'])

        try:
            flash("Sending payment request to your phone. Please complete it...", "info")

            # Initialize status as pending
            normalized_phone = mpesa._normalize_phone(phone)
            payment_statuses[normalized_phone] = "pending"

            response = mpesa.make_payment(phone=phone, amount=amount)

            if response.get("ResponseCode") == "0":
                flash("STK push sent! Awaiting your confirmation on phone...", "info")
            else:
                flash(f"Payment failed: {response.get('errorMessage', 'Unknown error')}", "danger")

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")

    return render_template('pay.html')


@app.route('/payment-status')
def payment_status():
    phone = request.args.get('phone')
    if not phone:
        return jsonify({"status": "unknown"}), 400

    normalized_phone = mpesa._normalize_phone(phone)
    status = payment_statuses.get(normalized_phone, "pending")
    return jsonify({"status": status})


@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()
    print("Callback received:", data)

    try:
        result_code = data['Body']['stkCallback']['ResultCode']
        items = data['Body']['stkCallback'].get('CallbackMetadata', {}).get('Item', [])

        # Extract phone number and amount
        phone = None
        amount = None

        for item in items:
            if item['Name'] == 'PhoneNumber':
                phone = str(item['Value'])
            if item['Name'] == 'Amount':
                amount = item['Value']

        if phone:
            normalized_phone = mpesa._normalize_phone(phone)
            if result_code == 0:
                payment_statuses[normalized_phone] = "success"
                print(f"✅ Payment successful for {normalized_phone}, amount: {amount}")
            else:
                payment_statuses[normalized_phone] = "failed"
                print(f"❌ Payment failed or cancelled for {normalized_phone}")

        return jsonify({"ResultDesc": "Callback processed"}), 200

    except Exception as e:
        print("Error parsing callback:", str(e))
        return jsonify({"ResultDesc": "Error occurred"}), 200


@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')


if __name__ == '__main__':
    app.run(debug=True)
