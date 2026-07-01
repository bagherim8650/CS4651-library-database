from flask import send_from_directory
from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc
import os
from config import Config

app = Flask(__name__)

# Configure CORS for production
CORS(app, origins=['*'])  # Or specify your frontend URL

def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn_str = os.environ.get('SQL_CONNECTION_STRING')
        if not conn_str:
            raise ValueError("SQL_CONNECTION_STRING not set")
        return pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        print(f"Database connection error: {e}")
        return None

# ===== HEALTH CHECK =====
@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if API is running"""
    return jsonify({'status': 'healthy', 'message': 'Library API is running'})

# ===== PATRON ENDPOINTS =====
@app.route('/api/books', methods=['GET'])
def search_books():
    """Search books by genre or keyword"""
    genre = request.args.get('genre', '')
    keyword = request.args.get('keyword', '')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    query = "SELECT book_id, title, author, genre, available_copies FROM Books WHERE 1=1"
    params = []
    
    if genre:
        query += " AND genre = ?"
        params.append(genre)
    if keyword:
        query += " AND (title LIKE ? OR author LIKE ?)"
        params.append(f'%{keyword}%')
        params.append(f'%{keyword}%')
    
    cursor.execute(query, params)
    books = []
    for row in cursor.fetchall():
        books.append({
            'book_id': row[0],
            'title': row[1],
            'author': row[2],
            'genre': row[3],
            'available': row[4] > 0
        })
    
    conn.close()
    return jsonify(books)

@app.route('/api/patrons', methods=['POST'])
def create_patron():
    """Sign up for library card"""
    data = request.json
    card_number = data.get('card_number')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO Patrons (card_number, first_name, last_name, email) VALUES (?, ?, ?, ?)",
            (card_number, first_name, last_name, email)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Patron created successfully'}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@app.route('/api/patrons/<card_number>/account', methods=['GET'])
def get_patron_account(card_number):
    """View patron's own account"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT card_number, first_name, last_name, email FROM Patrons WHERE card_number = ?",
        (card_number,)
    )
    patron = cursor.fetchone()
    if not patron:
        conn.close()
        return jsonify({'error': 'Patron not found'}), 404
    
    cursor.execute(
        "SELECT b.title, c.due_date FROM Checkouts c "
        "JOIN Books b ON c.book_id = b.book_id "
        "WHERE c.patron_card_number = ? AND c.is_returned = 0",
        (card_number,)
    )
    checkouts = [{'title': row[0], 'due_date': row[1].strftime('%Y-%m-%d')} for row in cursor.fetchall()]
    
    cursor.execute(
        "SELECT b.title, r.queue_position FROM Reservations r "
        "JOIN Books b ON r.book_id = b.book_id "
        "WHERE r.patron_card_number = ? AND r.is_active = 1",
        (card_number,)
    )
    reservations = [{'title': row[0], 'queue_position': row[1]} for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'patron': {
            'card_number': patron[0],
            'first_name': patron[1],
            'last_name': patron[2],
            'email': patron[3]
        },
        'checkouts': checkouts,
        'reservations': reservations
    })

@app.route('/api/reservations', methods=['POST'])
def make_reservation():
    """Patron reserves an unavailable book"""
    data = request.json
    book_id = data.get('book_id')
    patron_card = data.get('patron_card')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT available_copies FROM Books WHERE book_id = ?", (book_id,))
    available = cursor.fetchone()
    if not available or available[0] > 0:
        conn.close()
        return jsonify({'error': 'Book is available, no reservation needed'}), 400
    
    cursor.execute(
        "SELECT COUNT(*) + 1 FROM Reservations WHERE book_id = ? AND is_active = 1",
        (book_id,)
    )
    queue_position = cursor.fetchone()[0]
    
    cursor.execute(
        "INSERT INTO Reservations (book_id, patron_card_number, queue_position) VALUES (?, ?, ?)",
        (book_id, patron_card, queue_position)
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': 'Reservation created',
        'queue_position': queue_position
    }), 201

# ===== LIBRARIAN ENDPOINTS =====
@app.route('/api/librarians/books', methods=['POST'])
def add_book():
    """Librarian adds a book"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO Books (title, author, genre, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)",
        (data['title'], data['author'], data['genre'], data['total_copies'], data['total_copies'])
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book added'}), 201

@app.route('/api/librarians/books/<book_id>', methods=['DELETE'])
def remove_book(book_id):
    """Librarian removes a book"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Books WHERE book_id = ?", (book_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book removed'})

@app.route('/api/librarians/checkout', methods=['POST'])
def checkout_book():
    """Librarian checks out a book to a patron"""
    data = request.json
    book_id = data.get('book_id')
    patron_card = data.get('patron_card')
    librarian_id = data.get('librarian_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "{CALL sp_CheckoutBook(?, ?, ?, ?)}",
            (book_id, patron_card, librarian_id, '')
        )
        result = cursor.fetchval()
        conn.commit()
        conn.close()
        return jsonify({'message': result})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@app.route('/api/librarians/return', methods=['POST'])
def return_book():
    """Librarian processes a book return"""
    data = request.json
    book_id = data.get('book_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("{CALL sp_ReturnBook(?, ?)}", (book_id, ''))
        result = cursor.fetchval()
        conn.commit()
        conn.close()
        return jsonify({'message': result})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@app.route('/api/librarians/catalog', methods=['GET'])
def full_catalog():
    """Librarian views full catalog with patron info"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vw_LibrarianFullCatalog")
    books = []
    for row in cursor.fetchall():
        books.append({
            'book_id': row[0],
            'title': row[1],
            'author': row[2],
            'genre': row[3],
            'available_copies': row[4],
            'checked_out_to': row[5],
            'next_reserved_by': row[6]
        })
    
    conn.close()
    return jsonify(books)

# ===== ROOT ENDPOINT / FRONTEND =====
@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')

# ===== FOR AZURE =====
# Azure App Service uses Gunicorn by default
# This allows local testing as well
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)