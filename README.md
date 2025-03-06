# Workable Job Application Bot

An automated tool for applying to jobs on Workable.com, featuring intelligent form detection and filling capabilities.

## Features

- Automated form detection and filling
- Dynamic field mapping based on user metadata
- Captcha solving integration (2Captcha)
- Resume upload support
- Simple web interface
- Comprehensive logging

## Prerequisites

- Python 3.8+
- 2Captcha API key
- Modern web browser (Chrome/Chromium recommended)

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
python main.py --job-url "https://jobs.workable.com/..." --metadata-path "data/user_metadata.json"
```

### Web Interface

```bash
python -m ui.app
```

Then open your browser to `http://localhost:5000`

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
