#!/bin/bash

# Function to check if a path should be ignored
should_ignore() {
    local path="$1"
    
    # Normalize path for comparison (remove leading ./)
    local normalized_path="${path#./}"
    
    # Specific paths to exclude
    local exclude_paths=(
        "package.json"
        "package-lock.json"
        "frontend/public"
        "frontend/src/app/favicon.ico"
        "data"
        ".git"
        "backend/app/__pycache__"
        "backend/app/data"
        "backend/app/routers/__pycache__"
        "backend/app/utils/__pycache__"
        "backend/backend"
        "backend/venv"
    )
    
    # Check specific paths first
    for exclude in "${exclude_paths[@]}"; do
        if [[ "$normalized_path" == "$exclude"* ]] || [[ "$normalized_path" == *"/$exclude"* ]] || [[ "$normalized_path" == "$exclude" ]]; then
            return 0
        fi
    done
    
    # General patterns to ignore
    local ignore_patterns=(
        # Backend
        "backend/venv/"
        "backend/__pycache__/"
        "backend/*.pyc"
        "backend/.env"
        # Frontend
        "frontend/node_modules/"
        "frontend/.next/"
        "frontend/out/"
        "frontend/.env*.local"
        # Common patterns
        ".DS_Store"
        "*.log"
        ".vscode/"
        ".idea/"
        "/node_modules"
        "node_modules/"
        "/.pnp"
        ".pnp.*"
        ".yarn/*"
        "/coverage"
        "/.next/"
        "/out/"
        "*.pem"
        "npm-debug.log*"
        "yarn-debug.log*"
        "yarn-error.log*"
        ".pnpm-debug.log*"
        ".vercel"
        "*.tsbuildinfo"
        "next-env.d.ts"
        "__pycache__/"
        "*.py[cod]"
        "*\$py.class"
        "*.so"
        ".Python"
        "venv/"
        "env/"
        "ENV/"
        ".venv"
        ".env"
        "*.pyc"
        "*.pyo"
        "*.pyd"
        ".git"
        ".gitignore"
        "*.md"
        "Dockerfile"
        ".dockerignore"
        ".env.local"
        ".env.development.local"
        ".env.test.local"
        ".env.production.local"
    )
    
    for pattern in "${ignore_patterns[@]}"; do
        # Convert glob pattern to matching
        if [[ "$path" == *"$pattern"* ]] || [[ "$normalized_path" == *"$pattern"* ]]; then
            return 0
        fi
    done
    
    return 1
}

# Function to process files recursively
process_files() {
    local dir="$1"
    
    # Find all files (not directories) in the current directory and subdirectories
    # Skip hidden files and directories (those starting with .)
    find "$dir" -type f -not -path '*/.*' -not -path '*/.git/*' | sort | while read -r file; do
        # Skip the script itself
        if [[ "$file" == "$0" ]]; then
            continue
        fi
        
        # Skip if matches ignore patterns
        if should_ignore "$file"; then
            continue
        fi
        
        echo "### $file ###"
        
        # Check if file is readable
        if [[ -r "$file" ]]; then
            cat "$file"
        else
            echo "Error: Cannot read file $file (permission denied)"
        fi
        
        echo  # Add empty line between files for better readability
    done
}

# Start processing from current directory
process_files "."