# Claude Memory for Ebay Project

## Common Commands

### Testing Scripts
```bash
# Test eBay API client
python proto.py
```

### Development Commands

## Project Structure
- `proto.py` - eBay API client

## Coding Standards

### Error Handling
- **Avoid error hiding** - Don't silently return None or use default values for critical errors
- **Throw exceptions for unexpected conditions** - Use ValueError, RuntimeError, etc. for conditions that shouldn't happen
- **Validate inputs early** - Check for missing/invalid values as early as possible
