# 🚀 Quick Start: Get Hydra-Logger Running in 5 Minutes

**Purpose:** Get Hydra-Logger working immediately with console and file output.

**Time:** 2-3 minutes  
**Difficulty:** Beginner

## 🎯 What You'll Learn

- Basic Hydra-Logger setup
- Console and file logging
- Different log levels
- Colored output in console

## 🏃‍♂️ Quick Start

```bash
# Run the example
python main.py

# Check the generated logs
ls logs/
cat logs/app.log
```

## 📊 What You'll See

### Console Output (Colored)
```
2024-01-15 10:30:15 - APP - INFO - main.py:25 - Application started
2024-01-15 10:30:15 - APP - DEBUG - main.py:26 - Debug information
2024-01-15 10:30:15 - APP - WARNING - main.py:27 - Warning message
2024-01-15 10:30:15 - APP - ERROR - main.py:28 - Error occurred
```

### File Output (logs/app.log)
```
2024-01-15 10:30:15 - APP - INFO - main.py:25 - Application started
2024-01-15 10:30:15 - APP - DEBUG - main.py:26 - Debug information
2024-01-15 10:30:15 - APP - WARNING - main.py:27 - Warning message
2024-01-15 10:30:15 - APP - ERROR - main.py:28 - Error occurred
```

## 🔑 Key Concepts

- **Console logging** - See colored output immediately
- **File logging** - Persistent logs for later review
- **Log levels** - DEBUG, INFO, WARNING, ERROR
- **Simple setup** - Just a few lines of code

## ➡️ Next Steps

Ready for more? Try **[02_console_logging](../02_console_logging/)** to learn about console-only logging with custom colors and formats. 