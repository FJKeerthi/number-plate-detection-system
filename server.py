"""
Simple Web Server for License Plate Detection
Receives plate detections with images and stores them in SQLite database
"""

from flask import Flask, request, jsonify, render_template
import sqlite3
import base64
from datetime import datetime
import os

app = Flask(__name__)

# Database setup
DB_PATH = 'plates.db'

def init_db():
    """Initialize the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT NOT NULL,
            detection_count INTEGER,
            total_detections INTEGER,
            confidence REAL,
            image_data TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_PATH}")

# Initialize database on startup
init_db()

@app.route('/')
def index():
    """Home page - shows recent detections"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute('SELECT COUNT(*) FROM detections')
    total_count = cursor.fetchone()[0]
    
    # Get unique plates
    cursor.execute('SELECT COUNT(DISTINCT plate_number) FROM detections')
    unique_plates = cursor.fetchone()[0]
    
    # Get recent detections
    cursor.execute('''
        SELECT id, plate_number, detection_count, total_detections, 
               confidence, timestamp 
        FROM detections 
        ORDER BY timestamp DESC 
        LIMIT 100
    ''')
    
    detections = cursor.fetchall()
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>License Plate Detection System</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .header {
                background: white;
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                margin-bottom: 30px;
                text-align: center;
            }
            
            .header h1 {
                color: #333;
                font-size: 36px;
                margin-bottom: 10px;
            }
            
            .header p {
                color: #666;
                font-size: 16px;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                text-align: center;
                transition: transform 0.3s;
            }
            
            .stat-card:hover {
                transform: translateY(-5px);
            }
            
            .stat-number {
                font-size: 48px;
                font-weight: bold;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .stat-label {
                color: #666;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-top: 5px;
            }
            
            .controls {
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                align-items: center;
            }
            
            .search-box {
                flex: 1;
                min-width: 250px;
            }
            
            .search-box input {
                width: 100%;
                padding: 12px 20px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            
            .search-box input:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .refresh-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: transform 0.2s;
            }
            
            .refresh-btn:hover {
                transform: scale(1.05);
            }
            
            .auto-refresh {
                display: flex;
                align-items: center;
                gap: 10px;
                color: #666;
            }
            
            .detection-grid {
                display: grid;
                gap: 20px;
            }
            
            .detection-card { 
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                display: flex;
                align-items: center;
                justify-content: space-between;
                transition: transform 0.3s, box-shadow 0.3s;
                cursor: pointer;
            }
            
            .detection-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }
            
            .detection-info {
                flex: 1;
            }
            
            .plate-number { 
                font-size: 32px; 
                font-weight: bold;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 10px;
                font-family: 'Courier New', monospace;
                letter-spacing: 2px;
            }
            
            .detection-stats {
                display: flex;
                gap: 20px;
                margin-bottom: 8px;
            }
            
            .stat-item {
                display: flex;
                align-items: center;
                gap: 5px;
                color: #666;
                font-size: 14px;
            }
            
            .stat-icon {
                font-size: 18px;
            }
            
            .timestamp { 
                color: #999;
                font-size: 13px;
            }
            
            .view-btn {
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                text-decoration: none;
                font-weight: 600;
                transition: transform 0.2s;
                display: inline-block;
            }
            
            .view-btn:hover {
                transform: scale(1.05);
            }
            
            .no-results {
                text-align: center;
                padding: 60px 20px;
                background: white;
                border-radius: 12px;
                color: #999;
            }
            
            .no-results-icon {
                font-size: 64px;
                margin-bottom: 20px;
            }
            
            @media (max-width: 768px) {
                .detection-card {
                    flex-direction: column;
                    text-align: center;
                }
                
                .detection-stats {
                    justify-content: center;
                }
                
                .view-btn {
                    margin-top: 15px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚗 License Plate Detection System</h1>
                <p>Real-time vehicle monitoring and tracking</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">''' + str(total_count) + '''</div>
                    <div class="stat-label">Total Detections</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">''' + str(unique_plates) + '''</div>
                    <div class="stat-label">Unique Plates</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="live-count">''' + str(len(detections)) + '''</div>
                    <div class="stat-label">Showing</div>
                </div>
            </div>
            
            <div class="controls">
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="🔍 Search plate number..." onkeyup="filterDetections()">
                </div>
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
                <div class="auto-refresh">
                    <input type="checkbox" id="autoRefresh" onchange="toggleAutoRefresh()">
                    <label for="autoRefresh">Auto-refresh (10s)</label>
                </div>
            </div>
            
            <div class="detection-grid" id="detectionGrid">
    '''
    
    if detections:
        for detection in detections:
            det_id, plate, count, total, conf, timestamp = detection
            accuracy = (count / total * 100) if total > 0 else 0
            html += f'''
                <div class="detection-card" data-plate="{plate}" onclick="window.location.href='/detection/{det_id}'">
                    <div class="detection-info">
                        <div class="plate-number">{plate}</div>
                        <div class="detection-stats">
                            <div class="stat-item">
                                <span class="stat-icon">✓</span>
                                <span>{count}/{total} detections</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-icon">📊</span>
                                <span>{accuracy:.0f}% accuracy</span>
                            </div>
                        </div>
                        <div class="timestamp">⏱️ {timestamp}</div>
                    </div>
                    <a href="/detection/{det_id}" class="view-btn" onclick="event.stopPropagation()">View Details</a>
                </div>
            '''
    else:
        html += '''
                <div class="no-results">
                    <div class="no-results-icon">📭</div>
                    <h2>No Detections Yet</h2>
                    <p>Start the detection script to see plates here</p>
                </div>
        '''
    
    html += '''
            </div>
        </div>
        
        <script>
            let autoRefreshInterval = null;
            
            function filterDetections() {
                const input = document.getElementById('searchInput');
                const filter = input.value.toUpperCase();
                const cards = document.querySelectorAll('.detection-card');
                let visibleCount = 0;
                
                cards.forEach(card => {
                    const plate = card.getAttribute('data-plate');
                    if (plate.toUpperCase().indexOf(filter) > -1) {
                        card.style.display = '';
                        visibleCount++;
                    } else {
                        card.style.display = 'none';
                    }
                });
                
                document.getElementById('live-count').textContent = visibleCount;
            }
            
            function toggleAutoRefresh() {
                const checkbox = document.getElementById('autoRefresh');
                
                if (checkbox.checked) {
                    autoRefreshInterval = setInterval(() => {
                        location.reload();
                    }, 10000); // 10 seconds
                } else {
                    if (autoRefreshInterval) {
                        clearInterval(autoRefreshInterval);
                        autoRefreshInterval = null;
                    }
                }
            }
            
            // Save auto-refresh state
            document.addEventListener('DOMContentLoaded', () => {
                const saved = localStorage.getItem('autoRefresh');
                if (saved === 'true') {
                    document.getElementById('autoRefresh').checked = true;
                    toggleAutoRefresh();
                }
            });
            
            document.getElementById('autoRefresh').addEventListener('change', (e) => {
                localStorage.setItem('autoRefresh', e.target.checked);
            });
        </script>
    </body>
    </html>
    '''
    
    return html

@app.route('/detection/<int:det_id>')
def view_detection(det_id):
    """View a specific detection with image"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT plate_number, detection_count, total_detections, 
               confidence, image_data, timestamp 
        FROM detections 
        WHERE id = ?
    ''', (det_id,))
    
    detection = cursor.fetchone()
    conn.close()
    
    if not detection:
        return "Detection not found", 404
    
    plate, count, total, conf, image_data, timestamp = detection
    accuracy = (count / total * 100) if total > 0 else 0
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Detection Details - {plate}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            
            .container {{ 
                max-width: 900px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }}
            
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
                flex-wrap: wrap;
                gap: 15px;
            }}
            
            .back-btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
                transition: transform 0.2s;
            }}
            
            .back-btn:hover {{
                transform: translateX(-5px);
            }}
            
            .plate-number {{ 
                font-size: 48px;
                font-weight: bold;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-align: center;
                margin: 20px 0;
                font-family: 'Courier New', monospace;
                letter-spacing: 3px;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            
            .stat-box {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                border-radius: 12px;
                text-align: center;
            }}
            
            .stat-value {{
                font-size: 32px;
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }}
            
            .stat-label {{
                color: #666;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .image-section {{
                margin-top: 40px;
            }}
            
            .section-title {{
                font-size: 24px;
                color: #333;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .image-container {{
                position: relative;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 8px 20px rgba(0,0,0,0.15);
                background: #000;
            }}
            
            .image-container img {{
                width: 100%;
                display: block;
                transition: transform 0.3s;
            }}
            
            .image-container:hover img {{
                transform: scale(1.05);
            }}
            
            .download-btn {{
                background: #4CAF50;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
                margin-top: 20px;
                transition: transform 0.2s;
            }}
            
            .download-btn:hover {{
                transform: scale(1.05);
            }}
            
            .timestamp-badge {{
                display: inline-block;
                background: #f0f0f0;
                padding: 10px 20px;
                border-radius: 20px;
                color: #666;
                font-size: 14px;
                margin: 20px 0;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    padding: 20px;
                }}
                
                .plate-number {{
                    font-size: 32px;
                }}
                
                .stat-value {{
                    font-size: 24px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/" class="back-btn">
                    <span>←</span>
                    <span>Back to List</span>
                </a>
            </div>
            
            <div class="plate-number">{plate}</div>
            
            <div class="timestamp-badge">
                🕒 Detected on {timestamp}
            </div>
            
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value">{count}</div>
                    <div class="stat-label">Successful Detections</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">Total Attempts</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{accuracy:.0f}%</div>
                    <div class="stat-label">Accuracy Rate</div>
                </div>
            </div>
            
            <div class="image-section">
                <div class="section-title">
                    <span>📸</span>
                    <span>Captured Image</span>
                </div>
                <div class="image-container">
                    <img src="data:image/jpeg;base64,{image_data}" alt="Plate Image" id="plateImage">
                </div>
                <a href="data:image/jpeg;base64,{image_data}" download="{plate}_{timestamp}.jpg" class="download-btn">
                    <span>⬇️</span>
                    <span>Download Image</span>
                </a>
            </div>
        </div>
        
        <script>
            // Allow clicking image to view fullscreen
            document.getElementById('plateImage').addEventListener('click', function() {{
                if (this.requestFullscreen) {{
                    this.requestFullscreen();
                }} else if (this.webkitRequestFullscreen) {{
                    this.webkitRequestFullscreen();
                }} else if (this.msRequestFullscreen) {{
                    this.msRequestFullscreen();
                }}
            }});
        </script>
    </body>
    </html>
    '''
    
    return html

@app.route('/api/detect', methods=['POST'])
def receive_detection():
    """API endpoint to receive plate detections"""
    try:
        data = request.json
        
        plate_number = data.get('plate_number')
        detection_count = data.get('detection_count')
        total_detections = data.get('total_detections')
        image_base64 = data.get('image')
        
        # Store in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO detections 
            (plate_number, detection_count, total_detections, image_data)
            VALUES (?, ?, ?, ?)
        ''', (plate_number, detection_count, total_detections, image_base64))
        
        conn.commit()
        detection_id = cursor.lastrowid
        conn.close()
        
        print(f"✅ Stored detection: {plate_number} (ID: {detection_id})")
        
        return jsonify({
            'success': True,
            'message': 'Detection stored successfully',
            'id': detection_id
        }), 200
        
    except Exception as e:
        print(f"❌ Error storing detection: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/detections', methods=['GET'])
def get_detections():
    """API endpoint to get all detections"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, plate_number, detection_count, total_detections, timestamp
        FROM detections 
        ORDER BY timestamp DESC
    ''')
    
    detections = cursor.fetchall()
    conn.close()
    
    results = []
    for det in detections:
        results.append({
            'id': det[0],
            'plate_number': det[1],
            'detection_count': det[2],
            'total_detections': det[3],
            'timestamp': det[4]
        })
    
    return jsonify(results)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting License Plate Detection Server")
    print("="*60)
    print(f"📊 Database: {os.path.abspath(DB_PATH)}")
    print(f"🌐 Web Interface: http://localhost:5000")
    print(f"📡 API Endpoint: http://localhost:5000/api/detect")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
