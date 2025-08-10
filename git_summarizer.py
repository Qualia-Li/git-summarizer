#!/usr/bin/env python3
"""
Git History Summarizer

Usage: python git_summarizer.py --date 2024-01-01 --projects-folder /path/to/projects

This program checks git history across all projects in a specified folder
and summarizes the commits using Azure OpenAI API.

Optional: Create a .env file with:
AZURE_OPENAI_KEY=your_key_here
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
AUTHOR_FILTER=comma,separated,author,names
"""

import os
import sys
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

class GitHistorySummarizer:
    def __init__(self, azure_key: str = None, endpoint: str = None):
        """Initialize the summarizer with Azure OpenAI credentials."""
        # Use provided credentials or defaults from environment
        self.azure_key = azure_key or os.getenv("AZURE_OPENAI_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_ENDPOINT")

        self.client = AzureOpenAI(
            api_key=self.azure_key,
            api_version=os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=self.endpoint,
            azure_deployment="gpt-4o-2",
        )
        
    def get_git_projects(self, projects_folder: str) -> List[str]:
        """Find all git repositories in the projects folder."""
        git_projects = []
        # Expand tilde to home directory if present
        expanded_path = os.path.expanduser(projects_folder)
        projects_path = Path(expanded_path)
        
        if not projects_path.exists():
            raise ValueError(f"Projects folder does not exist: {projects_folder}")
            
        for item in projects_path.iterdir():
            if item.is_dir():
                git_dir = item / ".git"
                if git_dir.exists():
                    git_projects.append(str(item))
                    
        return git_projects
    
    def get_git_log(self, project_path: str, date: str) -> List[Dict[str, Any]]:
        """Get git log for a specific project on a given date."""
        try:
            # Change to project directory
            os.chdir(project_path)
            
            # Get author filter from environment
            author_filter = os.getenv("AUTHOR_FILTER", "").strip()
            
            # Get git log with detailed information for a specific date
            cmd = [
                "git", "log", 
                "--since", f"{date} 00:00:00",
                "--until", f"{date} 23:59:59",
                "--pretty=format:%H|%an|%ad|%s|%b",
                "--date=short",
                "--all"
            ]
            
            # Add author filter if specified
            if author_filter:
                authors = [author.strip() for author in author_filter.split(",")]
                for author in authors:
                    cmd.extend(["--author", author])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('|', 4)
                    if len(parts) >= 4:
                        commit = {
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'subject': parts[3],
                            'body': parts[4] if len(parts) > 4 else ''
                        }
                        commits.append(commit)
                        
            return commits
            
        except subprocess.CalledProcessError as e:
            print(f"Error getting git log for {project_path}: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error for {project_path}: {e}")
            return []
    
    def format_commits_for_summary(self, project_name: str, commits: List[Dict[str, Any]]) -> str:
        """Format commits into a readable string for summarization."""
        if not commits:
            return f"Project: {project_name}\nNo commits found in the specified date range.\n"
            
        formatted = f"Project: {project_name}\n"
        formatted += f"Total commits: {len(commits)}\n\n"
        
        for commit in commits:
            formatted += f"Date: {commit['date']}\n"
            formatted += f"Author: {commit['author']}\n"
            formatted += f"Subject: {commit['subject']}\n"
            if commit['body'].strip():
                formatted += f"Body: {commit['body']}\n"
            formatted += f"Hash: {commit['hash']}\n"
            formatted += "-" * 50 + "\n"
            
        return formatted
    
    def summarize_with_azure_openai(self, content: str, date: str) -> str:
        """Summarize the git history using Azure OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_MODEL", "gpt-4"),
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful assistant that summarizes git commit history. 
                        This is the commitment message by one person on different projects
                        Analyze the commits and provide a concise summary in no more than 4 sentences.
                        Don't need to be too detailed. Just give a high level overview. 
                        Talk more about features and products than technical details.
                        
                        Keep the summary professional and informative."""
                    },
                    {
                        "role": "user",
                        "content": f"Please summarize the following git commit history on {date}:\n\n{content}"
                    }
                ],
                max_tokens=int(os.getenv("MAX_TOKENS", "1000")),
                temperature=float(os.getenv("TEMPERATURE", "0.3"))
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating summary with Azure OpenAI: {e}"
    
    def run(self, projects_folder: str, date: str) -> str:
        """Main method to run the git history summarization."""
        print(f"Scanning for git projects in: {projects_folder}")
        print(f"Looking for commits on {date}...")
        
        # Get all git projects
        git_projects = self.get_git_projects(projects_folder)
        
        if not git_projects:
            return "No git repositories found in the specified folder."
        
        print(f"Found {len(git_projects)} git repositories")
        
        # Collect all commit data
        all_commits_data = ""
        total_commits = 0
        
        for project_path in git_projects:
            project_name = os.path.basename(project_path)
            # print(f"Processing: {project_name}")
            
            commits = self.get_git_log(project_path, date)
            total_commits += len(commits)
            if commits:
                print(f"Found {len(commits)} commits in {project_name}")
                for commit in commits:
                    print(f"\t{commit['date']}\t{commit['author']}\tCommit: {commit['subject']}")
            
            project_summary = self.format_commits_for_summary(project_name, commits)
            all_commits_data += project_summary + "\n\n"
        
        if total_commits == 0:
            return "No commits found in the specified date range across all projects."
        
        print(f"Total commits found: {total_commits}")
        print("Generating summary with Azure OpenAI...")
        
        # Generate summary using Azure OpenAI
        summary = self.summarize_with_azure_openai(all_commits_data, date)
        
        return summary


