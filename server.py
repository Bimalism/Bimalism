#!/usr/bin/env python3
"""
BIMALISM SERVER with Simplified Hamburger Menu
Features:
1. Hamburger menu in top-right corner
2. Opens sidebar with ONLY requested items
3. Tracks coins and study time on server
4. Clean header without original navigation
"""

import http.server
import socketserver
import webbrowser
import os
import json
import time
from urllib.parse import urlparse, parse_qs
import mimetypes
from datetime import datetime

PORT = 8080
DATA_FILE = 'bimalism_data.json'

# Initialize MIME types
mimetypes.init()
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

class BimalismServer(http.server.SimpleHTTPRequestHandler):
    """Server handler with simplified hamburger menu"""
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        print(f"📱 Request: {path}")
        
        # API endpoints
        if path == '/api/get_coins':
            self.get_coins_data()
            return
        elif path == '/api/get_timer':
            self.get_timer_data()
            return
        elif path.startswith('/api/update_coins'):
            self.update_coins()
            return
        
        # Serve HTML pages with menu
        if path == '/' or path == '/index.html':
            self.serve_homepage()
        elif path in ['/neet', '/neet.html']:
            self.serve_page_with_menu('neet.html', 'NEET Preparation')
        elif path in ['/jee', '/jee.html']:
            self.serve_page_with_menu('jee.html', 'JEE Preparation')
        elif path in ['/game', '/g.html']:
            self.serve_page_with_menu('g.html', 'Educational Games')
        elif path in ['/settings', '/settings.html']:
            self.serve_page_with_menu('settings.html', 'Settings')
        elif path in ['/tips', '/tips.html']:
            self.serve_page_with_menu('tips.html', 'Study Tips')
        elif path in ['/table', '/table.html']:
            self.serve_page_with_menu('table.html', 'Study Resources')
        elif path in ['/calculator', '/calculator.html']:
            self.serve_page_with_menu('calculator.html', 'Calculator')
        elif path in ['/bio-data-pop-up', '/bio-data-pop-up.html']:
            self.serve_page_with_menu('bio-data-pop-up.html', 'Student Profile')
        elif path in ['/registration', '/registration.html']:
            self.serve_registration_page()
        elif path == '/h.html':
            self.serve_page_with_menu('h.html', 'हिंदी')
        elif path == '/t.html':
            self.serve_page_with_menu('t.html', 'தமிழ்')
        else:
            # Try to serve static files
            self.serve_static_file(path)
    
    def serve_homepage(self):
        """Serve homepage with clean header and hamburger menu"""
        try:
            # Load data
            data = self.load_data()
            user_coins = data.get('coins', 0)
            study_time = data.get('study_time', 0)
            
            # Read original HTML
            with open('index.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Find header and replace with clean version
            if '<header>' in html_content and '</header>' in html_content:
                header_start = html_content.find('<header>')
                header_end = html_content.find('</header>') + 9
                header = html_content[header_start:header_end]
                
                # Replace the entire header with our clean version
                clean_header = self.generate_clean_header()
                html_content = html_content.replace(header, clean_header)
            else:
                # If no header found, add clean header at top
                clean_header = self.generate_clean_header()
                if '<body>' in html_content:
                    html_content = html_content.replace('<body>', '<body>' + clean_header)
            
            # Add sidebar menu HTML (always at end of body)
            sidebar_html = self.generate_sidebar_menu(user_coins)
            
            # Add JavaScript for menu functionality
            js_injection = f'''
            <!-- Menu JavaScript -->
            {sidebar_html}
            <script>
            // Hamburger Menu Toggle
            const hamburgerBtn = document.getElementById('hamburgerBtn');
            const sidebarMenu = document.getElementById('sidebarMenu');
            const overlay = document.getElementById('overlay');
            const closeMenuBtn = document.getElementById('closeMenuBtn');
            
            function openMenu() {{
                sidebarMenu.classList.add('active');
                overlay.classList.add('active');
                document.body.style.overflow = 'hidden';
            }}
            
            function closeMenu() {{
                sidebarMenu.classList.remove('active');
                overlay.classList.remove('active');
                document.body.style.overflow = 'auto';
            }}
            
            if (hamburgerBtn) {{
                hamburgerBtn.addEventListener('click', openMenu);
            }}
            
            if (closeMenuBtn) {{
                closeMenuBtn.addEventListener('click', closeMenu);
            }}
            
            if (overlay) {{
                overlay.addEventListener('click', closeMenu);
            }}
            
            // Close menu when clicking on menu items
            const menuItems = document.querySelectorAll('.menu-item');
            menuItems.forEach(item => {{
                item.addEventListener('click', function(e) {{
                    // Only close for internal links
                    if (this.getAttribute('href') && !this.getAttribute('href').startsWith('#')) {{
                        closeMenu();
                    }}
                }});
            }});
            
            // Close menu with Escape key
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') closeMenu();
            }});
            
            // Load coin data from server
            function loadCoinData() {{
                fetch('/api/get_coins')
                    .then(response => response.json())
                    .then(data => {{
                        // Update coin counter in menu
                        const coinBadge = document.querySelector('.menu-badge');
                        if (coinBadge) {{
                            coinBadge.textContent = data.coins + ' coins';
                        }}
                        
                        // Update coin display in menu header
                        const coinDisplay = document.querySelector('.user-coins');
                        if (coinDisplay) {{
                            coinDisplay.textContent = data.coins + ' Coins';
                        }}
                    }})
                    .catch(error => console.error('Error loading coin data:', error));
            }}
            
            // Load every 30 seconds
            setInterval(loadCoinData, 30000);
            
            // Initial load
            loadCoinData();
            </script>
            '''
            
            # Inject JavaScript before closing body tag
            if '</body>' in html_content:
                html_content = html_content.replace('</body>', js_injection + '\n</body>')
            else:
                html_content += js_injection
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            print(f"Error serving homepage: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def serve_registration_page(self):
        """Serve registration page with timer and coin tracking"""
        try:
            # Load data
            data = self.load_data()
            user_coins = data.get('coins', 0)
            study_time = data.get('study_time', 0)
            study_hours = study_time // 3600
            study_minutes = (study_time % 3600) // 60
            
            # Create enhanced registration page
            registration_html = self.generate_registration_page(user_coins, study_hours, study_minutes)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(registration_html.encode('utf-8'))
            
        except Exception as e:
            print(f"Error serving registration page: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def serve_page_with_menu(self, filename, title):
        """Serve any page with menu navigation"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Wrap in app layout with menu
                wrapped_content = self.wrap_in_app_layout(html_content, title)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(wrapped_content.encode('utf-8'))
            else:
                # Create default page
                default_content = f'''
                <div style="padding: 2rem; text-align: center;">
                    <h1 style="color: #2563eb;">{title}</h1>
                    <p>This page is under construction.</p>
                    <a href="/" style="display: inline-block; margin-top: 1rem; padding: 0.8rem 1.5rem; background: #2563eb; color: white; border-radius: 25px; text-decoration: none;">
                        ← Back to Home
                    </a>
                </div>
                '''
                wrapped_content = self.wrap_in_app_layout(default_content, title)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(wrapped_content.encode('utf-8'))
                
        except Exception as e:
            print(f"Error serving {filename}: {e}")
            self.send_error(404, f"Page not found: {filename}")
    
    def serve_static_file(self, path):
        """Serve static files"""
        try:
            filepath = '.' + path
            if not os.path.exists(filepath):
                self.send_error(404, "File not found")
                return
            
            # Determine MIME type
            if path.endswith('.css'):
                mimetype = 'text/css'
            elif path.endswith('.js'):
                mimetype = 'application/javascript'
            elif path.endswith('.png'):
                mimetype = 'image/png'
            elif path.endswith('.jpg') or path.endswith('.jpeg'):
                mimetype = 'image/jpeg'
            elif path.endswith('.html'):
                mimetype = 'text/html'
            else:
                mimetype = 'text/plain'
            
            with open(filepath, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', mimetype)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_error(404, f"File not found: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests for updating coins"""
        if self.path.startswith('/api/update_coins'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Parse the data
                data = json.loads(post_data.decode('utf-8'))
                
                # Load existing data
                server_data = self.load_data()
                
                if data.get('action') == 'add_coin':
                    # Add coin from study time
                    study_seconds = data.get('study_seconds', 0)
                    new_coins = study_seconds // 7200  # 2 hours = 7200 seconds = 1 coin
                    
                    # Update server data
                    server_data['coins'] = server_data.get('coins', 0) + new_coins
                    server_data['study_time'] = server_data.get('study_time', 0) + study_seconds
                    server_data['last_updated'] = datetime.now().isoformat()
                    
                    # Save data
                    self.save_data(server_data)
                    
                    response = {
                        'success': True,
                        'coins': server_data['coins'],
                        'study_time': server_data['study_time'],
                        'coins_added': new_coins
                    }
                    
                elif data.get('action') == 'update_timer':
                    # Update study time
                    study_seconds = data.get('study_seconds', 0)
                    server_data['study_time'] = server_data.get('study_time', 0) + study_seconds
                    server_data['last_updated'] = datetime.now().isoformat()
                    
                    # Recalculate coins
                    server_data['coins'] = server_data['study_time'] // 7200
                    
                    # Save data
                    self.save_data(server_data)
                    
                    response = {
                        'success': True,
                        'coins': server_data['coins'],
                        'study_time': server_data['study_time']
                    }
                    
                else:
                    response = {'success': False, 'error': 'Unknown action'}
                    
            except Exception as e:
                response = {'success': False, 'error': str(e)}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_error(404, "Not Found")
    
    def get_coins_data(self):
        """API: Get coins data"""
        data = self.load_data()
        response = {
            'coins': data.get('coins', 0),
            'study_time': data.get('study_time', 0),
            'last_updated': data.get('last_updated', '')
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def get_timer_data(self):
        """API: Get timer data"""
        data = self.load_data()
        response = {
            'study_time': data.get('study_time', 0),
            'coins': data.get('coins', 0)
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def update_coins(self):
        """API: Update coins via GET (for testing)"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        try:
            data = self.load_data()
            
            if 'add' in query_params:
                coins_to_add = int(query_params['add'][0])
                data['coins'] = data.get('coins', 0) + coins_to_add
                data['last_updated'] = datetime.now().isoformat()
                self.save_data(data)
                
                response = {
                    'success': True,
                    'coins': data['coins'],
                    'added': coins_to_add
                }
            else:
                response = {'success': False, 'error': 'No add parameter'}
                
        except Exception as e:
            response = {'success': False, 'error': str(e)}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def load_data(self):
        """Load data from JSON file"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'coins': 0, 'study_time': 0, 'last_updated': datetime.now().isoformat()}
    
    def save_data(self, data):
        """Save data to JSON file"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def generate_clean_header(self):
        """Generate clean header with only logo and hamburger menu"""
        return '''<header>
    <div class="container">
        <nav>
            <div class="logo">
                <span>Bimalism</span>
            </div>
            
            <!-- Hamburger Menu Button (Top-Right) -->
            <div class="hamburger-menu-container">
                <button class="hamburger-btn" id="hamburgerBtn">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
            </div>
        </nav>
    </div>
    
    <!-- Hamburger Menu Styles -->
    <style>
        /* Header Styles */
        header {
            background: linear-gradient(135deg, #2563eb, #4f46e5);
            color: white;
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1.5rem;
        }
        
        nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 1.8rem;
            font-weight: 700;
            color: white;
        }
        
        .logo span {
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        /* Hamburger Menu Container */
        .hamburger-menu-container {
            display: flex;
            align-items: center;
        }
        
        /* Hamburger Button */
        .hamburger-btn {
            background: rgba(255, 255, 255, 0.15);
            border: none;
            width: 44px;
            height: 44px;
            border-radius: 12px;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 8px;
            position: relative;
            z-index: 1001;
            transition: all 0.3s ease;
        }
        
        .hamburger-btn:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: rotate(90deg);
        }
        
        .hamburger-btn span {
            display: block;
            width: 22px;
            height: 2px;
            background: white;
            border-radius: 1px;
            margin: 2px 0;
            transition: all 0.3s ease;
        }
        
        .hamburger-btn:hover span {
            background: #fbbf24;
        }
        
        @media (max-width: 768px) {
            .hamburger-btn {
                width: 40px;
                height: 40px;
            }
            
            .logo {
                font-size: 1.5rem;
            }
        }
    </style>
</header>'''
    
    def generate_sidebar_menu(self, user_coins=0):
        """Generate sidebar menu with ONLY requested items"""
        return f'''
        <!-- Sidebar Menu (Left Side) -->
        <div class="sidebar-menu" id="sidebarMenu">
            <div class="sidebar-header">
                <div class="user-profile">
                    <div class="user-avatar">
                        <i class="fas fa-user-graduate"></i>
                    </div>
                    <div class="user-info">
                        <h3>Bimalism</h3>
                        <p class="user-coins">{user_coins} Coins</p>
                        <p>Education Portal</p>
                    </div>
                    <button class="close-menu-btn" id="closeMenuBtn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            
            <div class="sidebar-content">
                <!-- ONLY REQUESTED ITEMS -->
                <div class="menu-section">
                    <h4>Navigation</h4>
                    
                    <a href="/" class="menu-item">
                        <i class="fas fa-home"></i>
                        <span>Home</span>
                    </a>
                    
                    <a href="/bio-data-pop-up" class="menu-item">
                        <i class="fas fa-user-circle"></i>
                        <span>Bio Data</span>
                    </a>
                    
                    <a href="#features" class="menu-item">
                        <i class="fas fa-star"></i>
                        <span>Features</span>
                    </a>
                    
                    <a href="/neet" class="menu-item">
                        <i class="fas fa-stethoscope"></i>
                        <span>NEET</span>
                    </a>
                    
                    <a href="/jee" class="menu-item">
                        <i class="fas fa-calculator"></i>
                        <span>JEE</span>
                    </a>
                    
                    <a href="#results" class="menu-item">
                        <i class="fas fa-chart-line"></i>
                        <span>Results</span>
                    </a>
                    
                    <a href="#testimonials" class="menu-item">
                        <i class="fas fa-comments"></i>
                        <span>Testimonials</span>
                    </a>
                    
                    <a href="/game" class="menu-item">
                        <i class="fas fa-gamepad"></i>
                        <span>Game</span>
                    </a>
                </div>
                
                <!-- Additional Useful Pages -->
                <div class="menu-section">
                    <h4>Study Tools</h4>
                    
                    <a href="/registration" class="menu-item">
                        <i class="fas fa-trophy"></i>
                        <span>Study Challenge</span>
                        <span class="menu-badge">{user_coins} coins</span>
                    </a>
                    
                    <a href="/table" class="menu-item">
                        <i class="fas fa-book"></i>
                        <span>Study Resources</span>
                    </a>
                    
                    <a href="/calculator" class="menu-item">
                        <i class="fas fa-calculator"></i>
                        <span>Calculator</span>
                    </a>
                </div>
                
                <!-- App Settings -->
                <div class="menu-section">
                    <h4>Settings</h4>
                    
                    <a href="/settings" class="menu-item">
                        <i class="fas fa-cog"></i>
                        <span>Settings</span>
                    </a>
                    
                    <a href="#download-section" class="menu-item">
                        <i class="fas fa-download"></i>
                        <span>Download App</span>
                    </a>
                </div>
            </div>
            
            <div class="sidebar-footer">
                <p>Bimalism Education Platform</p>
                <p>© 2024 All rights reserved</p>
            </div>
        </div>
        
        <!-- Overlay -->
        <div class="overlay" id="overlay"></div>
        
        <!-- Sidebar Menu Styles -->
        <style>
            /* Sidebar Menu */
            .sidebar-menu {{
                position: fixed;
                top: 0;
                left: -350px;
                width: 320px;
                height: 100vh;
                background: white;
                box-shadow: 2px 0 15px rgba(0, 0, 0, 0.1);
                z-index: 1000;
                transition: left 0.3s ease;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }}
            
            .sidebar-menu.active {{
                left: 0;
            }}
            
            /* Overlay */
            .overlay {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 999;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
            }}
            
            .overlay.active {{
                opacity: 1;
                visibility: visible;
            }}
            
            /* Sidebar Header */
            .sidebar-header {{
                background: linear-gradient(135deg, #2563eb, #4f46e5);
                color: white;
                padding: 1.5rem;
                border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            }}
            
            .user-profile {{
                display: flex;
                align-items: center;
                gap: 12px;
                position: relative;
            }}
            
            .user-avatar {{
                width: 50px;
                height: 50px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                flex-shrink: 0;
            }}
            
            .user-info {{
                flex: 1;
            }}
            
            .user-info h3 {{
                margin: 0;
                font-size: 1.3rem;
                font-weight: 700;
                line-height: 1.3;
            }}
            
            .user-info p {{
                margin: 2px 0;
                font-size: 0.85rem;
                opacity: 0.9;
                line-height: 1.2;
            }}
            
            .user-coins {{
                color: #fbbf24;
                font-weight: bold;
                font-size: 0.9rem;
            }}
            
            .close-menu-btn {{
                position: absolute;
                top: -10px;
                right: -10px;
                background: rgba(255, 255, 255, 0.2);
                border: none;
                width: 36px;
                height: 36px;
                border-radius: 50%;
                color: white;
                font-size: 1.2rem;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                flex-shrink: 0;
            }}
            
            .close-menu-btn:hover {{
                background: rgba(255, 255, 255, 0.3);
                transform: rotate(90deg);
            }}
            
            /* Sidebar Content */
            .sidebar-content {{
                flex: 1;
                overflow-y: auto;
                padding: 1.5rem 0;
            }}
            
            .menu-section {{
                padding: 0 1.5rem;
                margin-bottom: 1.8rem;
            }}
            
            .menu-section:last-child {{
                margin-bottom: 0;
            }}
            
            .menu-section h4 {{
                color: #666;
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 1rem;
                padding-bottom: 0.5rem;
                border-bottom: 1px solid #eee;
                font-weight: 600;
            }}
            
            .menu-item {{
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 0.9rem 1rem;
                text-decoration: none;
                color: #333;
                border-radius: 8px;
                margin-bottom: 0.4rem;
                transition: all 0.2s ease;
                position: relative;
            }}
            
            .menu-item:hover {{
                background: #f3f4f6;
                color: #2563eb;
                transform: translateX(5px);
            }}
            
            .menu-item i {{
                width: 20px;
                text-align: center;
                font-size: 1.1rem;
                color: #666;
                flex-shrink: 0;
            }}
            
            .menu-item:hover i {{
                color: #2563eb;
            }}
            
            .menu-item span {{
                flex: 1;
                font-size: 0.95rem;
                font-weight: 500;
            }}
            
            .menu-badge {{
                margin-left: auto;
                background: #f59e0b;
                color: white;
                padding: 3px 9px;
                border-radius: 10px;
                font-size: 0.75rem;
                font-weight: 600;
                white-space: nowrap;
            }}
            
            /* Sidebar Footer */
            .sidebar-footer {{
                padding: 1.2rem 1.5rem;
                background: #f9fafb;
                border-top: 1px solid #e5e7eb;
                text-align: center;
                flex-shrink: 0;
            }}
            
            .sidebar-footer p {{
                margin: 0.3rem 0;
                font-size: 0.85rem;
                color: #666;
                line-height: 1.3;
            }}
            
            /* Scrollbar Styling */
            .sidebar-content::-webkit-scrollbar {{
                width: 4px;
            }}
            
            .sidebar-content::-webkit-scrollbar-track {{
                background: #f1f1f1;
            }}
            
            .sidebar-content::-webkit-scrollbar-thumb {{
                background: #c1c1c1;
                border-radius: 2px;
            }}
            
            .sidebar-content::-webkit-scrollbar-thumb:hover {{
                background: #a1a1a1;
            }}
            
            /* Responsive */
            @media (max-width: 768px) {{
                .sidebar-menu {{
                    width: 280px;
                    left: -280px;
                }}
                
                .menu-section {{
                    padding: 0 1rem;
                }}
                
                .menu-item {{
                    padding: 0.8rem;
                }}
            }}
            
            @media (max-width: 480px) {{
                .sidebar-menu {{
                    width: 100%;
                    left: -100%;
                }}
            }}
        </style>
        '''
    
    def generate_registration_page(self, coins, study_hours, study_minutes):
        """Generate enhanced registration page with server-side coin tracking"""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Study Challenge - Bimalism</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap">
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Poppins', sans-serif;
        }}
        
        body {{
            background: #f9fafb;
            color: #1f2937;
            min-height: 100vh;
        }}
        
        .app-container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
            box-shadow: 0 0 30px rgba(0, 0, 0, 0.1);
        }}
        
        .app-header {{
            background: linear-gradient(135deg, #2563eb, #4f46e5);
            color: white;
            padding: 1.2rem 1.5rem;
            display: flex;
            align-items: center;
            gap: 12px;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        
        .back-button {{
            background: rgba(255, 255, 255, 0.15);
            border: none;
            width: 44px;
            height: 44px;
            border-radius: 12px;
            color: white;
            font-size: 1.2rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            text-decoration: none;
        }}
        
        .back-button:hover {{
            background: rgba(255, 255, 255, 0.25);
            transform: translateX(-3px);
        }}
        
        .app-title {{
            font-size: 1.5rem;
            font-weight: 700;
        }}
        
        .page-content {{
            padding: 2rem 1.5rem;
        }}
        
        /* Coin Dashboard */
        .coin-dashboard {{
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            color: white;
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 20px rgba(245, 158, 11, 0.3);
        }}
        
        .coin-stats {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }}
        
        .coin-info h3 {{
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
            opacity: 0.9;
        }}
        
        .coin-value {{
            font-size: 3rem;
            font-weight: 700;
            line-height: 1;
        }}
        
        .coin-icon {{
            font-size: 4rem;
            opacity: 0.8;
        }}
        
        .coin-progress {{
            margin-top: 1.5rem;
        }}
        
        .progress-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            opacity: 0.9;
        }}
        
        .progress-bar {{
            height: 10px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: white;
            width: {(coins/30)*100}%;
            border-radius: 5px;
            transition: width 0.5s ease;
        }}
        
        /* Timer Section */
        .timer-section {{
            background: linear-gradient(135deg, #1e40af, #1e3a8a);
            color: white;
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            text-align: center;
        }}
        
        .timer-display {{
            font-size: 3.5rem;
            font-family: monospace;
            margin: 1rem 0;
            font-weight: bold;
            letter-spacing: 3px;
        }}
        
        .timer-controls {{
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 1.5rem;
        }}
        
        .timer-btn {{
            padding: 0.8rem 1.5rem;
            border: none;
            border-radius: 50px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
        }}
        
        .btn-start {{
            background: #10b981;
            color: white;
        }}
        
        .btn-pause {{
            background: #f59e0b;
            color: white;
        }}
        
        .btn-reset {{
            background: #ef4444;
            color: white;
        }}
        
        .timer-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }}
        
        .study-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }}
        
        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #2563eb;
            margin-bottom: 0.5rem;
        }}
        
        .stat-label {{
            color: #6b7280;
            font-size: 0.9rem;
        }}
        
        /* Server Status */
        .server-status {{
            background: #f3f4f6;
            padding: 1rem;
            border-radius: 10px;
            margin-top: 2rem;
            text-align: center;
            font-size: 0.9rem;
            color: #4b5563;
        }}
        
        .status-connected {{
            color: #10b981;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <header class="app-header">
            <a href="/" class="back-button">
                <i class="fas fa-arrow-left"></i>
            </a>
            <div class="app-title">Study Challenge</div>
        </header>
        
        <main class="page-content">
            <!-- Coin Dashboard -->
            <div class="coin-dashboard">
                <div class="coin-stats">
                    <div class="coin-info">
                        <h3>Study Challenge Progress</h3>
                        <div class="coin-value" id="coinValue">{coins}</div>
                        <p>Coins Earned • {study_hours}h {study_minutes}m studied</p>
                    </div>
                    <div class="coin-icon">
                        <i class="fas fa-coins"></i>
                    </div>
                </div>
                
                <div class="coin-progress">
                    <div class="progress-label">
                        <span>Progress to Goal</span>
                        <span id="progressLabel">{coins}/30 Coins</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                </div>
            </div>
            
            <!-- Timer Section -->
            <div class="timer-section">
                <h2><i class="fas fa-stopwatch"></i> Study Timer</h2>
                <p>Track your study time and earn coins automatically</p>
                
                <div class="timer-display" id="timerDisplay">00:00:00</div>
                
                <div class="timer-controls">
                    <button class="timer-btn btn-start" id="startTimer">
                        <i class="fas fa-play"></i> Start
                    </button>
                    <button class="timer-btn btn-pause" id="pauseTimer">
                        <i class="fas fa-pause"></i> Pause
                    </button>
                    <button class="timer-btn btn-reset" id="resetTimer">
                        <i class="fas fa-redo"></i> Reset
                    </button>
                </div>
            </div>
            
            <!-- Study Stats -->
            <div class="study-stats">
                <div class="stat-card">
                    <div class="stat-value" id="totalTime">0h 0m</div>
                    <div class="stat-label">Total Study Time</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-value" id="coinsEarned">{coins}</div>
                    <div class="stat-label">Coins Earned</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-value" id="coinsNeeded">{30 - coins}</div>
                    <div class="stat-label">Coins Needed</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-value" id="progressPercent">{((coins/30)*100):.1f}%</div>
                    <div class="stat-label">Progress</div>
                </div>
            </div>
            
            <!-- Server Status -->
            <div class="server-status">
                <i class="fas fa-server"></i> 
                <span class="status-connected">Connected to Server</span> • 
                Coins and study time are being saved on the server
            </div>
            
            <!-- Info Section -->
            <div style="background: #f0f9ff; padding: 1.5rem; border-radius: 15px; margin-top: 2rem;">
                <h3 style="color: #0369a1; margin-bottom: 1rem;">
                    <i class="fas fa-info-circle"></i> How it Works
                </h3>
                <ul style="color: #4b5563; padding-left: 1.5rem;">
                    <li style="margin-bottom: 0.5rem;">Start the timer when you begin studying</li>
                    <li style="margin-bottom: 0.5rem;">Every 2 hours of study = 1 coin</li>
                    <li style="margin-bottom: 0.5rem;">Reach 30 coins to get a special gift</li>
                    <li>Your progress is saved on the server automatically</li>
                </ul>
            </div>
        </main>
    </div>
    
    <script>
        // Timer variables
        let timerInterval;
        let studySeconds = 0;
        let isTimerRunning = false;
        let totalStudySeconds = {study_hours * 3600 + study_minutes * 60};
        
        // Update timer display
        function updateTimerDisplay() {{
            const hours = Math.floor(studySeconds / 3600);
            const minutes = Math.floor((studySeconds % 3600) / 60);
            const seconds = studySeconds % 60;
            
            document.getElementById('timerDisplay').textContent = 
                `${{hours.toString().padStart(2, '0')}}:${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;
        }}
        
        // Update total time display
        function updateTotalTimeDisplay() {{
            const totalHours = Math.floor(totalStudySeconds / 3600);
            const totalMinutes = Math.floor((totalStudySeconds % 3600) / 60);
            document.getElementById('totalTime').textContent = `${{totalHours}}h ${{totalMinutes}}m`;
        }}
        
        // Start timer
        function startTimer() {{
            if (!isTimerRunning) {{
                isTimerRunning = true;
                timerInterval = setInterval(() => {{
                    studySeconds++;
                    updateTimerDisplay();
                    
                    // Save to server every 60 seconds
                    if (studySeconds % 60 === 0) {{
                        saveStudyTime();
                    }}
                }}, 1000);
            }}
        }}
        
        // Pause timer
        function pauseTimer() {{
            if (isTimerRunning) {{
                isTimerRunning = false;
                clearInterval(timerInterval);
                saveStudyTime();
            }}
        }}
        
        // Reset timer
        function resetTimer() {{
            pauseTimer();
            studySeconds = 0;
            updateTimerDisplay();
            saveStudyTime();
        }}
        
        // Save study time to server
        function saveStudyTime() {{
            fetch('/api/update_coins', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{
                    action: 'update_timer',
                    study_seconds: studySeconds
                }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    // Update display with server data
                    updateCoinDisplay(data.coins, data.study_time);
                    studySeconds = 0; // Reset local timer after saving
                    updateTimerDisplay();
                }}
            }})
            .catch(error => console.error('Error saving study time:', error));
        }}
        
        // Update coin display
        function updateCoinDisplay(coins, studyTime) {{
            totalStudySeconds = studyTime;
            const hours = Math.floor(studyTime / 3600);
            const minutes = Math.floor((studyTime % 3600) / 60);
            
            // Update all displays
            document.getElementById('coinValue').textContent = coins;
            document.getElementById('coinsEarned').textContent = coins;
            document.getElementById('coinsNeeded').textContent = 30 - coins;
            document.getElementById('progressLabel').textContent = coins + '/30 Coins';
            document.getElementById('progressPercent').textContent = ((coins/30)*100).toFixed(1) + '%';
            
            // Update progress bar
            const progress = (coins / 30) * 100;
            document.getElementById('progressFill').style.width = progress + '%';
            
            // Update total time
            updateTotalTimeDisplay();
            
            // Check if reached goal
            if (coins >= 30) {{
                showCongratulations();
            }}
        }}
        
        // Load data from server
        function loadServerData() {{
            fetch('/api/get_coins')
                .then(response => response.json())
                .then(data => {{
                    updateCoinDisplay(data.coins, data.study_time);
                }})
                .catch(error => console.error('Error loading data:', error));
        }}
        
        // Show congratulations message
        function showCongratulations() {{
            const congratMsg = document.createElement('div');
            congratMsg.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: linear-gradient(135deg, #10b981, #059669);
                color: white;
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                z-index: 10000;
                text-align: center;
                animation: fadeIn 0.5s ease;
            `;
            congratMsg.innerHTML = `
                <div style="font-size: 3rem; margin-bottom: 1rem;">🎉</div>
                <h2 style="font-size: 1.8rem; margin-bottom: 0.5rem;">CONGRATULATIONS!</h2>
                <p style="margin-bottom: 1.5rem;">You've reached 30 coins! 🎁</p>
                <button onclick="this.parentElement.remove()" style="padding: 0.8rem 1.5rem; background: white; color: #10b981; border: none; border-radius: 25px; font-weight: bold; cursor: pointer;">
                    Continue Studying
                </button>
            `;
            document.body.appendChild(congratMsg);
        }}
        
        // Event listeners
        document.getElementById('startTimer').addEventListener('click', startTimer);
        document.getElementById('pauseTimer').addEventListener('click', pauseTimer);
        document.getElementById('resetTimer').addEventListener('click', resetTimer);
        
        // Initial setup
        updateTimerDisplay();
        updateTotalTimeDisplay();
        loadServerData();
        
        // Auto-save on page unload
        window.addEventListener('beforeunload', function() {{
            if (studySeconds > 0) {{
                saveStudyTime();
            }}
        }});
        
        // Load data every 30 seconds
        setInterval(loadServerData, 30000);
    </script>
</body>
</html>'''
    
    def wrap_in_app_layout(self, content, title):
        """Wrap content in app layout"""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Bimalism</title>
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Poppins', sans-serif;
            background: #f9fafb;
            color: #1f2937;
            min-height: 100vh;
        }}
        
        .app-container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
            box-shadow: 0 0 30px rgba(0, 0, 0, 0.1);
        }}
        
        .app-header {{
            background: linear-gradient(135deg, #2563eb, #4f46e5);
            color: white;
            padding: 1.2rem 1.5rem;
            display: flex;
            align-items: center;
            gap: 12px;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        
        .back-button {{
            background: rgba(255, 255, 255, 0.15);
            border: none;
            width: 44px;
            height: 44px;
            border-radius: 12px;
            color: white;
            font-size: 1.2rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            text-decoration: none;
        }}
        
        .back-button:hover {{
            background: rgba(255, 255, 255, 0.25);
            transform: translateX(-3px);
        }}
        
        .app-title {{
            font-size: 1.5rem;
            font-weight: 700;
        }}
        
        .module-content {{
            padding: 2rem 1.5rem;
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <header class="app-header">
            <a href="/" class="back-button">
                <i class="fas fa-arrow-left"></i>
            </a>
            <div class="app-title">{title}</div>
        </header>
        
        <main class="module-content">
            {content}
        </main>
    </div>
    
    <script>
        console.log('📚 {title} Page Loaded');
    </script>
</body>
</html>'''

def start_server():
    """Start the Bimalism server"""
    print("=" * 70)
    print("🚀 BIMALISM SERVER WITH CLEAN HAMBURGER MENU")
    print("=" * 70)
    print("✨ FEATURES:")
    print("   • Clean header with only logo")
    print("   • Hamburger menu in top-right corner")
    print("   • Sidebar with ONLY requested items")
    print("   • Server-side coin tracking")
    print("")
    print("📱 MENU INCLUDES ONLY:")
    print("   • Home")
    print("   • Bio Data")
    print("   • Features")
    print("   • NEET")
    print("   • JEE")
    print("   • Results")
    print("   • Testimonials")
    print("   • Game")
    print("   • Study Challenge (with coins)")
    print("   • Study Resources")
    print("   • Calculator")
    print("   • Settings")
    print("   • Download App")
    print("")
    print("💰 COIN TRACKING:")
    print("   • Study timer saves to server")
    print("   • 2 hours = 1 coin (auto-calculated)")
    print("   • Data stored in: bimalism_data.json")
    print("")
    print(f"🌐 Access at: http://localhost:{PORT}")
    print("=" * 70)
    
    # Create data file if not exists
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'coins': 0,
                'study_time': 0,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
        print(f"📁 Created data file: {DATA_FILE}")
    
    # Create missing HTML files
    required_files = [
        'neet.html', 'jee.html', 'g.html', 'settings.html', 
        'tips.html', 'table.html', 'calculator.html', 'bio-data-pop-up.html',
        'h.html', 't.html'
    ]
    
    for filename in required_files:
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f'''<!DOCTYPE html>
<html>
<head>
    <title>{filename.replace('.html', '').upper()} - Bimalism</title>
</head>
<body style="padding: 2rem; text-align: center;">
    <h1>{filename.replace('.html', '').replace('-', ' ').title()}</h1>
    <p>This page is under construction.</p>
    <a href="/" style="display: inline-block; margin-top: 1rem; padding: 0.8rem 1.5rem; background: #2563eb; color: white; border-radius: 25px; text-decoration: none;">
        ← Back to Home
    </a>
</body>
</html>''')
            print(f"📄 Created placeholder: {filename}")
    
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except:
        pass
    
    with socketserver.TCPServer(("", PORT), BimalismServer) as httpd:
        try:
            print(f"✅ Server started on port {PORT}")
            print("🍔 Click the hamburger menu (top-right) for navigation")
            print("📱 Menu shows ONLY the requested items")
            print("⏰ Go to /registration to start the study timer")
            print("🔄 Press Ctrl+C to stop server")
            print("=" * 70)
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
            print("✨ Thank you for using Bimalism!")

if __name__ == "__main__":
    start_server()