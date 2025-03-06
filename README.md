# Workable Job Application Bot

An automated tool for applying to jobs on Workable.com, featuring intelligent form detection and filling capabilities.

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
    <div>
        <img src="https://github.com/user-attachments/assets/50a53d30-5a20-41a9-a1db-a3aee4ea8696" alt="Image" style="width: 100%;">
    </div>
    <div>
        <img src="https://github.com/user-attachments/assets/5a40abe3-1b4d-49af-875c-53f1e8cf49f3" alt="Image" style="width: 100%;">
    </div>
</div>

## How to use

Go to **Installation** section to install dependencies.

Run the application

```bash
sh start_ui_web.sh # for web interface
sh start_apply_job.sh # for command line interface
```

Then open your browser to `http://localhost:8080` for web interface.

## Features

- Automated form detection and filling
- Dynamic field mapping based on user metadata
- Captcha solving integration (2Captcha)
- Resume upload support
- Simple web interface
- Comprehensive logging

## Prerequisites

- Python 3.11+
- 2Captcha API key
- Modern web browser (Chrome/Chromium recommended)

## Execution Flow

For a URL like `https://jobs.workable.com/view/...`:

1. Browser starts → Page opens.
2. Navigates to URL → Loads application form.
3. Metadata loaded (e.g., John Doe, <john.doe@example.com>).
4. Captcha detected → Solved via 2Captcha → Injected.
5. Form elements found (name input, email input, resume upload).
6. Fields mapped (name → "John Doe", email → "<john.doe@example.com>").
7. Fields filled → Resume uploaded.
8. Required fields validated.
9. Submit button clicked.
10. Success message detected → Logged.
11. Errors (if any) logged (e.g., "Timeout waiting for submit button").
12. Browser closed.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/workable-job-applier.git
cd workable-job-applier
```

2. Create and activate a virtual environment:

```bash
conda create -n workable-job-applier python=3.11
conda activate workable-job-applier
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:

```bash
playwright install
```

5. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your 2Captcha API key and other settings
```

## Usage

### Command Line Interface

```bash
sh start_apply_job.sh
```

### Web Interface

```bash
sh start_ui_web.sh
```

Then open your browser to `http://localhost:8080`

## Project Structure

```
workable-job-applier/
├── src/
│   ├── core/           # Core application logic
│   ├── config/         # Configuration files
│   ├── utils/          # Utility functions
│   └── ui/             # Web interface
├── tests/              # Test files
├── data/               # Data files (resumes, metadata)
└── logs/               # Application logs
```

## Configuration

1. Create a `.env` file with your settings:

```
TWOCAPTCHA_API_KEY=your_api_key_here
HEADLESS=true
DEFAULT_TIMEOUT=30000
```

2. Prepare your user metadata in `data/user_metadata.json`:

```json
{
    "name": "Your Name",
    "contact_information": {
        "email": "your.email@example.com",
        "phone": "+1234567890"
    },
    "resume_path": "data/resumes/your_resume.pdf"
}
```

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 guidelines. To check code style:

```bash
flake8
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
