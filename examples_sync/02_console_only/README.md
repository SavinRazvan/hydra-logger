# 02 - Console Only Logging

## 🎯 Overview

This example demonstrates **console-only logging** with Hydra-Logger. Perfect for development environments, CLI applications, and when you need immediate feedback without file I/O.

## 📚 Learning Path

### 🚀 **Step 1: Basic Console Logging** (5 minutes)
- **[01_basic_console.py](modules/01_basic_console.py)** - Simple console-only setup

### 📚 **Step 2: Console Configuration** (10 minutes)
- **[02_console_config.py](modules/02_console_config.py)** - Configure console output options
- **[03_console_levels.py](modules/03_console_levels.py)** - Different log levels for console

### ⚡ **Step 3: Advanced Console Features** (15 minutes)
- **[04_console_colors.py](modules/04_console_colors.py)** - Custom colors and formatting
- **[05_console_formats.py](modules/05_console_formats.py)** - Different output formats (text, JSON)

### 💼 **Step 4: Real Applications**
- **[cli_app.py](examples/cli_app.py)** - Interactive CLI application with console logging

## 🚀 Getting Started

### **Step 1: Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Or install Hydra-Logger directly
pip install hydra-logger
```

### **Step 2: Start Learning**
```bash
# Begin with basic console logging
python modules/01_basic_console.py

# Progress through modules
python modules/02_console_config.py
python modules/03_console_levels.py
python modules/04_console_colors.py
python modules/05_console_formats.py

# Try real application
python examples/cli_app.py
```

### **Step 3: Run Complete Tutorial**
```bash
# Run the guided tutorial
python main.py
```

## 📊 What You'll Learn

### **Core Concepts**
1. **Console-Only Setup** - Configure logging for terminal output only
2. **Console Configuration** - Customize console output options
3. **Log Levels** - Different levels for different console scenarios
4. **Color Customization** - Make console output visually appealing
5. **Format Options** - Text and JSON formats for console
6. **Real Applications** - CLI tools and interactive applications

### **Use Cases**
- **Development Environment** - Quick debugging and immediate feedback
- **CLI Applications** - Command-line tools and scripts
- **Testing** - Unit test output and debug information
- **Docker Containers** - Container logs and process output
- **Interactive Apps** - User-facing applications with real-time feedback

## 🎯 Module Structure

### **modules/** - Progressive Learning
Each module builds on previous knowledge:

- **01_basic_console.py** - Simple console-only setup
- **02_console_config.py** - Console configuration options
- **03_console_levels.py** - Log level management for console
- **04_console_colors.py** - Color customization and visual appeal
- **05_console_formats.py** - Different output formats for console

### **examples/** - Real Applications
Working applications that demonstrate practical usage:

- **cli_app.py** - Interactive CLI application with comprehensive console logging

### **Expected Console Output**
```
🚀 Console-Only Logging Demo
========================================
2025-01-27 10:30:15 DEBUG [CONSOLE] Debug message - only visible in debug mode
2025-01-27 10:30:15 INFO [CONSOLE] Info message - general information
2025-01-27 10:30:15 WARNING [CONSOLE] Warning message - something to watch out for
2025-01-27 10:30:15 ERROR [CONSOLE] Error message - something went wrong
2025-01-27 10:30:15 CRITICAL [CONSOLE] Critical message - system failure

✅ Console-only logging demo completed!
📝 All messages were logged to console only (no files created)
```

## 🔑 Key Features Demonstrated

### **Console-Only Benefits**
- **No File I/O**: Faster execution, no disk writes
- **Immediate Feedback**: See logs instantly in terminal
- **Development Friendly**: Perfect for debugging and development
- **No File Clutter**: No log files to manage
- **Portable**: Works anywhere with a terminal

### **Visual Appeal**
- **Colored Output**: Different log levels have different colors
- **Custom Colors**: Configure colors for your preferences
- **Format Options**: Text and JSON formats for different use cases
- **Professional Appearance**: Clean, readable console output

### **Configuration Options**
- **Log Levels**: Control what appears in console
- **Format Customization**: Text, JSON, and custom formats
- **Color Management**: Customize colors for different levels
- **Layer Support**: Organize console output by layers

## 📋 Prerequisites

### **Required**
- Python 3.7 or higher
- Hydra-Logger installed
- Terminal with color support (optional but recommended)

### **Installation**
```bash
# Install Hydra-Logger
pip install hydra-logger

# Or install in development mode
pip install -e .

# Install optional dependencies for enhanced examples
pip install -r requirements.txt
```

## 🎯 Expected Learning Outcomes

After completing this tutorial, you'll be able to:

### **Basic Console Setup**
- ✅ Configure console-only logging
- ✅ Understand console configuration options
- ✅ Use different log levels effectively
- ✅ Customize console appearance

### **Advanced Console Features**
- ✅ Customize colors for different log levels
- ✅ Use different output formats (text, JSON)
- ✅ Configure console for different environments
- ✅ Integrate console logging into applications

### **Real-World Applications**
- ✅ Build CLI applications with proper logging
- ✅ Create interactive tools with console feedback
- ✅ Implement development-friendly logging
- ✅ Follow console logging best practices

## 🧪 Testing Your Knowledge

### **Progressive Testing**
Each module includes:
- ✅ Clear examples with explanations
- ✅ Expected console outputs
- ✅ Next steps guidance
- ✅ Key takeaways summary

### **Real Application Testing**
```bash
# Run the CLI application
python examples/cli_app.py

# Try different commands:
# - Type anything to process it
# - Type 'error' to simulate an error
# - Type 'slow' to simulate slow processing
# - Type 'quit' to exit
```

## 🎨 Color Output

The console output includes professional colors:
- **DEBUG**: Cyan
- **INFO**: Green
- **WARNING**: Yellow
- **ERROR**: Red
- **CRITICAL**: Bright Red
- **Layer Names**: Magenta

## 📚 Use Cases

### **Development Environment**
- Quick debugging
- Immediate feedback
- No file clutter

### **CLI Applications**
- Command-line tools
- Scripts and utilities
- Interactive applications

### **Testing**
- Unit test output
- Integration test logs
- Debug information

### **Docker Containers**
- Container logs
- Process output
- Health check logs

## 📚 Next Steps

After completing this tutorial:

1. **Explore Other Examples**: Check out the other examples in this directory
2. **Try File Logging**: Explore `03_file_only` for file-based logging
3. **Learn Multi-Layer**: Try `05_multiple_layers` for complex logging
4. **Read Documentation**: Visit the main documentation for advanced features

## 🤝 Need Help?

- **Documentation**: Check the main README for comprehensive guides
- **Issues**: Report bugs or request features on GitHub
- **Discussions**: Join the community discussions for help and ideas

---

**Happy Console Logging! 🐉** 