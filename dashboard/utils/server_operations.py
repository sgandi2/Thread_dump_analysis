"""
Integration Server Operations
Provides functions to restart and manage webMethods Integration Server
"""

import subprocess
import os
import time
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()


def restart_integration_server() -> Dict[str, Any]:
    """
    Restart the webMethods Integration Server using restart.bat
    
    Returns:
        Dict with status, message, and details
    """
    # Default Integration Server path
    is_bin_path = r"C:\SoftwareAG11\IntegrationServer\instances\default\bin"
    restart_bat = os.path.join(is_bin_path, "restart.bat")
    
    result = {
        'success': False,
        'message': '',
        'details': {}
    }
    
    try:
        # Step 1: Check if restart.bat exists
        if not os.path.exists(restart_bat):
            result['message'] = f'restart.bat not found at {restart_bat}'
            result['details']['error'] = 'File not found'
            print(f"[ERROR] restart.bat not found at {restart_bat}")
            return result
        
        print(f"[1/3] Found restart.bat at {restart_bat}")
        result['details']['restart_script'] = restart_bat
        
        # Step 2: Execute restart.bat
        print(f"[2/3] Executing restart.bat...")
        
        # Run restart.bat in the background
        process = subprocess.Popen(
            [restart_bat],
            cwd=is_bin_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
        
        print("[SUCCESS] Restart command executed")
        result['details']['restart_initiated'] = True
        
        # Step 3: Wait for server to come back up
        print("[3/3] Waiting for server to restart (this may take 30-90 seconds)...")
        
        server_url = os.getenv('WEBMETHODS_URL', 'http://localhost:5555')
        max_wait = 120  # Wait up to 2 minutes
        wait_interval = 5
        elapsed = 0
        
        time.sleep(15)  # Initial wait for shutdown
        
        while elapsed < max_wait:
            try:
                # Try to connect to server
                check_response = requests.get(
                    server_url,
                    timeout=5
                )
                
                if check_response.status_code == 200:
                    print(f"[SUCCESS] Server is back online after {elapsed} seconds")
                    result['success'] = True
                    result['message'] = f'Integration Server restarted successfully in {elapsed} seconds'
                    result['details']['restart_time'] = elapsed
                    result['details']['post_restart_status'] = 'online'
                    return result
                
            except requests.exceptions.RequestException:
                # Server still restarting
                pass
            
            time.sleep(wait_interval)
            elapsed += wait_interval
            print(f"  Waiting... ({elapsed}s / {max_wait}s)")
        
        # Timeout waiting for server
        result['success'] = False
        result['message'] = f'Server restart initiated but did not come back online within {max_wait} seconds. Please check manually.'
        result['details']['timeout'] = True
        result['details']['note'] = 'Server may still be restarting - check Integration Server console'
        
    except Exception as e:
        result['message'] = f'Error executing restart: {str(e)}'
        result['details']['error'] = str(e)
        print(f"[ERROR] Error executing restart: {e}")
    
    return result


def get_server_status() -> Dict[str, Any]:
    """
    Get current Integration Server status
    
    Returns:
        Dict with server status information
    """
    server_url = os.getenv('WEBMETHODS_URL', 'http://localhost:5555')
    username = os.getenv('WEBMETHODS_USER', 'Administrator')
    password = os.getenv('WEBMETHODS_PASSWORD', 'manage')
    
    # Use https for REST API calls
    if server_url.startswith('http://'):
        server_url = server_url.replace('http://', 'https://')
    
    try:
        status_url = f"{server_url}/admin/server/status"
        response = requests.get(
            status_url,
            auth=(username, password),
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                'online': True,
                'status': 'running',
                'message': 'Server is online and responding'
            }
        else:
            return {
                'online': False,
                'status': 'error',
                'message': f'Server returned status code: {response.status_code}'
            }
    
    except Exception as e:
        return {
            'online': False,
            'status': 'offline',
            'message': f'Cannot connect to server: {str(e)}'
        }


if __name__ == '__main__':
    """Test the restart functionality"""
    print("=" * 70)
    print("Integration Server Restart Test")
    print("=" * 70)
    
    # Check status first
    print("\nChecking server status...")
    status = get_server_status()
    print(f"Status: {status}")
    
    if status['online']:
        print("\n⚠️  WARNING: This will restart the Integration Server!")
        print("Press Ctrl+C to cancel, or wait 5 seconds to proceed...")
        try:
            time.sleep(5)
            print("\nInitiating restart...")
            result = restart_integration_server()
            print("\n" + "=" * 70)
            print("RESULT:")
            print(f"Success: {result['success']}")
            print(f"Message: {result['message']}")
            print(f"Details: {result['details']}")
            print("=" * 70)
        except KeyboardInterrupt:
            print("\n\nRestart cancelled by user")
    else:
        print("\n✗ Server is not online, cannot test restart")

# Made with Bob
