# Claude Memory for Ebay Project

## Common Commands

### Testing Scripts
```bash
# Test eBay API client
python cc-python.py
```

### Development Commands

## Project Structure
- `cc-python.py` - Main script for eBay API client credentials and token management

## Coding Standards

### Error Handling
- **Avoid error hiding** - Don't silently return None or use default values for critical errors
- **Throw exceptions for unexpected conditions** - Use ValueError, RuntimeError, etc. for conditions that shouldn't happen
- **Validate inputs early** - Check for missing/invalid values as early as possible
