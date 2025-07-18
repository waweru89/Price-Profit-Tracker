from flask import Flask, render_template, request, redirect, send_file, session, url_for, flash
from flask_session import Session
from supabase_client import create_user, sign_in_user
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "your-secret-key"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# CSV paths
DATA_DIR = "data"
PRODUCTS_CSV = f"{DATA_DIR}/products.csv"
SALES_CSV = f"{DATA_DIR}/sales.csv"
EXPENSES_CSV = f"{DATA_DIR}/expenses.csv"

# Ensure data folder and CSVs exist
os.makedirs(DATA_DIR, exist_ok=True)

for file, cols in [
    (PRODUCTS_CSV, ['Date', 'Product', 'Buying Price', 'Quantity']),
    (SALES_CSV, ['Date', 'Product', 'Quantity Sold', 'Actual Sale Price']),
    (EXPENSES_CSV, ['Date', 'Description', 'Amount'])
]:
    if not os.path.exists(file):
        pd.DataFrame(columns=cols).to_csv(file, index=False)

@app.route('/')
def index():
    if not session.get("user_email"):
        return redirect(url_for('login'))
    return render_template('index.html', user_email=session['user_email'])

# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            create_user(email, password)
            flash("Account created. Please log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Signup error: {e}", "danger")
    return render_template('signup.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            sign_in_user(email, password)
            session['user_email'] = email
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash("Login failed. Please try again.", "danger")
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user_email', None)
    flash("Logged out.", "info")
    return redirect(url_for('login'))

@app.route('/add_stock', methods=['POST'])
def add_stock():
    if not session.get("user_email"):
        return redirect(url_for('login'))

    date = request.form['stock_date']
    product = request.form['product']
    buying_price = float(request.form['buying_price'])
    quantity = int(request.form['quantity'])

    df = pd.read_csv(PRODUCTS_CSV)
    df = df.append({'Date': date, 'Product': product, 'Buying Price': buying_price, 'Quantity': quantity}, ignore_index=True)
    df.to_csv(PRODUCTS_CSV, index=False)

    return redirect('/')

@app.route('/add_sale', methods=['POST'])
def add_sale():
    if not session.get("user_email"):
        return redirect(url_for('login'))

    date = request.form['sale_date']
    product = request.form['sale_product']
    quantity_sold = int(request.form['quantity_sold'])
    sale_price = float(request.form['actual_price'])

    df = pd.read_csv(SALES_CSV)
    df = df.append({'Date': date, 'Product': product, 'Quantity Sold': quantity_sold, 'Actual Sale Price': sale_price}, ignore_index=True)
    df.to_csv(SALES_CSV, index=False)

    return redirect('/')

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if not session.get("user_email"):
        return redirect(url_for('login'))

    date = request.form['expense_date']
    description = request.form['description']
    amount = float(request.form['amount'])

    df = pd.read_csv(EXPENSES_CSV)
    df = df.append({'Date': date, 'Description': description, 'Amount': amount}, ignore_index=True)
    df.to_csv(EXPENSES_CSV, index=False)

    return redirect('/')

@app.route('/download/<string:datatype>')
def download(datatype):
    if datatype == 'selling_price':
        df = pd.read_csv(PRODUCTS_CSV)
        df['Selling Price'] = df['Buying Price'] * 1.4
        df[['Product', 'Selling Price']].to_csv(f"{DATA_DIR}/selling_price.csv", index=False)
        return send_file(f"{DATA_DIR}/selling_price.csv", as_attachment=True)

    elif datatype == 'monthly_summary':
        df_sales = pd.read_csv(SALES_CSV)
        df_expenses = pd.read_csv(EXPENSES_CSV)

        df_sales['Date'] = pd.to_datetime(df_sales['Date'])
        df_expenses['Date'] = pd.to_datetime(df_expenses['Date'])

        df_sales['Profit'] = (df_sales['Actual Sale Price'] - get_buying_price(df_sales['Product'])) * df_sales['Quantity Sold']
        monthly_profit = df_sales.groupby(df_sales['Date'].dt.to_period('M')).agg({'Profit': 'sum'}).reset_index()

        monthly_expense = df_expenses.groupby(df_expenses['Date'].dt.to_period('M')).agg({'Amount': 'sum'}).reset_index()
        merged = pd.merge(monthly_profit, monthly_expense, on='Date', how='outer').fillna(0)
        merged['Net Profit'] = merged['Profit'] - merged['Amount']

        merged.to_csv(f"{DATA_DIR}/monthly_summary.csv", index=False)
        return send_file(f"{DATA_DIR}/monthly_summary.csv", as_attachment=True)

    elif datatype == 'expenses':
        return send_file(EXPENSES_CSV, as_attachment=True)

    elif datatype == 'net_profit':
        df_sales = pd.read_csv(SALES_CSV)
        df_expenses = pd.read_csv(EXPENSES_CSV)

        total_profit = ((df_sales['Actual Sale Price'] - get_buying_price(df_sales['Product'])) * df_sales['Quantity Sold']).sum()
        total_expenses = df_expenses['Amount'].sum()
        net = pd.DataFrame([{
            'Total Profit': total_profit,
            'Total Expenses': total_expenses,
            'Net Profit': total_profit - total_expenses
        }])
        net.to_csv(f"{DATA_DIR}/net_profit.csv", index=False)
        return send_file(f"{DATA_DIR}/net_profit.csv", as_attachment=True)

    return "Invalid type", 400

def get_buying_price(products):
    df = pd.read_csv(PRODUCTS_CSV)
    return products.map(lambda p: df[df['Product'] == p]['Buying Price'].values[0] if p in df['Product'].values else 0)

if __name__ == '__main__':
    app.run(debug=True)
