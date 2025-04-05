"""
Script to push the static directory to GitHub
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

def run_cmd(cmd, cwd=None):
    """Run a command and return its output"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            shell=True,
            cwd=cwd
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stdout:
            print(f"Command output: {e.stdout}")
        if e.stderr:
            print(f"Command error: {e.stderr}")
        return False

def push_static():
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("No GitHub token available. Please set the GITHUB_TOKEN environment variable.")
        return False
    
    temp_dir = Path("temp_clone")
    
    # Clean up any existing temp directory
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    # Create temp directory
    temp_dir.mkdir(exist_ok=True)
    
    # Set up Git config
    run_cmd("git config --global user.email 'replit@example.com'")
    run_cmd("git config --global user.name 'Replit AI'")
    
    # Clone the repository
    clone_cmd = f"git clone https://{github_token}@github.com/gmkdigitalmedia/pharma.git ."
    if not run_cmd(clone_cmd, cwd=temp_dir):
        return False
    
    # Copy static directory
    source_path = Path('static')
    if not source_path.exists():
        print(f"Static directory not found: {source_path}")
        return False
        
    dest_path = temp_dir / 'static'
    
    try:
        if dest_path.exists():
            shutil.rmtree(dest_path)
        print(f"Copying static directory from {source_path} to {dest_path}")
        shutil.copytree(source_path, dest_path)
    except Exception as e:
        print(f"Error copying static directory: {e}")
        return False
    
    # Add, commit, and push changes
    if not run_cmd("git add static/", cwd=temp_dir):
        return False
    
    # Commit with a meaningful message
    if not run_cmd("git commit -m 'Update static files from Replit'", cwd=temp_dir):
        print("No changes to commit or commit failed")
        return True  # Continue even if nothing to commit
    
    # Push to remote
    if not run_cmd("git push", cwd=temp_dir):
        return False
    
    print("Static files pushed successfully!")
    return True

if __name__ == "__main__":
    success = push_static()
    sys.exit(0 if success else 1)