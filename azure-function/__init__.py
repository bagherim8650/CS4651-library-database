import azure.functions as func
import logging
import pyodbc
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main(mytimer: func.TimerRequest) -> None:
    logging.info('Timer trigger function started.')
    
    # Try environment variable from Azure Function settings, fallback to .env
    conn_str = os.environ.get('SQL_CONNECTION_STRING')
    
    if not conn_str:
        logging.error('SQL_CONNECTION_STRING not found in environment variables')
        return
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Call stored procedure
        cursor.execute("EXEC sp_ReleaseExpiredReservations")
        affected = cursor.fetchall()
        conn.commit()
        conn.close()
        
        logging.info(f'Processed {len(affected)} expired reservations.')
        
        for book in affected:
            logging.info(f'Released expired reservation for book_id: {book[0]}')
            
    except Exception as e:
        logging.error(f'Error processing expired reservations: {str(e)}')