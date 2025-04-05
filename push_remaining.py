"""
Script to push remaining files to GitHub
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

def copy_files(temp_dir, files_to_push):
    """Copy files to temp directory"""
    for file_path in files_to_push:
        source_path = Path(file_path)
        if not source_path.exists():
            print(f"Warning: {source_path} does not exist, skipping")
            continue
            
        dest_path = temp_dir / file_path
        
        # Create parent directories if needed
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        try:
            shutil.copy2(source_path, dest_path)
            print(f"Copied: {source_path} -> {dest_path}")
        except Exception as e:
            print(f"Error copying {source_path}: {e}")

def push_remaining():
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
    
    # Copy any remaining files we might have missed
    files_to_push = [
        "temp_logout.html",
        "push_to_github.py",
        "push_templates.py",
        "push_static.py",
        "push_remaining.py"
    ]
    
    copy_files(temp_dir, files_to_push)
    
    # Copy the schema.sql file if it exists
    schema_file = Path("schema.sql")
    if schema_file.exists():
        dest_schema = temp_dir / "schema.sql"
        try:
            shutil.copy2(schema_file, dest_schema)
            print(f"Copied: {schema_file} -> {dest_schema}")
        except Exception as e:
            print(f"Error copying schema file: {e}")
    
    # Create a schema dump from the database
    print("Creating schema dump from database...")
    schema_path = temp_dir / "schema.sql"
    if not schema_path.exists():
        db_file = Path("instance/pharmaceptor.db")
        if db_file.exists():
            dump_cmd = f"sqlite3 {db_file} .schema > {schema_path}"
            run_cmd(dump_cmd)
            print(f"Created schema dump at {schema_path}")
    
    # Add, commit, and push changes
    if not run_cmd("git add .", cwd=temp_dir):
        return False
    
    # Commit with a meaningful message
    if not run_cmd("git commit -m 'Add remaining files and database schema'", cwd=temp_dir):
        print("No changes to commit or commit failed")
        return True  # Continue even if nothing to commit
    
    # Push to remote
    if not run_cmd("git push", cwd=temp_dir):
        return False
    
    print("Remaining files pushed successfully!")
    return True

if __name__ == "__main__":
    success = push_remaining()
    sys.exit(0 if success else 1)