def main() -> str:
    """Main entry point."""
    
    print("Git History Summarizer")
    print("=" * 30)
    
    # Get date choice
    today = datetime.now()
    date_choices = []
    
    for i in range(6):
        date = today - timedelta(days=i)
        date_choices.append(date.strftime("%Y-%m-%d"))
    
    print("\nChoose a date to start from:")
    for i, date in enumerate(date_choices):
        if i == 0:
            print(f"{i}. {date} (Today)")
        else:
            print(f"{i}. {date} ({i} day(s) ago)")
    print("6. Custom date")
    
    while True:
        try:
            choice = input("\nEnter your choice (0-6): ").strip()
            if choice == "6":
                custom_date = input("Enter custom date (YYYY-MM-DD): ").strip()
                datetime.strptime(custom_date, "%Y-%m-%d")
                selected_date = custom_date
                break
            elif choice in ["0", "1", "2", "3", "4", "5"]:
                selected_date = date_choices[int(choice)]
                break
            else:
                print("Invalid choice. Please enter 0-6.")
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
    
    # Get projects folder
    default_folder = "~/proj"
    if len(sys.argv) > 1:
        projects_folder = sys.argv[1]
    else:
        projects_folder = input(f"\nEnter projects folder path (default: {default_folder}): ").strip()
        if not projects_folder:
            projects_folder = default_folder
    
    print(f"\nUsing date: {selected_date}")
    print(f"Using projects folder: {projects_folder}")
    
    # Check for author filter
    author_filter = os.getenv("AUTHOR_FILTER", "").strip()
    if author_filter:
        authors = [author.strip() for author in author_filter.split(",")]
        print(f"Filtering by authors: {', '.join(authors)}")
    else:
        print("No author filter applied (showing all authors)")
    
    # Create summarizer and run
    azure_key = os.getenv("AZURE_OPENAI_KEY")
    endpoint = os.getenv("AZURE_ENDPOINT")
    summarizer = GitHistorySummarizer(azure_key, endpoint)
    
    try:
        summary = summarizer.run(projects_folder, selected_date)
        print("\n" + "="*60)
        print("GIT HISTORY SUMMARY")
        print("="*60)
        print(summary)

        return summary
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
