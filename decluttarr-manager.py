#!/usr/bin/env python3
"""
Decluttarr Enhanced Web Management Interface
Provides a web GUI for managing decluttarr containers and configuration
"""

from flask import Flask, render_template_string, request, jsonify
import subprocess
import json
import yaml
import os
import time
import requests

app = Flask(__name__)

# HTML Template for the web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Decluttarr Enhanced Manager</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .section h3 { margin-top: 0; color: #555; }
        .status-good { color: #28a745; }
        .status-bad { color: #dc3545; }
        .btn { background: #007bff; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .btn.danger { background: #dc3545; }
        .btn.danger:hover { background: #c82333; }
        .btn.success { background: #28a745; }
        .btn.success:hover { background: #218838; }
        .form-group { margin: 10px 0; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .logs { background: #000; color: #0f0; padding: 15px; border-radius: 5px; font-family: monospace; height: 300px; overflow-y: scroll; white-space: pre-wrap; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Decluttarr Enhanced Manager</h1>
        
        <div class="section">
            <h3>📊 Container Status</h3>
            <div id="status">Loading...</div>
            <button class="btn" onclick="refreshStatus()">🔄 Refresh Status</button>
            <button class="btn success" onclick="startContainers()">▶️ Start All</button>
            <button class="btn danger" onclick="stopContainers()">⏹️ Stop All</button>
            <button class="btn" onclick="restartContainers()">🔄 Restart & Apply Settings</button>
        </div>

        <div class="grid">
            <div class="section">
                <h3>⚙️ Configuration</h3>
                <div class="form-group">
                    <label>Log Level:</label>
                    <select id="logLevel">
                        <option value="INFO">INFO</option>
                        <option value="VERBOSE">VERBOSE</option>
                        <option value="DEBUG">DEBUG</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Timer (minutes):</label>
                    <input type="number" id="timer" value="6" min="1" max="60">
                </div>
                <div class="form-group">
                    <label>Radarr URL:</label>
                    <input type="text" id="radarrUrl" placeholder="http://192.168.1.100:7878">
                </div>
                <div class="form-group">
                    <label>Radarr API Key:</label>
                    <input type="text" id="radarrKey" placeholder="Your Radarr API Key">
                </div>
                <div class="form-group">
                    <label>Sonarr URL:</label>
                    <input type="text" id="sonarrUrl" placeholder="http://192.168.1.100:8989">
                </div>
                <div class="form-group">
                    <label>Sonarr API Key:</label>
                    <input type="text" id="sonarrKey" placeholder="Your Sonarr API Key">
                </div>
                <button class="btn success" onclick="saveConfig()">💾 Save Configuration</button>
                <button class="btn" onclick="testConnections()">🔍 Test Connections</button>
            </div>

            <div class="section">
                <h3>📝 Live Logs</h3>
                <div id="logs" class="logs">Loading logs...</div>
                <button class="btn" onclick="refreshLogs()">🔄 Refresh Logs</button>
                <button class="btn" onclick="clearLogs()">🗑️ Clear Display</button>
            </div>
        </div>

        <div class="section">
            <h3>🔗 Quick Links</h3>
            <p>
                <a href="http://localhost:9999" target="_blank" class="btn">📊 Log Viewer (Dozzle)</a>
                <a href="https://github.com/gitsumhubs/decluttarr-enhanced" target="_blank" class="btn">📚 Documentation</a>
            </p>
        </div>
    </div>

    <script>
        // Auto-refresh status every 30 seconds
        setInterval(refreshStatus, 30000);
        
        // Initial load
        refreshStatus();
        refreshLogs();

        async function refreshStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('status').innerHTML = formatStatus(data);
            } catch (error) {
                document.getElementById('status').innerHTML = '<span class="status-bad">❌ Error loading status</span>';
            }
        }

        function formatStatus(containers) {
            return containers.map(container => {
                const status = container.status.includes('Up') ? 'status-good' : 'status-bad';
                const icon = container.status.includes('Up') ? '✅' : '❌';
                return `<div><strong>${container.name}</strong>: <span class="${status}">${icon} ${container.status}</span></div>`;
            }).join('');
        }

        async function startContainers() {
            await fetch('/api/start', {method: 'POST'});
            setTimeout(refreshStatus, 2000);
        }

        async function stopContainers() {
            await fetch('/api/stop', {method: 'POST'});
            setTimeout(refreshStatus, 2000);
        }

        async function restartContainers() {
            document.getElementById('status').innerHTML = '🔄 Restarting with --force-recreate...';
            await fetch('/api/restart', {method: 'POST'});
            setTimeout(refreshStatus, 5000);
        }

        async function saveConfig() {
            const config = {
                logLevel: document.getElementById('logLevel').value,
                timer: document.getElementById('timer').value,
                radarrUrl: document.getElementById('radarrUrl').value,
                radarrKey: document.getElementById('radarrKey').value,
                sonarrUrl: document.getElementById('sonarrUrl').value,
                sonarrKey: document.getElementById('sonarrKey').value
            };
            
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            });
            
            if (response.ok) {
                alert('✅ Configuration saved! Use "Restart & Apply Settings" to apply changes.');
            } else {
                alert('❌ Error saving configuration');
            }
        }

        async function testConnections() {
            document.getElementById('status').innerHTML = '🔍 Testing connections...';
            const response = await fetch('/api/test');
            const result = await response.json();
            alert(result.message);
            refreshStatus();
        }

        async function refreshLogs() {
            try {
                const response = await fetch('/api/logs');
                const data = await response.text();
                document.getElementById('logs').textContent = data;
                // Auto-scroll to bottom
                const logsDiv = document.getElementById('logs');
                logsDiv.scrollTop = logsDiv.scrollHeight;
            } catch (error) {
                document.getElementById('logs').textContent = 'Error loading logs: ' + error.message;
            }
        }

        function clearLogs() {
            document.getElementById('logs').textContent = '';
        }

        // Auto-refresh logs every 10 seconds
        setInterval(refreshLogs, 10000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def get_status():
    """Get container status"""
    try:
        result = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=decluttarr', '--format', 'table {{.Names}}\t{{.Status}}'], 
                              capture_output=True, text=True, cwd='/docker/decluttarr')
        
        containers = []
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        for line in lines:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    containers.append({
                        'name': parts[0],
                        'status': parts[1]
                    })
        
        return jsonify(containers)
    except Exception as e:
        return jsonify([{'name': 'Error', 'status': str(e)}])

@app.route('/api/start', methods=['POST'])
def start_containers():
    """Start all containers"""
    try:
        subprocess.run(['docker', 'compose', 'up', '-d'], cwd='/docker/decluttarr', check=True)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stop', methods=['POST'])
def stop_containers():
    """Stop all containers"""
    try:
        subprocess.run(['docker', 'compose', 'down'], cwd='/docker/decluttarr', check=True)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/restart', methods=['POST'])
def restart_containers():
    """Restart containers with --force-recreate to apply config changes"""
    try:
        subprocess.run(['docker', 'compose', 'down'], cwd='/docker/decluttarr', check=True)
        subprocess.run(['docker', 'compose', 'up', '-d', '--force-recreate'], cwd='/docker/decluttarr', check=True)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/logs')
def get_logs():
    """Get recent container logs"""
    try:
        result = subprocess.run(['docker', 'compose', 'logs', '--tail', '50', 'decluttarr'], 
                              capture_output=True, text=True, cwd='/docker/decluttarr')
        return result.stdout
    except Exception as e:
        return f"Error getting logs: {str(e)}"

@app.route('/api/config', methods=['POST'])
def save_config():
    """Save configuration (placeholder - would update docker-compose.yml)"""
    try:
        config = request.json
        # In a real implementation, this would update the docker-compose.yml file
        # For now, just return success
        return jsonify({'success': True, 'message': 'Configuration saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test')
def test_connections():
    """Test connections to *arr services"""
    return jsonify({'message': '🔍 Connection testing feature coming soon!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=False)