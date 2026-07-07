# Git History Summarizer

A Python tool that analyzes git commit history across multiple projects and generates intelligent summaries using the OpenAI API.

## Features

- **Multi-project Analysis**: Scans multiple git repositories in a specified folder
- **Date-specific Filtering**: Get commits from a specific date or date range
- **Author Filtering**: Filter commits by specific authors (optional)
- **AI-powered Summaries**: Uses OpenAI to generate intelligent, concise summaries
- **Cross-platform**: Works on macOS, Linux, and Windows
- **Easy Setup**: Simple configuration via environment variables

## Installation

### Prerequisites

- Python 3.8 or higher
- Git installed and accessible from command line
- OpenAI API access

### Setup

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd git-summarizer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project directory:
   ```env
   OPENAI_API_KEY=your_openai_key_here
   OPENAI_MODEL=gpt-5.5
   AUTHOR_FILTER=comma,separated,author,names
   ```

## Usage

### Basic Usage

Run the script interactively:
```bash
pip install openai
pip install dotenv
python git_summarizer.py
```

The script will prompt you for:
1. **Date selection**: Choose from recent dates or enter a custom date
2. **Projects folder**: Path to folder containing git repositories (default: `~/proj`)


### Examples

**Get commits from yesterday:**
```bash
python git_summarizer.py
# Choose option 1 when prompted for date
```

**Filter by specific authors:**
Add to your `.env` file:
```env
AUTHOR_FILTER=John Doe,Jane Smith
```

## How It Works

1. **Project Discovery**: Scans the specified folder for git repositories
2. **Commit Extraction**: Uses `git log` to extract commits from the specified date
3. **Author Filtering**: Optionally filters commits by author names
4. **Data Formatting**: Formats commit data for AI processing
5. **AI Summarization**: Sends formatted data to OpenAI for intelligent summarization
6. **Output**: Displays a concise, professional summary
