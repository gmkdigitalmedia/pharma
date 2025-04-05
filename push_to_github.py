"""
Script to push code to GitHub in batches
"""
import os
import subprocess
import sys
import shutil
import time
from pathlib import Path

# Define batches of related files
BATCHES = [
    # Batch 1: Core application files
    [
        "main.py", 
        "app.py", 
        "models.py", 
        "routes.py", 
        "forms.py", 
        "utils.py"
    ],
    # Batch 2: Auth-related files
    [
        "create_admin.py",
        "list_users.py",
        "reset_password.py",
        "add_organization_id.py",
        "add_organization_id_to_invitation.py"
    ],
    # Batch 3: Services and utilities
    [
        "ai_services.py",
        "email_service.py",
        "asset_utils.py",
        "test_session.py"
    ],
    # Batch 4: Configuration files
    [
        ".replit",
        "pyproject.toml",
        "replit.nix",
        "uv.lock",
        "README.md"
    ],
    # Batch 5: Static assets
    [
        "generated-icon.png"
    ],
]

# Define batches of directories to push
DIR_BATCHES = [
    # Batch 1: Templates
    ["templates"],
    # Batch 2: Static
    ["static"],
]

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

def setup_repo():
    """Set up the Git repository"""
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("No GitHub token available. Please set the GITHUB_TOKEN environment variable.")
        return None
    
    # Clean up any existing temp directory
    temp_dir = Path("temp_clone")
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
        return None
    
    return temp_dir

def push_batch(batch, temp_dir, batch_name):
    """Push a batch of files to GitHub"""
    print(f"\n--- Pushing {batch_name} ---")
    
    # Copy each file in the batch
    for file_path in batch:
        source_path = Path(file_path)
        if not source_path.exists():
            print(f"Warning: {source_path} does not exist, skipping")
            continue
            
        dest_path = temp_dir / file_path
        
        # Create parent directories if needed
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        try:
            if source_path.is_dir():
                # Copy directory contents
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                shutil.copytree(source_path, dest_path)
                print(f"Copied directory: {source_path} -> {dest_path}")
            else:
                # Copy file
                shutil.copy2(source_path, dest_path)
                print(f"Copied file: {source_path} -> {dest_path}")
        except Exception as e:
            print(f"Error copying {source_path}: {e}")
    
    # Add, commit, and push the batch
    if not run_cmd("git add .", cwd=temp_dir):
        return False
    
    # Commit with a meaningful message
    if not run_cmd(f'git commit -m "Update {batch_name} from Replit"', cwd=temp_dir):
        print("No changes to commit or commit failed")
        return True  # Continue even if nothing to commit
    
    # Push to remote
    if not run_cmd("git push", cwd=temp_dir):
        return False
    
    return True

def copy_directory(source_dir, dest_dir, temp_dir):
    """Copy a directory to the temp directory"""
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Warning: {source_path} does not exist, skipping")
        return False
        
    dest_path = temp_dir / dest_dir
    
    # Create parent directories if needed
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    try:
        if dest_path.exists():
            shutil.rmtree(dest_path)
        shutil.copytree(source_path, dest_path)
        print(f"Copied directory: {source_path} -> {dest_path}")
        return True
    except Exception as e:
        print(f"Error copying directory {source_path}: {e}")
        return False

def main():
    """Main function to push code to GitHub in batches"""
    # Set up the repository
    temp_dir = setup_repo()
    if not temp_dir:
        print("Failed to set up repository.")
        return False
    
    # Push each batch of files
    for i, batch in enumerate(BATCHES):
        batch_name = f"Batch {i+1}"
        if not push_batch(batch, temp_dir, batch_name):
            print(f"Failed to push {batch_name}.")
            return False
        time.sleep(1)  # Pause between batches
    
    # Push directory batches
    for i, dir_batch in enumerate(DIR_BATCHES):
        batch_name = f"Directory Batch {i+1}"
        print(f"\n--- Pushing {batch_name} ---")
        
        # Copy each directory in the batch
        for directory in dir_batch:
            if not copy_directory(directory, directory, temp_dir):
                continue
        
        # Add, commit, and push the batch
        if not run_cmd("git add .", cwd=temp_dir):
            print(f"Failed to add {batch_name} changes.")
            continue
        
        # Commit with a meaningful message
        if not run_cmd(f'git commit -m "Update {batch_name} from Replit"', cwd=temp_dir):
            print("No changes to commit or commit failed")
            continue  # Continue even if nothing to commit
        
        # Push to remote
        if not run_cmd("git push", cwd=temp_dir):
            print(f"Failed to push {batch_name}.")
            continue
            
        time.sleep(1)  # Pause between batches
    
    print("\nAll batches pushed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)